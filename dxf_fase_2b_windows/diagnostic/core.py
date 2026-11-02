"""Standard-library controller and independent geometric comparisons."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def profile(root):
    root = Path(root).resolve()
    dirs = {key: root / name for key, name in {
        'FREECAD_USER_HOME': 'home', 'FREECAD_USER_DATA': 'data',
        'FREECAD_USER_TEMP': 'temp', 'APPDATA': 'roaming', 'LOCALAPPDATA': 'local',
        'TEMP': 'temp', 'TMP': 'temp', 'XDG_CONFIG_HOME': 'config',
        'XDG_DATA_HOME': 'data', 'XDG_CACHE_HOME': 'cache'}.items()}
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    env = {key: str(value) for key, value in dirs.items()}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    flags = ['--user-cfg', str(root / 'user.cfg'), '--system-cfg', str(root / 'system.cfg'),
             '--log-file', str(root / 'FreeCAD.log')]
    return flags, env


def isolation(app, root):
    root = Path(root).resolve()
    facts = {key: app.ConfigGet(key) for key in
             ('UserParameter', 'SystemParameter', 'UserAppData', 'UserHomePath')}
    def inside(value):
        try:
            Path(value).resolve().relative_to(root)
            return bool(value)
        except (ValueError, OSError):
            return False
    # Fail closed before importing a DXF if this FreeCAD ignores isolation.
    return {'passed': all(inside(v) for v in facts.values()), 'effectivePaths': facts}


def run_process(command, env, cwd, timeout, log_prefix):
    """No shell. On timeout terminate only this diagnostic's own process tree."""
    start = time.monotonic()
    with Path(str(log_prefix) + '.stdout.txt').open('wb') as out, \
            Path(str(log_prefix) + '.stderr.txt').open('wb') as err:
        try:
            child = subprocess.Popen(command, cwd=str(cwd), env=env, stdout=out, stderr=err)
        except OSError as exc:
            return {'exitCode': None, 'timedOut': False, 'error': str(exc), 'seconds': 0}
        timed_out = False
        try:
            child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == 'nt':
                # Built-in Windows utility, addressed exclusively by our child PID.
                killer = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'taskkill.exe'
                try:
                    subprocess.run([str(killer), '/PID', str(child.pid), '/T', '/F'],
                                   stdout=err, stderr=err, timeout=10, check=False)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            if child.poll() is None:
                child.kill()
            child.wait(timeout=10)
    return {'exitCode': child.returncode, 'timedOut': timed_out,
            'seconds': round(time.monotonic() - start, 3),
            'stdout': Path(str(log_prefix) + '.stdout.txt').name,
            'stderr': Path(str(log_prefix) + '.stderr.txt').name}


def validate_identity(packet, expected_hash, request):
    if packet.get('contract') != 'JEIA_DXF_TECH' or packet.get('version') != '1.0':
        raise ValueError('Unexpected contract')
    if packet.get('document', {}).get('sha256') != expected_hash:
        raise ValueError('Input hash mismatch')
    ctx = packet.get('context', {})
    for key in ('requestId', 'selectionGeneration', 'analysisRevision'):
        request_key = {'selectionGeneration': 'generation', 'analysisRevision': 'revision'}.get(key, key)
        if ctx.get(key) != request[request_key] or type(ctx.get(key)) is not type(request[request_key]):
            raise ValueError('Identity mismatch: ' + key)
    sources = packet.get('sources', [])
    if not sources or any(s.get('inputSha256') != expected_hash for s in sources):
        raise ValueError('Source hash mismatch')
    validation = packet.get('validation', {})
    if validation.get('cncReleased') is not False:
        raise ValueError('Experimental packet must not release CNC')
    for consumer in ('material', 'process', 'cost'):
        if not any(e.get('consumer') == consumer and e.get('status') == 'blocked'
                   for e in validation.get('eligibility', [])):
            raise ValueError('Unblocked downstream consumer: ' + consumer)


def close(a, b, tol=1e-5):
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    try:
        return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError, OverflowError):
        return False


def norm(vector):
    return math.sqrt(sum(x*x for x in vector))


def parallel(a, b):
    if len(a) != 3 or len(b) != 3:
        return False
    n = norm(a) * norm(b)
    cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    return n > 0 and norm(cross)/n <= math.sin(1e-7)


