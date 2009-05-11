from NGBoard import *
import NGBoardPanel
import os

NGF_WILDCARD = "Number Game File (*.ngf)|*.ngf|All files (*.*)|*.*"

[
	KEY_B,KEY_F,KEY_D,KEY_I,KEY_J,KEY_K,KEY_L,
	KEY_b,KEY_F,KEY_D,KEY_I,KEY_J,KEY_K,KEY_L,
	KEY_SPACE,KEY_0,KEY_EQUAL,KEY_MINUS,
	KEY_PLUS,KEY_UNDERLINE
] = map(ord,'BFDIJKLbfdijkl 0=-+_')
[IDT_GAME_NUM,IDT_PATTERN_NUM,ID_GAME_NUM,ID_PATTERN_NUM] = [wx.NewId() for i in xrange(4)]

class NGControlPanel(wx.Panel):
	def __init__(self, parent, frame=None):
		wx.Panel.__init__(
			self, parent, -1,
			style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE
		)
		self.frame = frame

		btnSizer = wx.BoxSizer(wx.VERTICAL)
		gnSpin = wx.SpinCtrl(self,-1,'1',size=(60,20),min=1,max=100000,initial=1)
		pnSpin = wx.SpinCtrl(self,-1,'1',size=(60,20),min=1,max=1000,initial=1)
		gnSpin.SetToolTip(wx.ToolTip("Load No. Game stored in NGData.ngb"))
		pnSpin.SetToolTip(wx.ToolTip("The bigger, the more difficult"))
		self.spinCtrls = [gnSpin,pnSpin]
		self.Bind(wx.EVT_SPINCTRL, self.OnSpin, id=gnSpin.GetId())
		self.Bind(wx.EVT_SPINCTRL, self.OnSpin, id=pnSpin.GetId())
		btnSizer.AddMany([
			self.GetToolButton(wx.ART_NEW,         'Random Game',  parent.OnRandomGame),
			self.GetToolButton(wx.ART_FILE_OPEN,   'Load Game', parent.OnLoadGame),
			self.GetToolButton(wx.ART_FILE_SAVE,   'Save Game', parent.OnSaveGame),
			((5,5),0,wx.EXPAND),
			self.GetToolButton(wx.ART_GO_BACK,     'Prev Move', parent.OnUndo),
			self.GetToolButton(wx.ART_GO_FORWARD,  'Next Move', parent.OnRedo),
			self.GetToolButton(wx.ART_TIP,         'Hint',      parent.OnHint),
			self.GetToolButton(wx.ART_FIND,        'Find Move', parent.OnAutoMove),
			((5,5),0,wx.EXPAND),
			self.GetToolButton(wx.ART_QUESTION,    'About',     parent.OnAbout),
			self.GetToolButton(wx.ART_QUIT,        'Exit',      parent.OnExit),
		])

		toolSizer = wx.BoxSizer(wx.HORIZONTAL)
		toolSizer.AddMany([
			((40,5),0,wx.EXPAND),
			(wx.StaticText(self,-1,'Game No:  '),0,wx.EXPAND),
			(gnSpin,0,wx.EXPAND),
			((20,5),0,wx.EXPAND),
			(wx.StaticText(self,-1,'Pattern No:  '),0,wx.EXPAND),
			(pnSpin,0,wx.EXPAND),
		])

		panelSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.boardPanel = NGBoardPanel.NGBoardPanel(self,frame)
		self.board = self.boardPanel.board
		panelSizer.AddMany([
			((5,0),0,wx.EXPAND),
			(btnSizer,0),
			((10,0),0,wx.EXPAND),
			(self.boardPanel,0)
		])
		mainSizer =  wx.BoxSizer(wx.VERTICAL)
		mainSizer.AddMany([
			((0,10),0,wx.EXPAND),
			(toolSizer,0,wx.EXPAND),
			((0,10),0,wx.EXPAND),
			(panelSizer,0)
		])
		self.SetSizer(mainSizer)
		self.mainSizer = mainSizer
		mainSizer.Fit(self)

	def OnSpin(self,evt=None):
		scv = [sc.GetValue() for sc in self.spinCtrls]
		self.board.LoadBoard(scv[0],scv[1])

	def GetToolButton(self,bmpName,btnName,action):
		btn = wx.BitmapButton(self,bitmap=GetBitmapByName(bmpName),name=btnName)
		self.Bind(wx.EVT_BUTTON,action,id = btn.GetId())
		btn.SetToolTip(wx.ToolTip(btnName))
		return (btn,0,wx.EXPAND)

