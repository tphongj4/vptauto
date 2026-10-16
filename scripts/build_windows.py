"""Build a Windows installer on Linux or Windows without executing Windows code.

The runtime and wheels are pinned and hash-verified. Windows execution is a
separate validation step, automated by the Windows CI workflow.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from package_portable import create_portable

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
STAGE = BUILD / "windows-stage"
VERSION = "0.3.0"
PYTHON_URL = "https://api.nuget.org/v3-flatcontainer/python/3.12.10/python.3.12.10.nupkg"
# NuGet's immutable package SHA512 (x-ms-meta-sha512, retrieved over verified TLS).
PYTHON_SHA512 = "u9pNz2iKlCEbYtUJaKkbOPMF0LjR7NkCafdKhvigpPzrt8oWKgdTpHaR6z3wyWQAm9PYGUxv0Zr66NX9AeHMDw=="


def unpack(archive: Path, destination: Path, prefix: str = "") -> None:
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            if not item.filename.startswith(prefix) or item.is_dir():
                continue
            relative = PurePosixPath(item.filename[len(prefix):])
            if relative.is_absolute() or ".." in relative.parts or "\\" in str(relative):
                raise RuntimeError("Unsafe archive member")
            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(item) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--makensis", type=Path)
    args = parser.parse_args()
    compiler = args.makensis or shutil.which("makensis")
    local_compiler = BUILD / "nsis/usr/bin/makensis"
    if not compiler and local_compiler.is_file():
        compiler = local_compiler
        os.environ["NSISDIR"] = str(BUILD / "nsis/usr/share/nsis")
    if not compiler:
        raise SystemExit("NSIS not found. On Linux run scripts/prepare_nsis.py; on Windows install NSIS.")
    downloads = BUILD / "windows-downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    runtime_package = downloads / "python.3.12.10.nupkg"
    if not runtime_package.exists():
        with urllib.request.urlopen(PYTHON_URL, timeout=90) as source, runtime_package.open("wb") as output:
            shutil.copyfileobj(source, output)
    if base64.b64encode(hashlib.sha512(runtime_package.read_bytes()).digest()).decode() != PYTHON_SHA512:
        raise SystemExit("Python package checksum failed. Delete the cached package and investigate before retrying.")
    subprocess.run([
        sys.executable, "-m", "pip", "download", "--disable-pip-version-check",
        "--dest", str(downloads), "--only-binary=:all:", "--platform", "win_amd64",
        "--python-version", "312", "--implementation", "cp", "--abi", "cp312",
        "--require-hashes", "-r", str(ROOT / "packaging/windows-requirements.lock"),
    ], check=True)
    # Read only the two explicitly pinned wheels, never arbitrary files from the cache.
    wheel_names = [
        "PySide6_Essentials-6.8.3-cp39-abi3-win_amd64.whl",
        "shiboken6-6.8.3-cp39-abi3-win_amd64.whl",
    ]
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    unpack(runtime_package, STAGE / "runtime", "tools/")
    for name in wheel_names:
        unpack(downloads / name, STAGE / "runtime/Lib/site-packages")
    (STAGE / "app").mkdir()
    shutil.copy2(ROOT / "main.py", STAGE / "app/main.py")
    shutil.copytree(ROOT / "src/vptauto", STAGE / "app/src/vptauto", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(ROOT / "README.md", STAGE / "README.md")
    shutil.copy2(ROOT / "packaging/THIRD_PARTY_NOTICES.txt", STAGE / "THIRD_PARTY_NOTICES.txt")
    # Keep installed runtime licenses and package license metadata in the distribution.
    required = ["runtime/python.exe", "runtime/pythonw.exe", "runtime/python312.dll",
                "runtime/Lib/site-packages/PySide6/QtWidgets.pyd",
                "runtime/Lib/site-packages/PySide6/Qt6Widgets.dll", "app/src/vptauto/ui.py"]
    if not all((STAGE / name).is_file() for name in required):
        raise SystemExit("Incomplete Windows runtime or UI dependencies.")
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    subprocess.run([sys.executable, str(ROOT / "scripts/make_icon.py")], check=True, env=env)
    defines = [f"-DSTAGE={STAGE}", f"-DSTAGE_FILES={STAGE / '*'}", f"-DAPP_VERSION={VERSION}", f"-DARTIFACTS={artifacts}", f"-DAPP_ICON={BUILD / 'app.ico'}"]
    for script in ("launcher.nsi", "installer.nsi"):
        subprocess.run([str(compiler), "-V3", "-INPUTCHARSET", "UTF8", *defines, str(ROOT / "packaging" / script)], check=True)
    installer = artifacts / f"VPTAuto-Setup-{VERSION}.exe"
    digest = hashlib.sha256(installer.read_bytes()).hexdigest()
    (artifacts / f"{installer.name}.sha256").write_text(f"{digest}  {installer.name}\n", encoding="utf-8")
    manifest = {"version": VERSION, "target": "Windows 10/11 x64", "installer_sha256": digest,
                "python": "3.12.10", "pyside6": "6.8.3", "windows_runtime_tested_by_this_build": False}
    (artifacts / "build-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    create_portable(STAGE, artifacts, VERSION)
    print(f"Installer created: {installer}\nWindows execution must be validated separately.")


if __name__ == "__main__":
    main()
