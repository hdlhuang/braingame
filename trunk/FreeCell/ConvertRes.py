import wx
import os
import re
import wx.tools.img2py as img2py
from Card import *
from Util import *

def ConvertCardImages():
	path = '.\\res1\\'
	allFiles = ListDirFiles(path)
	pyFile = os.path.join(path,'..\\FCRes.py')
	append = False
	for f in allFiles:
		i = GetIByName(f)
		fn = os.path.join(path,f)
		if i<0:
			imagName = ''
		else:
			imagName = '%02d'%i
		img2py.img2py(fn,pyFile,append=append,catalog=True,imgName=imagName)
		append = True

def ConvertIcons():
	path = '.\\ico\\'
	allFiles = ListDirFiles(path)
	pyFile = os.path.join(path,'..\\FCRes.py')
	append = False
	for f in allFiles:
		fn = os.path.join(path,f)
		img2py.img2py(fn,pyFile,append=True,catalog=True,icon=True)

if __name__ == "__main__":
	ConvertCardImages()
	ConvertIcons()