"""JEIA TECH Industrial — estabilizacao 03, UI Qt direta, recursos locais, leitura somente."""
import sys, os, json, shutil, hashlib, traceback, datetime, threading, subprocess, tempfile, urllib.request, ssl, http.server, base64, binascii
from pathlib import Path
from functools import partial
from engines.ezdxf_engine import scan as ez_scan

from PyQt6.QtCore import QObject, pyqtSlot, QUrl
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebChannel import QWebChannel

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
BASE = ROOT / 'JEIA_original_preservado.html'
APPDIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'JEIA_TECH_Industrial'
LOGFILE = APPDIR / 'diagnostico_inicializacao.txt'

def log(msg):
    APPDIR.mkdir(parents=True, exist_ok=True)
    with LOGFILE.open('a', encoding='utf-8') as fp:
        fp.write(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] {msg}\n")

def backup():
    if not BASE.is_file():
        raise RuntimeError('A base HTML do JEIA não foi encontrada')
    dest = APPDIR / 'backups'
    dest.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(BASE.read_bytes()).hexdigest()
    target = dest / ('JEIA_V20_6_8_3_' + sha[:16] + '.html')
    if not target.is_file():
        shutil.copy2(BASE, target)
    return {'arquivo': str(target), 'sha256': sha}

def freecadcmd():
    override=APPDIR/'freecad_path.txt'
    candidates=[]
    if override.is_file():
        try:candidates.append(Path(override.read_text(encoding='utf-8').strip().strip('"')))
        except Exception:pass
    for env in ('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA'):
        root=Path(os.environ.get(env,'C:/Program Files'))
        for pat in ('FreeCAD*/bin/FreeCADCmd.exe','FreeCAD*/bin/freecadcmd.exe',
                    'FreeCAD*/FreeCADCmd.exe','Programs/FreeCAD*/bin/FreeCADCmd.exe',
                    'Programs/FreeCAD*/FreeCADCmd.exe'):
            candidates.extend(root.glob(pat))
    for name in ('FreeCADCmd.exe','freecadcmd.exe'):
        found=shutil.which(name)
        if found:candidates.append(Path(found))
    return str(next((p for p in candidates if p.is_file()),''))

def freecad_analyze(mode,filepath):
    exe=freecadcmd()
    if not exe:return {'sucesso':False,'erro':'FreeCADCmd não encontrado. Instale o FreeCAD uma única vez ou configure seu caminho.'}
    with tempfile.TemporaryDirectory(prefix='jeia_cad_') as td:
        target=Path(td)/'resultado.json'
        cmd=[exe, str(ROOT/'engines/freecad_cad_engine.py'), mode, str(filepath), str(target)]
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
        try:
            run=subprocess.run(cmd,capture_output=True,text=True,timeout=120,creationflags=flags)
        except subprocess.TimeoutExpired:
            return {'sucesso':False,'erro':'FreeCAD excedeu 120 segundos. Nenhum resultado aprovado.'}
        if not target.is_file():
            return {'sucesso':False,'erro':'FreeCAD não retornou JSON. Código '+str(run.returncode),
                    'stderr':run.stderr[-1500:],'stdout':run.stdout[-1500:]}
        try:result=json.loads(target.read_text(encoding='utf-8'))
        except Exception as e:return {'sucesso':False,'erro':'JSON inválido do FreeCAD: '+str(e)}
        result['freecad_exec']=str(exe)
        return result

