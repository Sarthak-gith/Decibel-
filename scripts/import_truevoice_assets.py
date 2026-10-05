"""Validate and install a cloud-exported TrueVoice asset bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(name: str, root_name: str) -> PurePosixPath:
    member = PurePosixPath(name)
    if member.is_absolute() or ".." in member.parts or not member.parts:
        raise ValueError(f"Unsafe path in asset archive: {name!r}")
    if member.parts[0] != root_name:
        raise ValueError(f"Unexpected top-level archive path: {name!r}")
    return member


def import_assets(archive_path: Path, destination: Path, overwrite: bool = False) -> None:
    archive_path = archive_path.resolve()
    destination = destination.resolve()
    root_name = "decibel_truevoice_assets"
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)
    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Assets already exist at {destination}; choose a new destination or pass --overwrite."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging_parent = Path(tempfile.mkdtemp(prefix="truevoice-assets-", dir=destination.parent))
    staging_root = staging_parent / root_name
    staging_root.mkdir()
    try:
        with zipfile.ZipFile(archive_path) as bundle:
            names: set[str] = set()
            for info in bundle.infolist():
                member = _safe_member(info.filename, root_name)
                if info.is_dir():
                    continue
                if info.filename in names:
                    raise ValueError(f"Duplicate path in asset archive: {info.filename!r}")
                names.add(info.filename)
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError(f"Symlink in asset archive is not allowed: {info.filename!r}")
                output = staging_parent.joinpath(*member.parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info) as source, output.open("wb") as target:
                    shutil.copyfileobj(source, target, length=8 * 1024 * 1024)

        manifest_path = staging_root / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError("Asset bundle is missing manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = manifest.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError("Asset manifest has no file checksums")
        for relative_name, expected in files.items():
            relative = PurePosixPath(relative_name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Unsafe manifest path: {relative_name!r}")
            file_path = staging_root.joinpath(*relative.parts)
            if not file_path.is_file():
                raise ValueError(f"Manifest file is missing: {relative_name}")
            if file_path.stat().st_size != expected.get("bytes"):
                raise ValueError(f"Size mismatch for {relative_name}")
            if _sha256(file_path) != expected.get("sha256"):
                raise ValueError(f"SHA-256 mismatch for {relative_name}")

        required = [
            staging_root / "audio_tower" / "config.json",
            staging_root / "processor" / "preprocessor_config.json",
            staging_root / "classifier_head.pt",
        ]
        if not all(path.is_file() for path in required):
            missing = [str(path.relative_to(staging_root)) for path in required if not path.is_file()]
            raise ValueError(f"Required inference asset(s) missing: {missing}")

        if destination.exists():
            if not overwrite:
                raise FileExistsError(destination)
            if not destination.is_dir():
                raise NotADirectoryError(destination)
            shutil.rmtree(destination)
        staging_root.replace(destination)
        print(f"Validated {len(files)} files; assets installed at {destination}")
        print(f"Model revision: {manifest.get('model_revision', 'unknown')}")
    finally:
        shutil.rmtree(staging_parent, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument(
        "--destination", type=Path, default=Path("engine/assets/truevoice")
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    import_assets(args.archive, args.destination, args.overwrite)


if __name__ == "__main__":
    main()
