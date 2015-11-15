import sys
sys.path.insert(0, "/absolute/path/to/your/site/folder")

activate_this = "/absolute/path/to/your/venv/bin/activate_this.py"
execfile(activate_this, dict(__file__=activate_this))

from main import app as application
