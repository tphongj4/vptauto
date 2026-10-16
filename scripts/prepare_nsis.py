"""Install a local NSIS compiler from authenticated Debian package metadata.

No root access or changes to the system package database are required.
"""

from __future__ import annotations

import hashlib
import lzma
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "build" / "nsis"
MIRROR = "https://deb.debian.org/debian/"


def download(url: str, target: Path) -> None:
    with urllib.request.urlopen(url, timeout=90) as response:
        with target.open("wb") as stream:
            shutil.copyfileobj(response, stream)


def main() -> None:
    if (DEST / "usr/bin/makensis").is_file():
        print("Local NSIS compiler already installed.")
        return
    DEST.mkdir(parents=True, exist_ok=True)
    verifier = shutil.which("sqv")
    if not verifier:
        raise SystemExit("Install sqv or use a system-installed makensis. Signature verification is required.")
    download(MIRROR + "dists/trixie/InRelease", DEST / "InRelease")
    release = DEST / "Release"
    release.unlink(missing_ok=True)
    subprocess.run([
        verifier, "--keyring", "/usr/share/keyrings/debian-archive-keyring.gpg",
        "--cleartext", "--output", str(release), str(DEST / "InRelease"),
    ], check=True)
    index_path = "main/binary-amd64/Packages.xz"
    checksums = release.read_text().split("\nSHA256:\n", 1)[1].split("\nSHA", 1)[0]
    expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1:] == [index_path])
    index = DEST / "Packages.xz"
    download(MIRROR + "dists/trixie/" + index_path, index)
    if hashlib.sha256(index.read_bytes()).hexdigest() != expected:
        raise SystemExit("Debian package index checksum failed.")
    packages = lzma.decompress(index.read_bytes()).decode()
    found = set()
    for paragraph in packages.split("\n\n"):
        fields = dict(line.split(": ", 1) for line in paragraph.splitlines() if ": " in line and not line.startswith(" "))
        name = fields.get("Package")
        if name not in {"nsis", "nsis-common"}:
            continue
        archive = DEST / Path(fields["Filename"]).name
        download(MIRROR + fields["Filename"], archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != fields["SHA256"]:
            raise SystemExit(f"Debian package checksum failed: {name}")
        subprocess.run(["dpkg-deb", "-x", str(archive), str(DEST)], check=True)
        found.add(name)
    if found != {"nsis", "nsis-common"}:
        raise SystemExit("NSIS packages were not present in the authenticated index.")
    os.environ["NSISDIR"] = str(DEST / "usr/share/nsis")
    subprocess.run([str(DEST / "usr/bin/makensis"), "-VERSION"], check=True)


if __name__ == "__main__":
    main()
