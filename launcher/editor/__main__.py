import argparse
from pathlib import Path
from .runner import run_editor
parser=argparse.ArgumentParser(); parser.add_argument("project"); parser.add_argument("--entry", default="main.py")
args=parser.parse_args(); run_editor(Path(args.project), args.entry)
