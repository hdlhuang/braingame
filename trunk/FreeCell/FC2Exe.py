from distutils.core import setup
import py2exe
includes = ["encodings", "encodings.*"]
options = {"py2exe":
            {   "compressed": 1,
                "optimize": 2,
                "includes": includes,
                "bundle_files": 1
            }
          }
setup(
    version = "0.1.0",
    description = "FreeCell Game",
    name = "FreeCell Game",
    options = options,
    zipfile=None,
    windows=[{"script": "FCMain.py","icon_resources": [(1, "ico\\fc.ico")]}],
)
#d:\Softs\Python\python.exe FC2Exe.py py2exe