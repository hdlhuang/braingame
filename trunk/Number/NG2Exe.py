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
    description = "Number Game",
    name = "Number Game",
    options = options,
    zipfile=None,
    windows=[{"script": "NGMain.pyw","icon_resources": [(1, "wxpdemo.ico")]}],
    )
