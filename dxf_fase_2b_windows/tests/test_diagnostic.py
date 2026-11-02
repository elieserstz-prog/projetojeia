"""Regression tests require only the standard library; no Windows approval implied."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diagnostic import bootstrap, core, driver

ORACLES = core.read_json(ROOT / 'expected.json')['cases']


def packet(case=0):
    geometries, evidence, midpoints = [], [], {}
    for i, oracle in enumerate(ORACLES[case]['geometries']):
        payload = copy.deepcopy(oracle)
        payload.pop('id')
        edge = {'index': 1, 'geometryId': str(i), 'lengthMm': oracle.get('lengthMm', 1),
                'closed': oracle['type'] in ('CIRCLE', 'ELLIPSE')}
        if oracle['type'] == 'ARC':
            for key in ('start', 'end'):
                edge[key] = payload.pop(key)
            midpoints['Obj%d.Edge1' % i] = payload.pop('midpoint')
            payload.pop('lengthMm')
        if oracle['type'] == 'ELLIPSE':
            payload['majorAxis'] = [x*oracle['majorRadius'] for x in oracle['majorDirection']]
            payload['minorAxis'] = [x*oracle['minorRadius'] for x in oracle['minorDirection']]
            payload['sweepRad'] = 2*math.pi
        geometries.append({'id': str(i), 'payload': payload, 'validation': {'state': 'extracted'}})
        evidence.append({'value': {'objectName': 'Obj%d' % i, 'edges': [edge],
                                   'aggregateOnly': False, 'constructionReference': False}})
    return {'geometries': geometries, 'evidence': evidence}, midpoints


class GeometryTests(unittest.TestCase):
    def test_all_eight_basic_geometries(self):
        p, m = packet()
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'passed')
        self.assertEqual(len(p['geometries']), 8)

    def test_changed_radius_rejected(self):
        p, m = packet(); p['geometries'][2]['payload']['radius'] = 30
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'failed')

    def test_mirrored_bulge_rejected(self):
        p, m = packet(); m['Obj3.Edge1'][1] = 25
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'failed')

    def test_same_circle_wrong_arc_sweep_rejected(self):
        p, m = packet(); p['geometries'][1]['payload']['sweepRad'] = math.radians(340)
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'failed')

    def test_wrong_arc_endpoint_rejected(self):
        p, m = packet(); p['evidence'][1]['value']['edges'][0]['start'] = [0, 0, 0]
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'failed')

    def test_reverse_line_orientation_preserved(self):
        p, m = packet(); g = p['geometries'][0]['payload']; g['start'], g['end'] = g['end'], g['start']
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'passed')

    def test_extra_coincident_observation_is_not_silently_deduplicated(self):
        p, m = packet(); p['evidence'].append(copy.deepcopy(p['evidence'][2])); p['evidence'][-1]['value']['objectName'] = 'Copy'
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'failed')

    def test_parent_container_is_not_summed_with_children(self):
        p, m = packet(); obj = copy.deepcopy(p['evidence'][2]); obj['value']['aggregateOnly'] = True
        p['evidence'].append(obj)
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'passed')

    def test_datum_helpers_are_not_physical_geometry(self):
        p, m = packet(); obj = copy.deepcopy(p['evidence'][2]); obj['value']['constructionReference'] = True
        p['evidence'].append(obj)
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'passed')

    def test_conflicting_geometry_never_passes(self):
        p, m = packet(); p['geometries'][0]['validation']['state'] = 'conflicting'
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'failed')

    def test_missing_model_geometry_fails_despite_paper_pending(self):
        p, m = packet(1); p['geometries'][0]['payload']['start'] = [1000, 0, 0]
        self.assertEqual(core.compare(p, ORACLES[1], m)['status'], 'failed')

    def test_model_landmarks_do_not_approve_paper_semantics(self):
        p, m = packet(1)
        self.assertEqual(core.compare(p, ORACLES[1], m)['status'], 'pending')

    def test_inches_ocs_and_two_ellipses(self):
        p, m = packet(2)
        self.assertEqual(core.compare(p, ORACLES[2], m)['status'], 'pending')

    def test_wrong_unit_conversion_rejected(self):
        p, m = packet(2)
        for g in p['geometries']:
            g['payload']['center'] = [x/25.4 for x in g['payload']['center']]
        self.assertEqual(core.compare(p, ORACLES[2], m)['status'], 'failed')

    def test_double_unit_conversion_rejected(self):
        p, m = packet(2); p['geometries'][2]['payload']['radius'] *= 25.4
        self.assertEqual(core.compare(p, ORACLES[2], m)['status'], 'failed')

    def test_nonuniform_scaling_cannot_become_circle(self):
        p, m = packet(2); p['geometries'][0]['payload']['type'] = 'CIRCLE'
        self.assertEqual(core.compare(p, ORACLES[2], m)['status'], 'failed')

    def test_rotated_major_axis_rejected(self):
        p, m = packet(2); p['geometries'][0]['payload']['majorAxis'] = [50.8, 0, 0]
        self.assertEqual(core.compare(p, ORACLES[2], m)['status'], 'failed')

    def test_wrong_ocs_plane_rejected(self):
        p, m = packet(2); p['geometries'][2]['payload']['normal'] = [0, 0, 1]
        self.assertEqual(core.compare(p, ORACLES[2], m)['status'], 'failed')

    def test_small_normal_rotation_beyond_angular_tolerance_rejected(self):
        p, m = packet(); p['geometries'][2]['payload']['normal'] = [0, 1e-5, 1]
        self.assertEqual(core.compare(p, ORACLES[0], m)['status'], 'failed')

    def test_missing_array_occurrence_rejected(self):
        p, m = packet(2); p['evidence'].pop(1)
        self.assertEqual(core.compare(p, ORACLES[2], m)['status'], 'failed')

    def test_unitless_never_passes_physical_calibration(self):
        p = {'geometries': [{'id': 'a', 'payload': {'type': 'LINE'}}, {'id': 'b', 'payload': {'type': 'BSPLINE'}}],
             'evidence': [{'value': {'objectName': 'O', 'edges': [{'geometryId': 'a', 'index': 1}, {'geometryId': 'b', 'index': 2}]}}]}
        self.assertEqual(core.compare(p, ORACLES[3])['status'], 'pending')

    def test_no_geometry_cannot_be_success(self):
        self.assertEqual(core.compare({}, ORACLES[3])['status'], 'failed')

    def test_nan_and_infinite_are_not_equal(self):
        self.assertFalse(core.close(float('nan'), 0)); self.assertFalse(core.close(float('inf'), float('inf')))


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.request = dict(requestId='diag-id', generation=3, revision=1)
        self.p = dict(contract='JEIA_DXF_TECH', version='1.0', document={'sha256': 'abc'},
                      context=dict(requestId='diag-id', selectionGeneration=3, analysisRevision=1),
                      sources=[{'inputSha256': 'abc'}], validation={'cncReleased': False,
                      'eligibility': [{'consumer': c, 'status': 'blocked'} for c in ('material', 'process', 'cost')]})

    def test_matching_request_accepted(self):
        core.validate_identity(self.p, 'abc', self.request)

    def test_stale_request_rejected(self):
        self.p['context']['requestId'] = 'old'
        with self.assertRaises(ValueError): core.validate_identity(self.p, 'abc', self.request)

    def test_same_filename_changed_bytes_rejected(self):
        with self.assertRaises(ValueError): core.validate_identity(self.p, 'different-content', self.request)

    def test_selection_generation_rejected(self):
        self.p['context']['selectionGeneration'] = 2
        with self.assertRaises(ValueError): core.validate_identity(self.p, 'abc', self.request)

    def test_boolean_generation_rejected(self):
        self.p['context']['selectionGeneration'] = True; self.request['generation'] = 1
        with self.assertRaises(ValueError): core.validate_identity(self.p, 'abc', self.request)

    def test_analysis_revision_rejected(self):
        self.p['context']['analysisRevision'] = 2
        with self.assertRaises(ValueError): core.validate_identity(self.p, 'abc', self.request)

    def test_engine_source_hash_rejected(self):
        self.p['sources'][0]['inputSha256'] = 'other'
        with self.assertRaises(ValueError): core.validate_identity(self.p, 'abc', self.request)

    def test_cnc_release_rejected(self):
        self.p['validation']['cncReleased'] = True
        with self.assertRaises(ValueError): core.validate_identity(self.p, 'abc', self.request)

    def test_budget_unblock_rejected(self):
        self.p['validation']['eligibility'][2]['status'] = 'eligible'
        with self.assertRaises(ValueError): core.validate_identity(self.p, 'abc', self.request)


class IsolationAndTransportTests(unittest.TestCase):
    def test_profile_writes_only_new_session_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = os.environ.copy()
            flags, env = core.profile(Path(tmp) / 'p')
            self.assertEqual(before, os.environ)
            for key, value in env.items():
                if key != 'PYTHONDONTWRITEBYTECODE':
                    self.assertTrue(Path(value).is_dir()); Path(value).relative_to(tmp)
            self.assertIn('--user-cfg', flags); self.assertIn('--system-cfg', flags)

    def test_ignored_isolation_fails_closed(self):
        class App:
            @staticmethod
            def ConfigGet(key): return '/outside/profile'
        self.assertFalse(core.isolation(App, ROOT)['passed'])

    def test_verified_isolation_accepted(self):
        class App:
            @staticmethod
            def ConfigGet(key): return str(ROOT / 'session' / key)
        self.assertTrue(core.isolation(App, ROOT / 'session')['passed'])

    def test_new_output_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'x.json'; core.write_json(path, {'x': 1})
            with self.assertRaises(FileExistsError): core.write_json(path, {'x': 2})

    def test_process_logs_and_success(self):
        with tempfile.TemporaryDirectory(prefix='JEIA paths spaces ') as tmp:
            r = core.run_process([sys.executable, '-c', 'print("native log")'], os.environ.copy(), tmp, 5, Path(tmp) / 'worker')
            self.assertEqual(r['exitCode'], 0)
            self.assertIn('native log', (Path(tmp) / 'worker.stdout.txt').read_text())

    def test_native_crash_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = core.run_process([sys.executable, '-c', 'raise SystemExit(42)'], os.environ.copy(), tmp, 5, Path(tmp) / 'worker')
            self.assertEqual(r['exitCode'], 42)

    def test_timeout_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = core.run_process([sys.executable, '-c', 'import time; time.sleep(10)'], os.environ.copy(), tmp, .05, Path(tmp) / 'worker')
            self.assertTrue(r['timedOut']); self.assertNotEqual(r['exitCode'], 0)

    def test_missing_executable_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = core.run_process([str(Path(tmp) / 'nonexistent')], os.environ.copy(), tmp, 1, Path(tmp) / 'worker')
            self.assertIsNone(r['exitCode']); self.assertIn('error', r)

    def test_all_approved_assets_byte_identical(self):
        manifest = core.read_json(ROOT / 'APPROVED_FILES.json')
        self.assertEqual(len(list((ROOT / 'examples').glob('*.dxf'))), 4)
        for name, expected in manifest['files'].items():
            self.assertEqual(core.sha256(ROOT / name), expected, name)

    def test_failed_driver_exports_json_and_all_four_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Deterministic missing-module failure before any native import.
            with patch.dict(sys.modules, {'FreeCAD': None}):
                result = driver.run({'session': tmp, 'freecadCmd': 'not-used'})
            self.assertEqual(len(result['cases']), 4)
            self.assertTrue(all(c['status'] == 'not_run' for c in result['cases']))
            self.assertFalse(result['windowsValidationApproved']); self.assertFalse(result['integrationApproved'])
            self.assertTrue((Path(tmp) / 'relatorio.json').exists()); self.assertTrue((Path(tmp) / 'RESUMO.txt').exists())

    def test_launcher_has_no_policy_or_install_commands(self):
        # Text audit only: explicitly NOT a PowerShell syntax/runtime test.
        script = (ROOT / 'Diagnostico_FreeCAD.ps1').read_text().lower()
        cmd = (ROOT / 'INICIAR_DIAGNOSTICO.cmd').read_text().lower()
        for forbidden in ('set-executionpolicy', 'executionpolicy bypass', 'invoke-webrequest',
                          'invoke-expression', 'start-bitstransfer', 'pip install', 'winget install', 'runas'):
            self.assertNotIn(forbidden, script + cmd)
        self.assertIn('--user-cfg', script); self.assertIn('--system-cfg', script)

    def test_cmd_entry_points_execute_macros_instead_of_import_only_python(self):
        script = (ROOT / 'Diagnostico_FreeCAD.ps1').read_text()
        self.assertIn('run_driver.FCMacro', script)
        self.assertIn('run_driver.FCMacro', (ROOT / 'diagnostic/bootstrap.py').read_text())
        self.assertIn('run_worker.FCMacro', (ROOT / 'diagnostic/driver.py').read_text())
        self.assertNotIn("if __name__", (ROOT / 'diagnostic/run_driver.FCMacro').read_text())
        self.assertNotIn("if __name__", (ROOT / 'diagnostic/run_worker.FCMacro').read_text())


class BootstrapTests(unittest.TestCase):
    def test_non_windows_does_not_start_native_process(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap.platform, 'system', return_value='Linux'), \
                patch.object(bootstrap, 'run_process') as process:
            session = bootstrap.main(output_root=tmp)
            process.assert_not_called()
            report = core.read_json(session / 'relatorio.json')
            self.assertEqual(len(report['cases']), 4)
            self.assertTrue(all(c['status'] == 'not_run' for c in report['cases']))

    def test_missing_installation_never_installs(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap.platform, 'system', return_value='Windows'), \
                patch.object(bootstrap, 'find_candidates', return_value=[]), patch.object(bootstrap, 'run_process') as process:
            session = bootstrap.main(output_root=tmp)
            process.assert_not_called()
            self.assertEqual(core.read_json(session / 'bootstrap.json')['candidates'], [])

    def test_multiple_installations_require_explicit_selection(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap.platform, 'system', return_value='Windows'), \
                patch.object(bootstrap, 'find_candidates', return_value=['one', 'two']), patch.object(bootstrap, 'run_process') as process:
            session = bootstrap.main(output_root=tmp)
            process.assert_not_called()
            self.assertEqual(len(core.read_json(session / 'bootstrap.json')['candidates']), 2)

    def test_failed_version_probe_marks_all_dxf_not_run(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap.platform, 'system', return_value='Windows'):
            exe = Path(tmp) / 'FreeCADCmd.exe'; exe.write_bytes(b'fake executable: not run')
            with patch.object(bootstrap, 'run_process', return_value={'exitCode': 1, 'timedOut': False}) as process:
                session = bootstrap.main(str(exe), tmp)
            self.assertEqual(process.call_count, 1)
            self.assertTrue(all(c['status'] == 'not_run' for c in core.read_json(session / 'relatorio.json')['cases']))

    def test_successful_startup_without_report_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap.platform, 'system', return_value='Windows'):
            exe = Path(tmp) / 'FreeCADCmd.exe'; exe.write_bytes(b'fake executable: not run')
            with patch.object(bootstrap, 'run_process', return_value={'exitCode': 0, 'timedOut': False}):
                session = bootstrap.main(str(exe), tmp)
            self.assertEqual(core.read_json(session / 'relatorio.json')['technicalOutcome'], 'failed')

    def test_driver_timeout_is_failure(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bootstrap.platform, 'system', return_value='Windows'):
            exe = Path(tmp) / 'FreeCADCmd.exe'; exe.write_bytes(b'fake executable: not run')
            with patch.object(bootstrap, 'run_process', side_effect=[{'exitCode': 0, 'timedOut': False},
                                                                   {'exitCode': -1, 'timedOut': True}]):
                session = bootstrap.main(str(exe), tmp)
            self.assertFalse(core.read_json(session / 'bootstrap.json')['integrationApproved'])
            self.assertEqual(core.read_json(session / 'bootstrap.json')['status'], 'failed')

    def test_partial_worker_geometry_never_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = dict(mode='dxf')
            with patch.object(driver, 'run_process', return_value={'exitCode': 0, 'timedOut': False}), \
                    patch.object(driver, 'read_json', return_value={'workerError': 'missing PySide'}):
                with self.assertRaisesRegex(RuntimeError, 'missing PySide'):
                    driver.execute('not-run', tmp, Path(tmp) / 'case', request)
            self.assertTrue((Path(tmp) / 'case' / 'process.json').exists())

    def test_isolation_failure_prevents_worker_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(driver, 'run_process', return_value={'exitCode': 0, 'timedOut': False}), \
                    patch.object(driver, 'read_json', return_value={'isolation': {'passed': False}}):
                with self.assertRaisesRegex(RuntimeError, 'isolation'):
                    driver.execute('not-run', tmp, Path(tmp) / 'case', {})


if __name__ == '__main__':
    unittest.main()