def run_probe(kind,filepath):
    path=Path(filepath)
    if not path.is_file():return {'erro':'Arquivo não encontrado'}
    if path.stat().st_size > 80*1024*1024:return {'erro':'Arquivo maior que 80 MB; teste cancelado'}
    try:
        if kind=='dxf':
            if path.suffix.lower()!='.dxf':return {'erro':'Selecione arquivo .dxf'}
            cmd=([sys.executable,'--probe-dxf',str(path)] if getattr(sys,'frozen',False)
                  else [sys.executable,str(ROOT/'engines/dxf_probe.py'),str(path)])
            p=subprocess.run(cmd,capture_output=True,text=True,timeout=40,
                             creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if p.returncode:return {'erro':(p.stderr or p.stdout)[-1200:]}
            return json.loads(p.stdout.strip().splitlines()[-1])
        if kind=='step':
            if path.suffix.lower() not in ('.step','.stp'):return {'erro':'Selecione STEP ou STP'}
            exe=freecadcmd()
            if not exe:return {'erro':'FreeCADCmd não instalado; use o leitor STEP OpenCascade local na aba Desenhos.'}
            with tempfile.TemporaryDirectory() as td:
                out=Path(td)/'saida.json'
                p=subprocess.run([exe,str(ROOT/'engines/freecad_probe.py'),str(path),str(out)],capture_output=True,text=True,
                                 timeout=100,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                if not out.is_file():return {'erro':'FreeCAD não retornou arquivo: '+(p.stderr or p.stdout)[-1000:]}
                return json.loads(out.read_text(encoding='utf-8'))
        return {'erro':'Motor desconhecido'}
    except subprocess.TimeoutExpired:
        return {'erro':'Tempo limite excedido'}
    except Exception as exc:
        return {'erro':str(exc)}

class API(QObject):
    @pyqtSlot(str,str,str,result='QVariant')
    def analyze_selected(self,engine,filename,encoded):
        ext=Path(filename).suffix.lower()
        expected=('.dxf',) if engine.startswith('dxf') else ('.step','.stp')
        if ext not in expected:return {'sucesso':False,'erro':'Extensão incompatível com o motor selecionado.'}
        if engine not in ('dxf_ezdxf','dxf_freecad','step_freecad'):
            return {'sucesso':False,'erro':'Motor não permitido'}
        if len(encoded)>55*1024*1024:return {'sucesso':False,'erro':'Limite de transferência excedido'}
        try:raw=base64.b64decode(encoded,validate=True)
        except (ValueError,binascii.Error):return {'sucesso':False,'erro':'Dados de arquivo inválidos'}
        if len(raw)>40*1024*1024:return {'sucesso':False,'erro':'Arquivo acima de 40 MB'}
        with tempfile.TemporaryDirectory(prefix='jeia_input_') as td:
            f=Path(td)/('desenho'+ext)
            f.write_bytes(raw)
            try:
                if engine=='dxf_ezdxf':r=ez_scan(f)
                else:r=freecad_analyze('dxf' if engine=='dxf_freecad' else 'step',f)
                r['nome_original']=Path(filename).name
                r['sha256_original']=hashlib.sha256(raw).hexdigest()
                r['apto_para_cnc']=False
                return r
            except Exception as e:
                log('Motor '+engine+': '+repr(e))
                return {'sucesso':False,'erro':type(e).__name__+': '+str(e),'motor':engine}


    @pyqtSlot(result='QVariant')
    def backup(self):return backup()

    @pyqtSlot(result='QVariant')
    def status(self):
        wasm=ROOT/'vendor'/'occt'/'occt-import-js.wasm'
        return {'freecad_instalado':bool(freecadcmd()),'freecad_caminho':freecadcmd(), 'ezdxf_instalado':True, 'dxf_embutido':True,
                'step_wasm_local':wasm.is_file() and wasm.stat().st_size>1_000_000,
                'base_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest()}

    @pyqtSlot(result='QVariant')
    def network_diagnostic(self):
        results=[]
        for url in ['https://www.google.com/generate_204','https://generativelanguage.googleapis.com/', 'https://cdn.jsdelivr.net/']:
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'JEIA-Diagnostico/2.0'},method='HEAD')
                with urllib.request.urlopen(req,timeout=7,context=ssl.create_default_context()) as resp:
                    code=resp.status
                results.append({'url':url,'http':code,'alcancavel':True})
            except Exception as ex:
                # HTTP 403/404 on API base still implies DNS/TLS connectivity succeeded.
                from urllib.error import HTTPError
                if isinstance(ex,HTTPError):results.append({'url':url,'http':ex.code,'alcancavel':True})
                else:results.append({'url':url,'alcancavel':False,'erro':str(ex)[:180]})
        return {'resultados':results,'nota':'HTTP 403/404 não comprova falha de rede. Teste de API Gemini requer chave e permissão e não é executado aqui.'}

    @pyqtSlot(str,result='QVariant')
    def test_file(self,kind):
        filtro='DXF (*.dxf)' if kind=='dxf' else 'STEP (*.step *.stp)'
        path,_=QFileDialog.getOpenFileName(None,'Selecionar desenho para teste (somente leitura)','',filtro+';;Todos (*.*)')
        if not path:return {'cancelado':True}
        return run_probe(kind,path)

    @pyqtSlot(str,str,result='QVariant')
    def save_json(self, filename, contents):
        if len(contents)>15*1024*1024:return {'ok':False,'erro':'Relatório acima de 15 MB; exportação cancelada'}
        try:
            obj=json.loads(contents)
            if not isinstance(obj,dict):return {'ok':False,'erro':'JSON inválido: objeto esperado'}
            clean=''.join(x for x in filename if x.isalnum() or x in ('_','-','.'))[:120]
            if not clean.lower().endswith('.json'):clean += '.json'
            if not clean:clean='JEIA_Relatorio.json'
            destination,_=QFileDialog.getSaveFileName(None,'Salvar relatório JSON do JEIA',str(Path.home()/'Downloads'/clean),'JSON (*.json)')
            if not destination:return {'cancelado':True,'ok':False}
            Path(destination).write_text(contents,encoding='utf-8')
            log('JSON salvo: '+str(destination))
            return {'ok':True,'arquivo':str(destination)}
        except Exception as ex:
            log('Erro ao salvar JSON: '+str(ex))
            return {'ok':False,'erro':str(ex)}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def do_GET(self):
        path=self.path.split('?',1)[0].split('#',1)[0]
        if path not in ('/jeia_shell.html','/JEIA_original_preservado.html','/favicon.ico') and not path.startswith('/vendor/occt/'):
            self.send_error(404)
            return
        super().do_GET()
    def list_directory(self,path):self.send_error(403);return None
    def log_message(self,fmt,*args):pass
    def guess_type(self,path):
        if path.endswith('.wasm'):return 'application/wasm'
        return super().guess_type(path)


def main():
    if '--probe-dxf' in sys.argv:
        import runpy
        sys.argv=[str(ROOT/'engines/dxf_probe.py'),sys.argv[2]]
        runpy.run_path(str(ROOT/'engines/dxf_probe.py'),run_name='__main__')
        return 0
    log('Abrindo JEIA CAD 04.1; Qt direto e bibliotecas STEP locais')
    backup()
    wasm=ROOT/'vendor'/'occt'/'occt-import-js.wasm'
    if not wasm.is_file() or wasm.stat().st_size<1_000_000:
        raise RuntimeError('Biblioteca STEP local não foi incluída. Compilação/instalação incompleta.')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    app=QApplication(sys.argv)
    window=QWebEngineView()
    window.setWindowTitle('JEIA TECH Industrial — Windows LAB • CAD 04.1')
    window.resize(1450,900);window.setMinimumSize(980,670)
    bridge=API();channel=QWebChannel(window.page());channel.registerObject('jeia',bridge)
    window.page().setWebChannel(channel)
    window.loadFinished.connect(lambda ok:log('Carregamento da interface: '+str(ok)))
    def handle_download(item):
        try:
            suggested=item.downloadFileName() or 'JEIA_Relatorio.json'
            dest,_=QFileDialog.getSaveFileName(window,'Salvar arquivo do JEIA',str(Path.home()/'Downloads'/suggested))
            if not dest:item.cancel();return
            p=Path(dest);item.setDownloadDirectory(str(p.parent));item.setDownloadFileName(p.name);item.accept()
            log('Download autorizado: '+str(p))
        except Exception as e:log('Falha ao autorizar download: '+str(e))
    window.page().profile().downloadRequested.connect(handle_download)
    url=f'http://127.0.0.1:{server.server_address[1]}/jeia_shell.html'
    window.load(QUrl(url));window.showMaximized()
    log('Janela Qt apresentada com servidor local restrito')
    code=app.exec()
    server.shutdown();server.server_close()
    log('Aplicativo encerrado pelo usuário; código '+str(code))
    return code

if __name__=='__main__':
    try:sys.exit(main())
    except BaseException as e:
        try:log('ERRO FATAL: '+repr(e)+'\n'+traceback.format_exc())
        except Exception:pass
        try:
            from ctypes import windll
            windll.user32.MessageBoxW(0,'Não foi possível abrir o JEIA. Consulte: '+str(LOGFILE)+'\n'+str(e),'JEIA — Erro de inicialização',0x10)
        except Exception:pass
        sys.exit(1)
