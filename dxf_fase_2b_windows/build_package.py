"""Build only this independent diagnostic package; standard library only."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
ZIP_NAME = 'JEIA_DXF_TECH_FASE_2B_DIAGNOSTICO_WINDOWS_CORRECOES_R01.zip'
PREFIX = ZIP_NAME[:-4]


def main():
    files = sorted(p for p in ROOT.rglob('*') if p.is_file()
                   and not any(x in ('__pycache__', 'resultados', '.git') for x in p.relative_to(ROOT).parts)
                   and p.suffix != '.pyc' and p.name != 'MANIFESTO_SHA256.txt')
    manifest = ROOT / 'MANIFESTO_SHA256.txt'
    manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' +
                                p.relative_to(ROOT).as_posix() + '\n' for p in files), encoding='utf-8')
    files.append(manifest)
    destination = ROOT.parent / ZIP_NAME
    # Deterministic archive: only package files, fixed timestamps and permissions.
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            name = PREFIX + '/' + path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix('.zip.sha256').write_text(digest + '  ' + ZIP_NAME + '\n', encoding='ascii')
    print(destination.name, destination.stat().st_size, 'bytes', digest)


if __name__ == '__main__':
    main()
