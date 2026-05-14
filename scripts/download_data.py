"""
Download CMS Open Payments + Medicare Part D datasets locally.

These files are large (multi-GB) — we download them once into data/raw/
(which is gitignored), then load_data.py applies filtering before pushing
into Neon. Re-running this script is idempotent: it skips files that
already exist on disk.

Run:
    python scripts/download_data.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

# Make project root importable regardless of how this script is invoked
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Force UTF-8 stdout so emoji/unicode print on Windows (cp1252 default)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import requests
from tqdm import tqdm

from scripts.config import (
    OPEN_PAYMENTS_URL,
    PART_D_PROVIDER_URL,
    PART_D_PROVIDER_DRUG_URL,
    RAW_DIR,
)


def download_file(url: str, dest: Path, chunk_size: int = 1 << 20) -> None:
    """Stream-download a URL to disk with a progress bar. Skips if file exists."""
    if dest.exists():
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"  ✓ {dest.name} already exists ({size_mb:.1f} MB) — skipping")
        return

    print(f"  ↓ Downloading {url}")
    print(f"    → {dest}")

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with (
            open(dest, "wb") as f,
            tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=f"    {dest.name}",
            ) as pbar,
        ):
            for chunk in r.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                pbar.update(len(chunk))


def unzip_open_payments(zip_path: Path) -> Path:
    """Extract the General Payments CSV from the Open Payments zip."""
    extract_dir = RAW_DIR / "open_payments_unzipped"
    extract_dir.mkdir(exist_ok=True)

    # Look for the general payments file already extracted
    existing = list(extract_dir.glob("OP_DTL_GNRL_PGYR*.csv"))
    if existing:
        print(f"  ✓ Already extracted: {existing[0].name}")
        return existing[0]

    print(f"  📦 Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path) as z:
        # Open Payments zips contain General, Research, and Ownership files.
        # We only want General (the bulk of pharma rep / KOL payments).
        general_files = [
            name
            for name in z.namelist()
            if name.startswith("OP_DTL_GNRL_PGYR") and name.endswith(".csv")
        ]
        if not general_files:
            raise RuntimeError(
                f"No General Payments CSV found in {zip_path.name}. "
                f"Archive contents: {z.namelist()[:10]}..."
            )
        target = general_files[0]
        print(f"    → extracting {target}")
        z.extract(target, extract_dir)

    extracted = extract_dir / target
    print(f"  ✓ Extracted to {extracted}")
    return extracted


def main() -> int:
    print("=" * 72)
    print(" CMS Data Download")
    print("=" * 72)
    print(f"\nData destination: {RAW_DIR}\n")

    print("[1/3] CMS Open Payments — General Payments 2022 (~500 MB zip)")
    op_zip = RAW_DIR / "open_payments_2022.zip"
    try:
        download_file(OPEN_PAYMENTS_URL, op_zip)
        unzip_open_payments(op_zip)
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ Open Payments download failed: {exc}")
        print(
            "  If the CMS URL has changed, find the current 2022 General "
            "Payments link at https://www.cms.gov/openpayments and update "
            "OPEN_PAYMENTS_URL in scripts/config.py"
        )
        return 1

    print("\n[2/3] CMS Medicare Part D Prescribers by Provider 2022 (~110 MB)")
    pd_provider = RAW_DIR / "part_d_provider_2022.csv"
    try:
        download_file(PART_D_PROVIDER_URL, pd_provider)
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ Part D Provider download failed: {exc}")
        return 1

    print("\n[3/3] CMS Medicare Part D Prescribers by Provider AND Drug 2022 (~3 GB)")
    print("      We download the full file but only load a filtered subset.")
    pd_drug = RAW_DIR / "part_d_provider_drug_2022.csv"
    try:
        download_file(PART_D_PROVIDER_DRUG_URL, pd_drug)
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ Part D Provider-Drug download failed: {exc}")
        return 1

    print("\n" + "=" * 72)
    print(" ✓ All downloads complete")
    print("=" * 72)
    print("\nNext step: python scripts/load_data.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
