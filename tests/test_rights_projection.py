"""Rights projection fails closed; synthetic data only."""
import unittest
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts import rights_projection as module
from scripts.rights_projection import RightsError, projection_plan, scan_text_surfaces

BASE = {
    'contract_version': '1.0.0', 'purpose': 'deposit-public',
    'metadata': {
        'resources': [
            {'id': 'figure-1', 'kind': 'image', 'path': 'assets/synthetic-figure.svg'},
            {'id': 'paper-1', 'kind': 'document', 'path': 'resources/fictional-paper.pdf'},
        ],
        'rights': [
            {'resource_id': 'figure-1', 'status': 'owned'},
            {'resource_id': 'paper-1', 'status': 'excluded'},
        ],
        'publications': [{'id':'pub1', 'resource_ids':['paper-1']}],
    }
}

class ProjectionTests(unittest.TestCase):
    def test_owned_and_excluded_make_plan_not_release_authority(self):
        result = projection_plan(BASE, 'public')
        self.assertEqual(result['include_candidate_ids'], ['figure-1'])
        self.assertEqual(result['excluded_ids'], ['paper-1'])
        self.assertEqual(result['status'], 'plan-only')
        self.assertFalse(result['release_authorized'])
        self.assertTrue(result['requires_output_scan'])

    def test_unknown_and_missing_rights_are_blocking(self):
        for metadata in (
            {**BASE['metadata'], 'rights': BASE['metadata']['rights'][:1]},
            {**BASE['metadata'], 'rights': BASE['metadata']['rights'] + [{'resource_id':'unknown', 'status':'owned'}]},
        ):
            with self.subTest(metadata=metadata), self.assertRaises(RightsError):
                projection_plan({**BASE, 'metadata': metadata}, 'public')

    def test_permission_reference_is_not_approval(self):
        rights = [BASE['metadata']['rights'][0], {'resource_id':'paper-1', 'status':'licensed', 'permission_ref':'opaque-approval'}]
        result = projection_plan({**BASE, 'metadata':{**BASE['metadata'], 'rights':rights}}, 'public')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['holds'][0]['resource_id'], 'paper-1')
        self.assertFalse(result['release_authorized'])

    def test_duplicate_resource_or_rights_entry_is_invalid(self):
        for field in ('resources','rights'):
            items=BASE['metadata'][field]
            cfg={**BASE,'metadata':{**BASE['metadata'], field:items+[items[0]]}}
            with self.subTest(field=field), self.assertRaises(RightsError):
                projection_plan(cfg,'public')

    def test_referenced_resource_must_exist(self):
        pubs = [{'id':'pub1', 'resource_ids':['nonexistent']}]
        cfg={**BASE,'metadata':{**BASE['metadata'],'publications':pubs}}
        with self.assertRaisesRegex(RightsError, 'unknown'):
            projection_plan(cfg,'public')

    def test_unsafe_or_ambiguous_path_rejected(self):
        for path in ('../private', '/etc/passwd', 'figures/../../secret', 'figures//a', 'a\\b'):
            resources=[{**BASE['metadata']['resources'][0], 'path':path}, BASE['metadata']['resources'][1]]
            cfg={**BASE,'metadata':{**BASE['metadata'],'resources':resources}}
            with self.subTest(path=path), self.assertRaises(RightsError):
                projection_plan(cfg,'public')

    def test_public_projection_requires_public_deposit_purpose(self):
        with self.assertRaises(RightsError):
            projection_plan({**BASE,'purpose':'examination'},'public')

    def test_unknown_status_does_not_become_publicly_licensed(self):
        rights=[BASE['metadata']['rights'][0], {'resource_id':'paper-1','status':'permitted'}]
        with self.assertRaises(RightsError):
            projection_plan({**BASE,'metadata':{**BASE['metadata'],'rights':rights}},'public')

