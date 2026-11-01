"""Check the files actually delivered to a Home Assistant installation."""

import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from scripts.build_release import build_release


def test_archive_imports_without_external_library(tmp_path: Path) -> None:
    """Import every shipped module from the extracted ZIP in a fresh process."""
    archive = build_release(tmp_path / "release")
    config_dir = tmp_path / "config"
    with ZipFile(archive) as package:
        assert not any("__pycache__" in name for name in package.namelist())
        package.extractall(config_dir)
    component = config_dir / "custom_components/eheimdigital"
    manifest = json.loads((component / "manifest.json").read_text())
    assert manifest["requirements"] == []
    assert (component / "LICENSE").is_file()
    assert (component / "_vendor/eheimdigital/LICENSE").is_file()
    code = """
import importlib
import importlib.util
import pkgutil
import sys

sys.path.insert(0, sys.argv[1])
assert importlib.util.find_spec("eheimdigital") is None
import custom_components.eheimdigital as integration
assert integration.__file__.startswith(sys.argv[1])
for module in pkgutil.walk_packages(integration.__path__, integration.__name__ + "."):
    importlib.import_module(module.name)
assert "eheimdigital" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(config_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