def matches(expected, actual):
    if expected['type'] != actual.get('type'):
        return False
    typ = expected['type']
    if typ == 'LINE':
        return ((close(expected['start'], actual.get('start')) and close(expected['end'], actual.get('end')))
                or (close(expected['start'], actual.get('end')) and close(expected['end'], actual.get('start'))))
    if typ in ('CIRCLE', 'ARC'):
        if not (close(expected['center'], actual.get('center')) and close(expected['radius'], actual.get('radius'))):
            return False
        if not parallel(expected.get('normal', [0, 0, 1]), actual.get('normal', [0, 0, 0])):
            return False
        if typ == 'ARC':
            # Match the trimmed sweep and its midpoint, not only its support circle.
            # Midpoint distinguishes the upper/lower semicircle and arc complements.
            edge = actual.get('_edge', {})
            return (close(abs(expected['sweepRad']), abs(actual.get('sweepRad', -999)), 1e-7)
                    and close(expected['lengthMm'], edge.get('lengthMm'))
                    and close(expected['midpoint'], edge.get('midpoint'))
                    and ((close(expected['start'], edge.get('start')) and close(expected['end'], edge.get('end')))
                         or (close(expected['start'], edge.get('end')) and close(expected['end'], edge.get('start')))))
        return actual.get('_edge', {}).get('closed') is True
    if typ == 'ELLIPSE':
        return (close(expected['center'], actual.get('center'))
                and close(expected['majorRadius'], norm(actual.get('majorAxis', [])))
                and close(expected['minorRadius'], norm(actual.get('minorAxis', [])))
                and parallel(expected['majorDirection'], actual.get('majorAxis', []))
                and parallel(expected['minorDirection'], actual.get('minorAxis', []))
                and close(abs(actual.get('sweepRad', 0)), 2*math.pi, 1e-7)
                and actual.get('_edge', {}).get('closed') is True)
    return False


def observations(packet, midpoints=None):
    geometry = {g['id']: g for g in packet.get('geometries', [])}
    results, objects = [], []
    for evidence in packet.get('evidence', []):
        obj = evidence.get('value', {})
        if 'objectName' not in obj or 'edges' not in obj:
            continue
        objects.append(obj)
        if obj.get('aggregateOnly') or obj.get('constructionReference'):
            continue
        for edge in obj['edges']:
            g = geometry.get(edge.get('geometryId'), {})
            if g.get('validation', {}).get('state') in ('conflicting', 'unsupported'):
                continue
            value = dict(g.get('payload', {}))
            value['_edge'] = dict(edge)
            key = obj['objectName'] + '.Edge' + str(edge['index'])
            if midpoints and key in midpoints:
                value['_edge']['midpoint'] = midpoints[key]
            value['_key'] = key
            results.append(value)
    return results, objects


def compare(packet, oracle, midpoints=None):
    actual, objects = observations(packet, midpoints)
    used, checks = set(), []
    for expected in oracle.get('geometries', []):
        candidates = [i for i, g in enumerate(actual) if i not in used and matches(expected, g)]
        if candidates:
            chosen = candidates[0]
            used.add(chosen)
            checks.append({'id': expected['id'], 'status': 'passed', 'observation': actual[chosen]['_key'],
                           'candidateCount': len(candidates)})
        else:
            checks.append({'id': expected['id'], 'status': 'failed', 'reason': 'Expected analytic geometry not found',
                           'expected': expected})
    # Never silently merge coincident geometry. Exact-count fixtures flag extras.
    extras = [g['_key'] for i, g in enumerate(actual) if i not in used]
    if oracle.get('exactAnalyticCount'):
        checks.append({'id': 'analytic_multiplicity', 'status': 'passed' if not extras else 'failed',
                       'extraObservations': extras})
    for pending in oracle.get('pending', []):
        checks.append({'id': pending['id'], 'status': 'pending', 'reason': pending['reason']})
    if not oracle.get('geometries'):
        # Unitless data can be observed, never assumed to be calibrated millimetres.
        kinds = sorted({g.get('type', 'unknown') for g in actual})
        checks.append({'id': 'unitless_structural_curves', 'status': 'passed' if 'LINE' in kinds and 'BSPLINE' in kinds else 'failed',
                       'observedTypes': kinds})
    status = 'failed' if any(c['status'] == 'failed' for c in checks) else (
        'pending' if any(c['status'] == 'pending' for c in checks) else 'passed')
    return {'status': status, 'checks': checks, 'unmatchedObservations': extras,
            'nativeShapeObjects': len(objects), 'analyticObservations': len(actual),
            'meaning': 'Geometric oracle only; no classification, operation or integration approval'}


def summarize(report):
    lines = ['JEIA DXF Fase 2B - diagnostico experimental',
             'Integracao ao JEIA: NAO AUTORIZADA. Aguardar revisao do operador.',
             'Sistema: ' + report.get('platform', 'unknown'),
             'Resultado tecnico: ' + report.get('technicalOutcome', 'failed')]
    for case in report.get('cases', []):
        lines.append(case['file'] + ': ' + case['status'] + ' - ' + case.get('reason', ''))
    lines += ['JSON detalhado: relatorio.json',
              'Configuracoes e arquivos gerados pertencem somente a esta sessao.',
              'Nenhum resultado autoriza integracao ou uso para fabricacao.']
    return '\n'.join(lines) + '\n'
