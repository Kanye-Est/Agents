"""Filesystem-backed skill installation with an auditable manifest.

This module intentionally keeps installation local to a per-run sandbox.  It
does not execute shell commands, access a remote registry, or install Python
dependencies.  A package is a directory containing ``SKILL.md`` and optional
handler files.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MANIFEST_NAME = ".acquisition-manifest.json"
MANIFEST_SCHEMA_VERSION = 1
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_IGNORED_PARTS = {"__pycache__"}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}


class InstallationError(RuntimeError):
    """Raised when a package cannot be safely copied or verified."""


@dataclass(frozen=True)
class InstalledPackage:
    name: str
    path: Path
    package_sha256: str
    files: dict[str, str]


def install_package(
    source_dir: Path,
    install_root: Path,
    *,
    expected_name: str,
) -> InstalledPackage:
    """Copy one package into ``install_root`` and verify its manifest.

    The copy is staged under the same root and atomically renamed into place.
    Existing destinations are rejected so every experimental run has an
    unambiguous installation transition.
    """
    source = Path(source_dir).resolve()
    root = Path(install_root).resolve()
    _validate_name(expected_name)
    _validate_source(source)
    root.mkdir(parents=True, exist_ok=True)

    destination = root / expected_name
    if destination.exists():
        raise InstallationError(f"destination already exists: {destination}")

    staging = root / f".{expected_name}.staging-{uuid.uuid4().hex}"
    try:
        shutil.copytree(
            source,
            staging,
            symlinks=False,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        files, digest = hash_package_tree(staging)
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "name": expected_name,
            "package_sha256": digest,
            "files": files,
        }
        (staging / MANIFEST_NAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(staging, destination)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    verified = verify_installed_package(destination, expected_name=expected_name)
    return InstalledPackage(
        name=expected_name,
        path=destination,
        package_sha256=verified["package_sha256"],
        files=verified["files"],
    )


def verify_installed_package(
    package_dir: Path,
    *,
    expected_name: str | None = None,
) -> dict[str, Any]:
    """Verify manifest, file set, and hashes for an installed package."""
    package = Path(package_dir).resolve()
    manifest_path = package / MANIFEST_NAME
    if not manifest_path.is_file():
        raise InstallationError(f"missing install manifest: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallationError(f"invalid install manifest: {exc}") from exc

    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise InstallationError("unsupported install manifest schema")
    name = manifest.get("name")
    if not isinstance(name, str):
        raise InstallationError("manifest name is missing")
    _validate_name(name)
    if expected_name is not None and name != expected_name:
        raise InstallationError(
            f"manifest name mismatch: expected {expected_name}, got {name}"
        )

    files, digest = hash_package_tree(package)
    if manifest.get("files") != files:
        raise InstallationError("installed package file set or file hash changed")
    if manifest.get("package_sha256") != digest:
        raise InstallationError("installed package digest changed")

    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "name": name,
        "package_sha256": digest,
        "files": files,
    }


def hash_package_tree(package_dir: Path) -> tuple[dict[str, str], str]:
    """Return per-file SHA-256 hashes and a deterministic package digest."""
    package = Path(package_dir).resolve()
    if not package.is_dir():
        raise InstallationError(f"package directory does not exist: {package}")

    file_hashes: dict[str, str] = {}
    for path in sorted(package.rglob("*")):
        if not path.is_file() or _ignore_path(path, package):
            continue
        if path.is_symlink():
            raise InstallationError(f"symbolic links are not allowed: {path}")
        relative = path.relative_to(package).as_posix()
        file_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()

    if "SKILL.md" not in file_hashes:
        raise InstallationError("package is missing SKILL.md")

    aggregate = hashlib.sha256()
    for relative, file_digest in sorted(file_hashes.items()):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(file_digest.encode("ascii"))
        aggregate.update(b"\n")
    return file_hashes, aggregate.hexdigest()


def _validate_source(source: Path) -> None:
    if not source.is_dir():
        raise InstallationError(f"source package does not exist: {source}")
    if not (source / "SKILL.md").is_file():
        raise InstallationError(f"source package has no SKILL.md: {source}")
    for path in source.rglob("*"):
        if path.is_symlink():
            raise InstallationError(f"symbolic links are not allowed: {path}")


def _validate_name(name: str) -> None:
    if not _SAFE_NAME.fullmatch(name or ""):
        raise InstallationError(f"unsafe package name: {name!r}")


def _ignore_path(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if relative.as_posix() == MANIFEST_NAME:
        return True
    if any(part in _IGNORED_PARTS for part in relative.parts):
        return True
    return path.suffix in _IGNORED_SUFFIXES
