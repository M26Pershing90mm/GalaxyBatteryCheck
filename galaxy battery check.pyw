from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("galaxy battery gui.py")), run_name="__main__")
