"""Alternative launcher using only the Python already embedded in FreeCAD.

Invoked by the supplied FCMacro if Windows policy blocks the PowerShell launcher.
Does not import FreeCAD or access the GUI's documents/preferences.
"""
import os
from pathlib import Path
import platform
import shutil
import sys
import uuid

from .core import profile, read_json, run_process, sha256, summarize, write_json

ROOT = Path(__file__).resolve().parents[1]


def find_candidates():
    roots, candidates = [], []
    found = shutil.which('FreeCADCmd.exe')
    if found:
        candidates.append(Path(found))
    for base in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)'),
                 str(Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs')):
        if base and Path(base).is_dir():
            roots.extend(p for p in Path(base).glob('FreeCAD*') if p.is_dir())
    import winreg
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, r'Software\Microsoft\Windows\CurrentVersion\Uninstall',
                                    0, winreg.KEY_READ | view) as parent:
                    for i in range(winreg.QueryInfoKey(parent)[0]):
                        try:
                            with winreg.OpenKey(parent, winreg.EnumKey(parent, i)) as item:
                                name = winreg.QueryValueEx(item, 'DisplayName')[0]
                                if 'freecad' in str(name).lower():
                                    roots.append(Path(winreg.QueryValueEx(item, 'InstallLocation')[0]))
                        except OSError:
                            continue
            except OSError:
                continue
    for root in roots:
        for relative in ('bin/FreeCADCmd.exe', 'FreeCADCmd.exe'):
            path = root / relative
            if path.is_file():
                candidates.append(path)
    unique = {str(p.resolve()).casefold(): str(p.resolve()) for p in candidates}
    return sorted(unique.values())


def main(freecad_cmd=None, output_root=None):
    print('JEIA: somente FreeCADCmd existente, perfis isolados e quatro DXFs sinteticos.')
    print('Sem instalacoes, rede, alteracao de politica ou execucao do JEIA.')
    print('Timeout encerra somente os processos iniciados por este diagnostico.')
    output = Path(output_root) if output_root else ROOT / 'resultados'
    session = output.resolve() / ('sessao_macro_' + uuid.uuid4().hex[:12])
    session.mkdir(parents=True)
    bootstrap = {'format': 'JEIA_DXF_WINDOWS_BOOTSTRAP', 'version': '1.0', 'status': 'failed',
                 'launcher': 'FreeCAD macro / embedded Python', 'platform': platform.platform(),
                 'integrationApproved': False, 'windowsValidationApproved': False, 'session': str(session)}
    try:
        if platform.system() != 'Windows':
            raise RuntimeError('Windows required; no native process started')
        candidates = [str(Path(freecad_cmd).resolve())] if freecad_cmd else find_candidates()
        bootstrap['candidates'] = candidates
        if len(candidates) != 1:
            raise RuntimeError('Select one existing FreeCADCmd.exe explicitly; found %d (see candidates)' % len(candidates))
        exe = candidates[0]
        if Path(exe).name.lower() != 'freecadcmd.exe' or not Path(exe).is_file():
            raise ValueError('Existing FreeCADCmd.exe required')
        bootstrap.update(freecadCmd=exe, executableSha256=sha256(exe))
        flags, updates = profile(session / 'startup_profile')
        env = os.environ.copy(); env.update(updates)
        probe = run_process([exe, *flags, '--version'], env, session, 30, session / 'version')
        bootstrap['versionProbe'] = probe
        if probe['exitCode'] != 0 or probe['timedOut']:
            raise RuntimeError('FreeCADCmd --version failed or timed out; DXF tests not started')
        config = {'session': str(session), 'freecadCmd': exe}
        write_json(session / 'session.json', config)
        flags, updates = profile(session / 'driver_profile')
        env.update(updates); env['JEIA_DIAG_SESSION'] = str(session / 'session.json')
        process = run_process([exe, *flags, str(ROOT / 'diagnostic' / 'run_driver.FCMacro')],
                              env, session, 600, session / 'driver')
        bootstrap['driver'] = process
        if process['exitCode'] != 0 or process['timedOut']:
            raise RuntimeError('Diagnostic process failed or timed out; inspect driver logs')
        report = read_json(session / 'relatorio.json')
        bootstrap.update(status='completed', technicalOutcome=report['technicalOutcome'])
    except Exception as exc:
        bootstrap['error'] = type(exc).__name__ + ': ' + str(exc)
        if not (session / 'relatorio.json').exists():
            report = {'format': 'JEIA_DXF_WINDOWS_DIAGNOSTIC', 'version': '1.0', 'experimental': True,
                      'platform': platform.platform(), 'technicalOutcome': 'failed',
                      'windowsValidationApproved': False, 'integrationApproved': False,
                      'error': bootstrap['error'], 'cases': [
                          {'file': p.name, 'status': 'not_run', 'reason': bootstrap['error']}
                          for p in sorted((ROOT / 'examples').glob('*.dxf'))]}
            write_json(session / 'relatorio.json', report)
            (session / 'RESUMO.txt').write_text(summarize(report), encoding='utf-8')
    finally:
        write_json(session / 'bootstrap.json', bootstrap)
        print('Resultados: ' + str(session))
        print('Leia RESUMO.txt e relatorio.json. Integracao nao autorizada.')
    return session