class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.surfaces={'pdf_text':'Synthetic public document', 'pdf_metadata':'Title: Public', 'bookmarks':'Chapter 1', 'attachments':''}

    def test_complete_synthetic_text_surfaces_pass_as_partial_scan_only(self):
        result=scan_text_surfaces(self.surfaces,['RESTRICTED-SYNTHETIC-SENTINEL'])
        self.assertEqual(result['status'],'text-surfaces-cleared')
        self.assertFalse(result['release_authorized'])

    def test_missing_surface_or_blank_main_text_blocks(self):
        for surfaces in ({'pdf_text':'x'}, {**self.surfaces, 'pdf_text':''}):
            with self.assertRaises(RightsError):
                scan_text_surfaces(surfaces,['RESTRICTED-SYNTHETIC-SENTINEL'])

    def test_sentinel_leaks_detected_in_all_surfaces(self):
        for field in self.surfaces:
            with self.subTest(field=field), self.assertRaisesRegex(RightsError, 'sentinel'):
                scan_text_surfaces({**self.surfaces,field:'Restricted-Synthetic-Sentinel'},['RESTRICTED-SYNTHETIC-SENTINEL'])

    def test_missing_or_empty_sentinel_invalid(self):
        for sentinels in ([],[''], ['same','same']):
            with self.assertRaises(RightsError):
                scan_text_surfaces(self.surfaces,sentinels)

class ExecutableBoundaryTests(unittest.TestCase):
    def test_cli_returns_plan_without_claiming_authority(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'data.json'
            source.write_text(json.dumps(BASE))
            output=io.StringIO()
            with patch('sys.stdout', output):
                self.assertEqual(module.main([str(source)]),0)
            report=json.loads(output.getvalue())
            self.assertEqual(report['status'], 'plan-only')
            self.assertFalse(report['release_authorized'])

    def test_cli_rejects_duplicate_keys_nonfinite_and_oversized_inputs(self):
        for value in ('{"contract_version":"1.0.0","contract_version":"1.0.0"}',
                      '{"contract_version":"1.0.0","x":NaN}',
                      ' ' * (1024*1024+10)):
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'data.json'
                path.write_text(value)
                with patch('sys.stderr', new_callable=io.StringIO):
                    self.assertEqual(module.main([str(path)]),1)

    def test_cli_missing_file_and_symlink_fail(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'missing.json'
            with patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(module.main([str(path)]),1)
            actual=Path(td)/'source.json'; actual.write_text(json.dumps(BASE))
            path.symlink_to(actual)
            with patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(module.main([str(path)]),1)

    def test_full_projection_is_still_not_release_authorisation(self):
        plan=projection_plan({**BASE,'purpose':'deposit-full'},'full')
        self.assertEqual(plan['audience'],'full')
        self.assertFalse(plan['release_authorized'])
        with self.assertRaises(RightsError):
            projection_plan(BASE,'full')

    def test_unknown_resource_fields_and_nonlist_references_fail(self):
        cfg={**BASE,'metadata':{**BASE['metadata'], 'resources':[
            {**BASE['metadata']['resources'][0],'unrecognized':True},
            BASE['metadata']['resources'][1]]}}
        with self.assertRaises(RightsError): projection_plan(cfg,'public')
        cfg={**BASE,'metadata':{**BASE['metadata'], 'publications':[{'id':'a','resource_ids':'paper-1'}]}}
        with self.assertRaises(RightsError): projection_plan(cfg,'public')

    def test_duplicate_resource_paths_and_invalid_permission_refs_fail(self):
        r0, r1=BASE['metadata']['resources']
        cfg={**BASE,'metadata':{**BASE['metadata'], 'resources':[r0,{**r1,'path':r0['path']}]}}
        with self.assertRaises(RightsError): projection_plan(cfg,'public')
        status=[BASE['metadata']['rights'][0], {'resource_id':'paper-1', 'status':'licensed', 'permission_ref':'bad ref'}]
        cfg={**BASE,'metadata':{**BASE['metadata'],'rights':status}}
        with self.assertRaises(RightsError): projection_plan(cfg,'public')

    def test_empty_metadata_and_unknown_version_and_audience_fail(self):
        for config, audience in (({'contract_version':'other'},'public'),
                                 ({'contract_version':'1.0.0','purpose':'deposit-public'},'public'),
                                 (BASE,'unknown')):
            with self.assertRaises(RightsError): projection_plan(config,audience)

if __name__=='__main__':
    unittest.main()
