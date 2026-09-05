import argparse
from pathlib import Path
from .app import main
from .editor.runner import run_editor
parser=argparse.ArgumentParser(); parser.add_argument("--run-editor", metavar="PROJECT"); parser.add_argument("--entry",default="main.py")
args=parser.parse_args()
if args.run_editor: run_editor(Path(args.run_editor),args.entry)
else: raise SystemExit(main())
