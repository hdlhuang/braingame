# -*- coding: gbk -*-
import wx
import os
import random
import time
import FCGame
import FCControlPanel
import CardRes
import ctypes

def _x(str):
	return unicode(str,"gbk")

FCF_WILDCARD = "FreeCell Game File (*.fcf)|*.fcf|All files (*.*)|*.*"

[
	TB_NEW,TB_LOAD,TB_SAVE,TB_UNDO,TB_REDO,TB_HINT,TB_AUTO,TB_HELP
] = [wx.NewId() for x in range(8)]
[
	MI_SEARCH,MI_RANDOM,MI_NEW,MI_LOAD,MI_SAVE,MI_OPTIONS,MI_EXIT,
	MI_UNDO,MI_REDO,MI_HINT,MI_AUTO,MI_HELP,
	MI_ABOUT,MI_ANI
] = [wx.NewId() for x in range(14)]

class FCFrame(wx.Frame):
	MENUS = [
		["&Game",
			["Exit Game", "E&xit\tCtrl-Q"],
			["New Game", "&New\tCtrl-N"],
			["Load Game", "&Load\tCtrl-L"],
			["Save Game", "&Save\tCtrl-L"]
		]
	]

	def __init__(self, ngApp, parent = None, id=wx.ID_ANY, title="FreeCell Game", pos=wx.DefaultPosition,
				 size=(720,600), style=wx.DEFAULT_FRAME_STYLE):

		wx.Frame.__init__(self, parent, id, title, pos, size, style)
		self.ngApp = ngApp
		win = FCControlPanel.FCControlPanel(self, self)
		self.topPanel = win
		self.gamePanel = win.gamePanel
		self.SetIcon(CardRes.getfcIcon())

		self.InitMenuBar()
		self.statusBar = self.CreateStatusBar(3, wx.ST_SIZEGRIP)
		self.statusBar.SetStatusWidths([-5, -3,-3])
		self.statusBar.SetStatusText("HL @ 2009", 1)
		self.statusBar.SetStatusText("Welcome to FreeCell Game!", 2)
		#self.SetSize(FCBoard.BOARD_SIZE)
		#self.Center()
		self.Bind(wx.EVT_CLOSE, self.topPanel.OnExit)
		self.Show(True)
		self.SetMinSize(self.GetSize())
		self.SetMaxSize(self.GetSize())

	def GetMenuBarEng(self):
		mb = wx.MenuBar()
		menu = wx.Menu()
		#search games is only used to generate game solutions
		#item = menu.Append(MI_SEARCH, "Se&arch Games", "")
		#item = menu.Append(MI_NEW, "&New\tCtrl-N", "New Game")
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
		#item = menu.Append(MI_NEW, _x("新游戏\tCtrl-N"), _x("新游戏"))
		item = menu.Append(MI_RANDOM, _x("随机新游戏\tCtrl-R"),_x("随机新游戏"))
		item = menu.Append(MI_LOAD, _x("读取存档\tCtrl-L"), _x("读取存档"))
		item = menu.Append(MI_SAVE, _x("保存存档\tCtrl-S"), _x("保存存档"))
		item = menu.Append(MI_OPTIONS, _x("设置"), _x("游戏设置"))

		item = menu.Append(MI_EXIT, _x("退出\tCtrl-Q"), _x("退出游戏"))
		mb.Append(menu,_x("游戏"))

		menu = wx.Menu()
		item = menu.Append(MI_UNDO, _x("取消上次移动\tCtrl-Z"), "Undo Move")
		item = menu.Append(MI_REDO, _x("重复上次移动\tCtrl-Y"), "Redo Move")
		item = menu.Append(MI_HINT, _x("显示提示\tCtrl-H"), "Show Hint")
		#item = menu.Append(MI_AUTO, _x("自动求解\tCtrl-M"), "Auto Move")
		mb.Append(menu,_x("移动"))

		menu = wx.Menu()
		item = menu.Append(MI_ABOUT, _x("关于"), "Introduction")
		mb.Append(menu,_x("帮助"))
		return mb
	def ShowMessage(self,msg,idx=0):
		self.statusBar.SetStatusText(msg,idx)
	def InitMenuBar(self):
		mb = self.GetMenuBarChs()

		#self.Bind(wx.EVT_MENU, self.OnSearchGames, id=MI_SEARCH)
		#self.Bind(wx.EVT_MENU, self.OnNewGame, id=MI_NEW)
		self.Bind(wx.EVT_MENU, self.OnRandomGame, id=MI_RANDOM)
		self.Bind(wx.EVT_MENU, self.topPanel.OnLoadGame, id=MI_LOAD)
		self.Bind(wx.EVT_MENU, self.topPanel.OnExit, id=MI_EXIT)
		self.Bind(wx.EVT_MENU, self.topPanel.OnSaveGame, id=MI_SAVE)

		self.Bind(wx.EVT_MENU, self.topPanel.OnUndo, id=MI_UNDO)
		self.Bind(wx.EVT_MENU, self.topPanel.OnRedo, id=MI_REDO)
		#self.Bind(wx.EVT_MENU, self.topPanel.OnHint, id=MI_HINT)
		#self.Bind(wx.EVT_MENU, self.topPanel.OnStartAuto, id=MI_AUTO)

		self.Bind(wx.EVT_MENU, self.topPanel.OnAbout, id=MI_ABOUT)
		self.SetMenuBar(mb)
		return mb

	def OnHint(self,evt=None):
		return 0
		self.gamePanel.ShowHint()

	def OnRandomGame(self,evt=None):
		self.gamePanel.LoadGame(-1)

class FCApp(wx.App):
	def __init__(self):
		self.frame = None
		self.window = None
		wx.App.__init__(self, redirect=False)

	def OnInit(self):
		frame = FCFrame(self)
		self.SetTopWindow(frame)
		self.frame = frame
		return True

#----------------------------------------------------------------------------
if __name__ == "__main__":
	app = FCApp()
	try:
		app.MainLoop()
	except:
		app.frame.Close(True)
