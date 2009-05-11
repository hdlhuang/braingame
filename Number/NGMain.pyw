
# -*- coding: gbk -*-
import wx
import os
import random
import time
import NGBoard
import NGBoardPanel
import NGControlPanel
import NGRes

def _x(str):
	return unicode(str,"gbk")

NGF_WILDCARD = "Number Game File (*.ngf)|*.ngf|All files (*.*)|*.*"

[
	TB_NEW,TB_LOAD,TB_SAVE,TB_UNDO,TB_REDO,TB_HINT,TB_AUTO,TB_HELP
] = [wx.NewId() for x in range(8)]
[
	MI_SEARCH,MI_RANDOM,MI_NEW,MI_LOAD,MI_SAVE,MI_EXIT,
	MI_UNDO,MI_REDO,MI_HINT,MI_AUTO,MI_HELP,
	MI_ABOUT,MI_ANI
] = [wx.NewId() for x in range(13)]

class NGFrame(wx.Frame):
	MENUS = (
		("&Game",
			["Exit Game", "E&xit\tCtrl-Q"],
			["New Game", "&New\tCtrl-N"],
			["Load Game", "&Load\tCtrl-L"],
			["Save Game", "&Save\tCtrl-L"]
		)
	)

	def __init__(self, ngApp, parent = None, id=wx.ID_ANY, title="Number Game", pos=wx.DefaultPosition,
				 size=(360,460), style=wx.DEFAULT_FRAME_STYLE):

		wx.Frame.__init__(self, parent, id, title, pos, size, style)
		self.ngApp = ngApp
		#win = NGBoardPanel.NGBoardPanel(self, self)
		self.SetIcon(NGRes.GetNGIcon())
		self.InitMenuBar()
		self.statusBar = self.CreateStatusBar(3, wx.ST_SIZEGRIP)
		self.statusBar.SetStatusWidths([-3, -3,-5])
		self.statusBar.SetStatusText("HL @ 2008", 1)
		self.statusBar.SetStatusText("Welcome to Number Game!", 2)
		#self.SetSize(NGBoard.BOARD_SIZE)
		win = NGControlPanel.NGControlPanel(self, self)
		self.topPanel = win
		self.boardPanel = win.boardPanel
		self.board = self.boardPanel.board
		#self.Center()
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.Show(True)
		self.SetMinSize(self.GetSize())
		self.SetMaxSize(self.GetSize())

	def GetMenuBarEng(self):
		mb = wx.MenuBar()
		menu = wx.Menu()
		#search games is only used to generate game solutions
		#item = menu.Append(MI_SEARCH, "Se&arch Games", "")
		item = menu.Append(MI_NEW, "&New\tCtrl-N", "New Game")
		item = menu.Append(MI_RANDOM, "&Random\tCtrl-R", "New Random Game")
		item = menu.Append(MI_LOAD, "&Load\tCtrl-L", "Load Game")
		item = menu.Append(MI_SAVE, "&Save\tCtrl-S", "Save Game")
		item = menu.Append(MI_EXIT, "E&xit\tCtrl-Q", "Exit Game")
		mb.Append(menu,"&Game")

		menu = wx.Menu()
		item = menu.Append(MI_UNDO, "&Undo\tCtrl-Z", "Undo Move")
		item = menu.Append(MI_REDO, "&Redo\tCtrl-Y", "Redo Move")
		item = menu.Append(MI_HINT, "&Hint\tCtrl-H", "Show Hint")
		item = menu.Append(MI_AUTO, "&Auto Move\tCtrl-M", "Auto Move")
		item = menu.Append(MI_ANI,  "Animation\tCtrl-A", "Cycle animation type")
		mb.Append(menu,"&Move")

		menu = wx.Menu()
		item = menu.Append(MI_ABOUT, "&About", "Introduction")
		mb.Append(menu,"&Help")
		return mb

	def GetMenuBarChs(self):
		mb = wx.MenuBar()
		menu = wx.Menu()
		#search games is only used to generate game solutions
		#item = menu.Append(MI_SEARCH, "Se&arch Games", "")
		item = menu.Append(MI_NEW, _x("新游戏\tCtrl-N"), _x("新游戏"))
		item = menu.Append(MI_RANDOM, _x("随机新游戏\tCtrl-R"),_x("随机新游戏"))
		item = menu.Append(MI_LOAD, _x("读取存档\tCtrl-L"), _x("读取存档"))
		item = menu.Append(MI_SAVE, _x("保存存档\tCtrl-S"), _x("保存存档"))
		item = menu.Append(MI_EXIT, _x("退出\tCtrl-Q"), _x("退出游戏"))
		mb.Append(menu,_x("游戏"))

		menu = wx.Menu()
		item = menu.Append(MI_UNDO, _x("取消上次移动\tCtrl-Z"), "Undo Move")
		item = menu.Append(MI_REDO, _x("重复上次移动\tCtrl-Y"), "Redo Move")
		item = menu.Append(MI_HINT, _x("显示提示\tCtrl-H"), "Show Hint")
		item = menu.Append(MI_AUTO, _x("自动求解\tCtrl-M"), "Auto Move")
		item = menu.Append(MI_ANI,  _x("动画测试\tCtrl-A"), "Cycle animation type")
		mb.Append(menu,_x("移动"))

		menu = wx.Menu()
		item = menu.Append(MI_ABOUT, _x("关于"), "Introduction")
		mb.Append(menu,_x("帮助"))
		return mb

	def InitMenuBar(self):
		mb = self.GetMenuBarChs()

		self.Bind(wx.EVT_MENU, self.OnSearchGames, id=MI_SEARCH)
		self.Bind(wx.EVT_MENU, self.OnNewGame, id=MI_NEW)
		self.Bind(wx.EVT_MENU, self.OnRandomGame, id=MI_RANDOM)
		self.Bind(wx.EVT_MENU, self.OnLoadGame, id=MI_LOAD)
		self.Bind(wx.EVT_MENU, self.OnClose, id=MI_EXIT)
		self.Bind(wx.EVT_MENU, self.OnSaveGame, id=MI_SAVE)

		self.Bind(wx.EVT_MENU, self.OnUndo, id=MI_UNDO)
		self.Bind(wx.EVT_MENU, self.OnRedo, id=MI_REDO)
		self.Bind(wx.EVT_MENU, self.OnHint, id=MI_HINT)
		self.Bind(wx.EVT_MENU, self.OnAutoMove, id=MI_AUTO)
		self.Bind(wx.EVT_MENU, self.OnAnimation, id=MI_ANI)

		self.Bind(wx.EVT_MENU, self.OnAbout, id=MI_ABOUT)
		self.SetMenuBar(mb)
		return mb

	def ChooseFileName(self,msg="Choose a file",dlgStyle=wx.OPEN):
		dlg = wx.FileDialog(
			self, message=msg,
			defaultDir=os.getcwd(),
			defaultFile="",
			wildcard=NGF_WILDCARD,
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
	def OnSearchGames(self,evt=None):
	   self.board.SearchAllGames()

	def OnUndo(self,evt=None):
		self.board.BackwardMove()
		#self.boardPanel.board.UpdateNumFinishedFlags()
		self.board.RedrawBoard()
	def OnRedo(self,evt=None):
		self.board.ForwardMove()
		#self.boardPanel.board.UpdateNumFinishedFlags()
		self.board.RedrawBoard()
	def OnHint(self,evt=None):
		self.board.ShowHint()
	def OnAutoMove(self,evt=None):
		self.board.SearchAllGames(1)
	def OnAnimation(self,evt=None):self.board.NextAniType()
	def OnNewGame(self,evt=None):
		self.board.InitData()
	def OnRandomGame(self,evt=None):
		random.seed(time.clock())
		for i in [0,1]:
			sc = self.topPanel.spinCtrls[i]
			wx.SpinCtrl.GetMax
			v = random.randrange(sc.GetMin(),sc.GetMax())
			sc.SetValue(v)
		self.topPanel.OnSpin()

	def OnLoadGame(self,evt=None):
		try:
			fileName = self.ChooseFileName("Load Number Game File")
			if fileName:
				self.board.LoadFromFile(fileName)
		except:
			wx.MessageBox('Error in reading file')

	def OnSaveGame(self,evt=None):
		try:
			fileName = self.ChooseFileName("Save Number Game File",wx.SAVE)
			if fileName:
				self.board.SaveToFile(fileName)
		except:
			wx.MessageBox('Error in saving file')

	def OnClose(self,evt=None):
		self.board.StopThreadTimer()
		self.Destroy()

	def OnExit(self,evt=None):
		self.Close(True)

	def OnAbout(self,evt=None):
		import NGAbout
		dlg = NGAbout.NGAboutBox(self)
		dlg.ShowModal()
		dlg.Destroy()

class NGApp(wx.App):

	def __init__(self):
		self.frame = None
		self.window = None
		wx.App.__init__(self, redirect=False)

	def OnInit(self):
		frame = NGFrame(self)
		self.SetTopWindow(frame)
		self.frame = frame
		return True

#----------------------------------------------------------------------------
if __name__ == "__main__":
	app = NGApp()
	try:
		app.MainLoop()
	except:
		app.frame.Close(True)
