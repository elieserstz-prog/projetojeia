"""Main script run by the installed FreeCADCmd, never by an external Python."""
import os
from pathlib import Path
import platform
import sys
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from diagnostic.core import (isolation, profile, read_json, run_process, sha256,
                             summarize, validate_identity, write_json)
from diagnostic.assessment import assess_geometry


def execute(exe, session, folder, request):
    folder.mkdir()
    flags, updates = profile(folder / 'profile')
    write_json(folder / 'request.json', request)
    env = os.environ.copy()
    env.update(updates)
    env.update(JEIA_DIAG_REQUEST=str(folder / 'request.json'), JEIA_DIAG_RESPONSE=str(folder / 'response.json'))
    process = run_process([exe, *flags, str(ROOT / 'diagnostic' / 'run_worker.FCMacro')], env, folder,
                          30 if request.get('mode') == 'kernel_control' else 90, folder / 'worker')
    write_json(folder / 'process.json', process)
    if process['timedOut'] or process['exitCode'] != 0:
        raise RuntimeError('FreeCADCmd failed or timed out: ' + str(process))
    result = read_json(folder / 'response.json')
    if 'workerError' in result:
        raise RuntimeError(result['workerError'])
    if not result.get('isolation', {}).get('passed'):
        raise RuntimeError('Worker isolation not confirmed')
    result['process'] = process
    return result


def export_brep(result, folder):
    records = []
    destination = folder / 'brep'
    destination.mkdir()
    for index, evidence in enumerate(result['packet']['evidence']):
        obj = evidence['value']
        for kind in ('rawObjectBrep', 'globalBrep', 'localBrep'):
            text = obj.get(kind)
            if text:
                # Numeric file names: no DXF name/handle is used as a path.
                path = destination / ('object_%04d_%s.brep' % (index, kind))
                path.write_text(text, encoding='utf-8')
                records.append({'object': obj.get('objectName'), 'kind': kind,
                                'path': str(path.relative_to(folder)), 'sha256': sha256(path)})
    return records


def run(config):
    session = Path(config['session']).resolve()
    report = {'format': 'JEIA_DXF_WINDOWS_DIAGNOSTIC', 'version': '1.0', 'platform': platform.platform(),
              'experimental': True, 'windowsValidationApproved': False, 'integrationApproved': False,
              'schemaValidation': 'not_run_no_jsonschema_dependency',
              'freecadCmd': config['freecadCmd'], 'cases': [], 'technicalOutcome': 'failed',
              'note': 'Geometric diagnostic only. Pending operator review; no JEIA, STEP or manufacturing use.'}
    oracle = read_json(ROOT / 'expected.json')
    try:
        import FreeCAD as app
        report['freecadVersion'] = list(app.Version())
        report['pythonVersion'] = sys.version
        report['isolation'] = isolation(app, session)
        if not report['isolation']['passed']:
            raise RuntimeError('Driver configuration isolation not confirmed; DXF import cancelled')
        manifest = read_json(ROOT / 'APPROVED_FILES.json')
        mismatches = [f for f, expected in manifest['files'].items() if sha256(ROOT / f) != expected]
        report['approvedAssetsIntegrity'] = {'passed': not mismatches, 'mismatches': mismatches}
        if mismatches:
            raise RuntimeError('Approved adapter/example integrity failed')
        request = {'session': str(session), 'mode': 'kernel_control', 'requestId': 'control-' + uuid.uuid4().hex,
                   'generation': 0, 'revision': 1}
        try:
            control = execute(config['freecadCmd'], session, session / 'kernel_control', request)
            report['kernelControl'] = {'passed': control['kernelControlPassed'],
                                       'brepChecks': control['brepChecks'], 'process': control['process']}
        except Exception as exc:
            report['kernelControl'] = {'passed': False, 'error': str(exc)}
        # Try all four independently even if the synthetic control fails.
        for index, case in enumerate(oracle['cases'], 1):
            path = ROOT / 'examples' / case['file']
            folder = session / ('case_%02d' % index)
            entry = {'file': case['file'], 'status': 'failed', 'folder': folder.name,
                     'expected': case, 'reason': ''}
            report['cases'].append(entry)
            try:
                original_hash = sha256(path)
                request = {'session': str(session), 'input': str(path), 'inputSha256': original_hash,
                           'requestId': 'diag-' + uuid.uuid4().hex, 'generation': index, 'revision': 1}
                result = execute(config['freecadCmd'], session, folder, request)
                validate_identity(result['packet'], original_hash, request)
                if sha256(path) != original_hash:
                    raise ValueError('Example bytes changed')
                entry['comparison'] = assess_geometry(result['packet'], case, result['edgeMidpoints'], result['objectInventory'])
                entry['brepChecks'] = result['brepChecks']
                entry['brepFiles'] = export_brep(result, folder)
                entry['objectInventory'] = result['objectInventory']
                entry['diagnostics'] = result['packet']['diagnostics']
                entry['process'] = result['process']
                entry['status'] = entry['comparison']['status']
                if not entry['brepChecks'] or any(c['status'] != 'passed' for c in entry['brepChecks']):
                    entry['status'] = 'failed'
                    entry['reason'] = 'BREP absent, invalid, or changed during round-trip'
                if any(d['code'] in ('NATIVE_GEOMETRY_CONFLICT', 'TOPOLOGY_RESOURCE_LIMIT', 'BREP_RESOURCE_LIMIT',
                                     'BREP_EXPORT_FAILED', 'FACE_METADATA_UNAVAILABLE')
                       for d in entry['diagnostics']):
                    entry['status'] = 'failed'
                    entry['reason'] = 'Native conflict, resource limit or incomplete geometry; inspect diagnostics'
            except Exception as exc:
                entry['reason'] = type(exc).__name__ + ': ' + str(exc)
        # Extra investigation is observational; it never patches the input or
        # changes acceptance of the original four cases.
        try:
            probe_folder = session / 'polyline_probe'
            request = {'session': str(session), 'mode': 'polyline_probe',
                       'input': str(ROOT / 'examples' / oracle['cases'][0]['file']),
                       'probeOutput': str(probe_folder / 'trials')}
            probe = execute(config['freecadCmd'], session, probe_folder, request)
            report['polylineInvestigation'] = {'status': 'completed', 'folder': probe_folder.name,
                                                'trials': len(probe['trials']),
                                                'sourceUnchanged': probe['sourceUnchanged'],
                                                'changesOriginalCaseResults': False}
        except Exception as exc:
            report['polylineInvestigation'] = {'status': 'failed', 'error': str(exc),
                                                'changesOriginalCaseResults': False}
        statuses = [c['status'] for c in report['cases']]
        if not report['kernelControl']['passed'] or 'failed' in statuses:
            report['technicalOutcome'] = 'failed'
        else:
            report['technicalOutcome'] = 'pending' if 'pending' in statuses else 'passed'
        if platform.system() != 'Windows':
            report['hostLimitation'] = 'Non-Windows run cannot validate Windows FreeCADCmd'
    except Exception as exc:
        report['driverError'] = str(exc)
        report['driverTrace'] = traceback.format_exc()
        done = {c['file'] for c in report['cases']}
        for case in oracle['cases']:
            if case['file'] not in done:
                report['cases'].append({'file': case['file'], 'status': 'not_run', 'reason': str(exc)})
    write_json(session / 'relatorio.json', report)
    (session / 'RESUMO.txt').write_text(summarize(report), encoding='utf-8')
    return report


if __name__ == '__main__':
    run(read_json(os.environ['JEIA_DIAG_SESSION']))
