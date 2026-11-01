"""Check module coverage for the HA integration separately from bundled protocol code."""

import argparse
import json
from pathlib import Path
from typing import Any

COMPONENT = Path("custom_components/eheimdigital_plus")


def check_coverage(report: dict[str, Any]) -> list[str]:
    """Require over 95% per HA module and full coverage for the config flow."""
    failures = []
    measured = set()
    for filename, data in report["files"].items():
        path = Path(filename)
        if path.parent != COMPONENT:
            continue
        measured.add(path.name)
        covered = data["summary"]["percent_covered"]
        required = 100 if path.name == "config_flow.py" else 95
        if covered < required or covered == 95:
            failures.append(
                f"{filename}: {covered:.2f}% coverage, required {'100%' if required == 100 else '>95%'}"
            )
    for path in COMPONENT.glob("*.py"):
        if path.name not in measured:
            failures.append(f"{path}: missing coverage")
    return failures


def main() -> None:
    """Read a Coverage.py JSON report and fail when an integration module is below its target."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    failures = check_coverage(json.loads(args.report.read_text()))
    if failures:
        parser.exit(1, "\n".join(failures) + "\n")
    print("Every HA module exceeds 95%; config flow is fully covered.")


if __name__ == "__main__":
    main()
