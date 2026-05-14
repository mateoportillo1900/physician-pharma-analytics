"""
Render the Mermaid diagrams in docs/ as PNG images using mermaid.ink.

Why this exists: GitHub renders Mermaid inline, but LinkedIn, Twitter,
and most other surfaces do not. So when you want to share the
architecture diagram on social or paste it into a slide deck, you need
a PNG. This script generates them on demand.

Run:
    python scripts/export_diagrams.py

Outputs to docs/images/*.png.

The mermaid.ink service is free, no auth, and returns the PNG directly
when you POST a base64-encoded graph to https://mermaid.ink/img/<b64>.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Force UTF-8 stdout so emoji/unicode print on Windows (cp1252 default)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import requests

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMAGES_DIR = DOCS / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def render_to_png(mermaid_source: str, output_path: Path) -> None:
    """Render a Mermaid diagram to PNG via Kroki.io (POST endpoint).

    Kroki has no length limit (unlike mermaid.ink's GET-based encoding),
    so we POST the raw source and get the PNG back directly.

    Args:
        mermaid_source: The Mermaid markup (without the ```mermaid fence)
        output_path: Where to save the PNG
    """
    print(f"  Rendering {output_path.name}...")
    response = requests.post(
        "https://kroki.io/mermaid/png",
        data=mermaid_source.encode("utf-8"),
        headers={"Content-Type": "text/plain"},
        timeout=45,
    )
    response.raise_for_status()

    output_path.write_bytes(response.content)
    print(
        f"    ✓ {output_path.relative_to(ROOT)}  "
        f"({len(response.content) / 1024:.1f} KB)"
    )


def extract_mermaid_blocks(markdown_path: Path) -> list[str]:
    """Pull every ```mermaid ... ``` code block out of a markdown file."""
    content = markdown_path.read_text(encoding="utf-8")
    blocks = []
    in_block = False
    current: list[str] = []

    for line in content.splitlines():
        if line.strip() == "```mermaid":
            in_block = True
            current = []
        elif line.strip() == "```" and in_block:
            blocks.append("\n".join(current))
            in_block = False
        elif in_block:
            current.append(line)

    return blocks


def main() -> int:
    print("=" * 60)
    print(" Mermaid → PNG export")
    print("=" * 60)

    # Extract diagrams from ARCHITECTURE.md and DATA_MODEL.md
    arch_blocks = extract_mermaid_blocks(DOCS / "ARCHITECTURE.md")
    data_blocks = extract_mermaid_blocks(DOCS / "DATA_MODEL.md")

    print(f"\nFound {len(arch_blocks)} diagrams in ARCHITECTURE.md")
    print(f"Found {len(data_blocks)} diagrams in DATA_MODEL.md")

    # ARCHITECTURE.md diagrams in order:
    arch_names = [
        "01-system-overview",
        "02-data-pipeline",
        "03-dbt-lineage",
        "04-user-interaction-flow",
        "05-llm-flow",
    ]
    # DATA_MODEL.md diagrams in order:
    data_names = [
        "06-star-schema",
        "07-headline-join",
        "08-data-quality",
        "09-privacy-design",
    ]

    print("\nRendering...")
    for source, name in zip(arch_blocks, arch_names, strict=False):
        render_to_png(source, IMAGES_DIR / f"{name}.png")
    for source, name in zip(data_blocks, data_names, strict=False):
        render_to_png(source, IMAGES_DIR / f"{name}.png")

    print(
        f"\n✓ Done. {len(arch_blocks) + len(data_blocks)} PNGs in {IMAGES_DIR.relative_to(ROOT)}/"
    )
    print("\nFor LinkedIn: drag docs/images/01-system-overview.png directly into")
    print("the post composer. It will render full-size in the feed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
