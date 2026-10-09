"""
EvoLap Standalone Build Automation Script.

Builds the application into a standalone distribution directory via PyInstaller
and packages it into a release zip archive.

Usage:
    python scripts/build.py
    uv run python scripts/build.py
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def get_version() -> str:
    """Reads current project version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.is_file():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                return data.get("project", {}).get("version", "0.1.1")
        except Exception:
            pass
    return "0.1.1"


def build_app(skip_zip: bool = False, clean: bool = False) -> None:
    root_dir = Path(__file__).resolve().parent.parent
    os.chdir(root_dir)

    version = get_version()
    system_name = platform.system().lower()
    machine = platform.machine().lower()
    if system_name == "windows":
        plat_tag = "windows-x64" if "64" in machine else "windows-x86"
        sep = ";"
    elif system_name == "darwin":
        plat_tag = f"macos-{machine}"
        sep = ":"
    else:
        plat_tag = f"linux-{machine}"
        sep = ":"

    print("=" * 60)
    print(f"EvoLap Standalone Build Engine — v{version} ({plat_tag})")
    print("=" * 60)

    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"

    if clean:
        print("[1/3] Cleaning previous build artifacts...")
        if (dist_dir / "EvoLap").exists():
            shutil.rmtree(dist_dir / "EvoLap", ignore_errors=True)
        if build_dir.exists():
            shutil.rmtree(build_dir, ignore_errors=True)

    # 1. PyInstaller arguments
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--name",
        "EvoLap",
        "--add-data",
        f"assets{sep}assets",
        "--add-data",
        f"storage{sep}storage",
    ]

    # Windows PE header icon
    icon_ico = root_dir / "assets" / "favicon.ico"
    if system_name == "windows" and icon_ico.is_file():
        cmd.extend(["--icon", str(icon_ico)])

    cmd.append("main.py")

    print("[2/3] Compiling standalone executable with PyInstaller...")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[ERROR] PyInstaller build failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    output_app_dir = dist_dir / "EvoLap"
    if not output_app_dir.is_dir():
        print(f"[ERROR] Expected output directory not found at: {output_app_dir}")
        sys.exit(1)

    print(f"[SUCCESS] Standalone bundle created at: {output_app_dir}")

    # 2. Packaging into zip archive
    if not skip_zip:
        zip_filename = f"EvoLap-v{version}-{plat_tag}.zip"
        zip_path = dist_dir / zip_filename
        print(f"[3/3] Packaging into portable release archive: {zip_path.name}...")

        # Create zip archive of dist/EvoLap contents
        base_name = str(dist_dir / f"EvoLap-v{version}-{plat_tag}")
        archive_path = shutil.make_archive(
            base_name=base_name,
            format="zip",
            root_dir=str(output_app_dir),
        )
        archive_size_mb = Path(archive_path).stat().st_size / (1024 * 1024)
        print(f"[SUCCESS] Release archive ready ({archive_size_mb:.1f} MB): {archive_path}")
    else:
        print("[3/3] Skipping archive packaging (--skip-zip specified).")

    print("=" * 60)
    print("Build complete! Ready for local execution or GitHub Release upload.")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="EvoLap Build Script")
    parser.add_argument("--skip-zip", action="store_true", help="Skip creating release zip archive")
    parser.add_argument("--clean", action="store_true", help="Clean build and dist folders before build")
    args = parser.parse_args()

    build_app(skip_zip=args.skip_zip, clean=args.clean)


if __name__ == "__main__":
    main()
