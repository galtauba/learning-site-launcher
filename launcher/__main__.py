"""Executable entry point that works both as ``python -m launcher`` and in PyInstaller."""
import argparse
import sys
from pathlib import Path

# PyInstaller executes the supplied script as ``__main__``, not as the
# ``launcher`` package.  Make its parent importable before using absolute
# imports; relative imports would otherwise have no parent package.
if __package__ in (None, ""):
    package_parent = str(Path(__file__).resolve().parent.parent)
    if package_parent not in sys.path:
        sys.path.insert(0, package_parent)

from launcher.app import main
from launcher.editor.runner import run_editor


def run() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-editor", metavar="PROJECT")
    parser.add_argument("--entry", default="main.py")
    args = parser.parse_args()
    if args.run_editor:
        run_editor(Path(args.run_editor), args.entry)
        return 0
    return main()


if __name__ == "__main__":
    raise SystemExit(run())
