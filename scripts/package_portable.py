"""Zip the already prepared Windows application for use without installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from vptauto import __version__


def create_portable(stage: Path, artifacts: Path, version: str) -> Path:
    required = (
        "VPTAuto.exe", "runtime/pythonw.exe", "runtime/python312.dll",
        "runtime/Lib/site-packages/PySide6/QtWidgets.pyd",
        "runtime/Lib/site-packages/PySide6/Qt6Widgets.dll",
        "runtime/Lib/site-packages/PySide6/plugins/platforms/qwindows.dll",
        "app/main.py", "app/src/vptauto/__init__.py", "THIRD_PARTY_NOTICES.txt",
    )
    if not all((stage / name).is_file() for name in required):
        raise RuntimeError("Windows application bundle is incomplete. Run scripts/build_windows.py first.")
    for name in ("VPTAuto.exe", "runtime/pythonw.exe"):
        with (stage / name).open("rb") as stream:
            if stream.read(2) != b"MZ":
                raise RuntimeError(f"Not a Windows executable: {name}")
    # Reject a stale app bundle rather than labeling older code as the current version.
    for path in (ROOT / "src/vptauto").glob("*.py"):
        staged = stage / "app/src/vptauto" / path.name
        if not staged.is_file() or staged.read_bytes() != path.read_bytes():
            raise RuntimeError("Staged app differs from current source. Rebuild the Windows bundle first.")
    if (stage / "app/main.py").read_bytes() != (ROOT / "main.py").read_bytes():
        raise RuntimeError("Staged entrypoint differs from current source. Rebuild first.")
    artifacts.mkdir(parents=True, exist_ok=True)
    target = artifacts / f"VPTAuto-Portable-{version}.zip"
    temporary = target.with_suffix(".zip.tmp")
    prefix = f"VPTAuto-{version}"
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_symlink():
                    raise RuntimeError("Unexpected symlink in the Windows bundle.")
                if not path.is_file():
                    continue
                relative = path.relative_to(stage)
                if relative == Path("README.md") or "__pycache__" in relative.parts:
                    continue
                archive.write(path, f"{prefix}/{relative.as_posix()}")
            archive.write(ROOT / "README.md", f"{prefix}/README.md")
            archive.write(ROOT / "packaging/PORTABLE_GUIDE.txt", f"{prefix}/HUONG_DAN.txt")
            # Windows cmd reads a native CRLF batch file; all commands are ASCII.
            batch = (ROOT / "packaging/ChayThu.bat").read_text(encoding="utf-8")
            archive.writestr(f"{prefix}/ChayThu.bat", batch.replace("\n", "\r\n"))
        with ZipFile(temporary) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise RuntimeError(f"Portable archive CRC failure: {bad}")
            count = len(archive.namelist())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_name(target.name + ".sha256").write_text(f"{digest}  {target.name}\n", encoding="utf-8")
    manifest = {
        "version": version, "target": "Windows 10/11 x64", "format": "portable ZIP",
        "sha256": digest, "files": count, "python_required_on_user_machine": False,
        "windows_runtime_tested_by_this_packaging_step": False,
    }
    target.with_name(target.name + ".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Portable ZIP created: {target} ({target.stat().st_size / 1024 / 1024:.1f} MiB)")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=ROOT / "build/windows-stage")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    create_portable(args.stage, args.output_dir, __version__)
