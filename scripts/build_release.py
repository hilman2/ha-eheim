"""Build a ZIP that can be extracted into the Home Assistant config directory."""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "eheimdigital_plus"


def build_release(output_dir: Path) -> Path:
    """Package the integration and its bundled protocol code and licenses."""
    version = json.loads((COMPONENT / "manifest.json").read_text())["version"]
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"ha-eheim-{version}.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as output:
        for path in sorted(COMPONENT.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                output.write(path, path.relative_to(ROOT))
    return archive


if __name__ == "__main__":
    print(build_release(ROOT / "dist"))
