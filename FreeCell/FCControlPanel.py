import os
import FCAbout
from FCGame import *
from Util import *

FCF_WILDCARD = "FreeCell Game File (*.fcf)|*.fcf|All files (*.*)|*.*"

[IDT_GAME_NUM,ID_GAME_NUM] = [wx.NewId() for i in xrange(2)]

class FCControlPanel(wx.Panel):
	def __init__(self, parent, log=None):
		wx.Panel.__init__(
			self, parent, -1,
			style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE
		)
		self.parent = parent
		self.log = log

		self.gnSpin = gnSpin = wx.SpinCtrl(self,-1,'1',size=(60,20),min=1,max=100000,initial=1)
		gnSpin.SetToolTip(wx.ToolTip("Load No. Game"))
		self.Bind(wx.EVT_SPINCTRL, self.OnSpin, id=gnSpin.GetId())

		self.scSpin = scSpin = wx.SpinCtrl(self,-1,'1',size=(60,20),min=1,max=3,initial=1)
		self.debugCB = wx.CheckBox(self,-1,'Debug?')
		self.fastModeCB = wx.CheckBox(self,-1,'Fast Move?')
		scSpin.SetToolTip(wx.ToolTip("Seach Method"))

		btnSizer = wx.BoxSizer(wx.HORIZONTAL)
		btnSizer.AddMany([
			((5,5),0,wx.EXPAND),
			(wx.StaticText(self,-1,'Game No:  '),0,wx.EXPAND),
			((5,5),0,wx.EXPAND),
			(gnSpin,0,wx.EXPAND),
			(scSpin,0,wx.EXPAND),
			((5,5),0,wx.EXPAND),
			(self.debugCB,0,wx.EXPAND),
			(self.fastModeCB,0,wx.EXPAND),
			((5,5),0,wx.EXPAND),
			self.GetToolButton(wx.ART_NEW,       'Random Game', self.OnRandomGame),
			self.GetToolButton(wx.ART_FILE_OPEN,   'Load Game', self.OnLoadGame),
			self.GetToolButton(wx.ART_FILE_SAVE,   'Save Game', self.OnSaveGame),
			((5,5),0,wx.EXPAND),
			self.GetToolButton(wx.ART_GO_BACK,     'Prev Move', self.OnUndo),
			self.GetToolButton(wx.ART_GO_FORWARD,  'Next Move', self.OnRedo),
			self.GetToolButton(wx.ART_FIND,        'Start Search', self.OnStartAuto),
			self.GetToolButton(wx.ART_ERROR,       'Stop Search', self.OnStopAuto),
			((5,5),0,wx.EXPAND),
			self.GetToolButton(wx.ART_QUESTION,    'About',     self.OnAbout),
			self.GetToolButton(wx.ART_QUIT,        'Exit',      self.OnExit),
		])
		mainSizer =  wx.BoxSizer(wx.VERTICAL)
		self.gamePanel = FCGamePanel(self,parent)
		#self.logTC = wx.TextCtrl(self,-1,'')

		mainSizer.AddMany([
			((0,10),0,wx.EXPAND),
			(btnSizer,0,wx.EXPAND),
			((0,10),0,wx.EXPAND),
			(self.gamePanel,0,wx.EXPAND|wx.ALL),
			((0,10),0,wx.EXPAND),
			#(self.logTC,0,wx.EXPAND|wx.ALL)
		])
		self.SetSizer(mainSizer)
		self.mainSizer = mainSizer
		mainSizer.Fit(self)
		self.SetAutoLayout(True)
		self.gamePanel.OnKeyDown('r')

	def OnSpin(self,evt=None):
		scv = self.gnSpin.GetValue()
		self.gamePanel.LoadGame(scv)

	def GetToolButton(self,bmpName,btnName,action):
		btn = wx.BitmapButton(self,bitmap=GetBitmapByName(bmpName),name=btnName)
		self.Bind(wx.EVT_BUTTON,action,id = btn.GetId())
		btn.SetToolTip(wx.ToolTip(btnName))
		return (btn,0,wx.EXPAND)
	def OnStartAuto(self,evt=None):
		self.gamePanel.StartSearch()
	def OnStopAuto(self,evt=None):
		self.gamePanel.StopSearch()
	def OnUndo(self,evt=None):
		self.gamePanel.OnBackward()
	def OnRedo(self,evt=None):
		self.gamePanel.OnForward()
	def OnRandomGame(self,evt=None):
		self.gamePanel.LoadGame(-1)

	def OnLoadGame(self,evt=None):
		try:
			fileName = self.ChooseFileName("Load FreeCell Game File",wx.OPEN,FCF_WILDCARD)
			if fileName:
				self.gamePanel.LoadFromFile(fileName)
		except:
			wx.MessageBox('Error in reading file')
	def OnSaveGame(self,evt=None):
		try:
			fileName = self.ChooseFileName("Save FreeCell Game File",wx.SAVE,FCF_WILDCARD)
			if fileName:
				self.gamePanel.SaveToFile(fileName)
		except:
			wx.MessageBox('Error in saving file')

	#def OnClose(self,evt=None):
	#	self.parent.Destroy()
	def ChooseFileName(self,msg="Choose a file",dlgStyle=wx.OPEN,wildcard=FCF_WILDCARD):
		dlg = wx.FileDialog(
			self, message=msg,
			defaultDir=os.getcwd(),
			defaultFile="",
			wildcard=wildcard,
			style=dlgStyle|wx.CHANGE_DIR
		)
		# Show the dialog and retrieve the user response. If it is the OK response,
		# process the data.
		fileNames = []
		if dlg.ShowModal() == wx.ID_OK:
			# This returns a Python list of files that were selected.
			fileNames = dlg.GetPaths()
		dlg.Destroy()
		if len(fileNames)<1:
			return ''
		else:
			return fileNames[0]

	def OnExit(self,evt=None):
		#quick save
		#self.gamePanel.OnKeyDown('e')
		self.gamePanel.OnExit()
		self.parent.Destroy()

	def OnAbout(self,evt=None):
		dlg = FCAbout.FCAboutBox(self)
		dlg.ShowModal()
		dlg.Destroy()