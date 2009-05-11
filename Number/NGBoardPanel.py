from NGBoard import *
import os

[
	KEY_B,KEY_F,KEY_D,KEY_I,KEY_J,KEY_K,KEY_L,
	KEY_b,KEY_f,KEY_d,KEY_i,KEY_j,KEY_k,KEY_l,
	KEY_SPACE,KEY_0,KEY_EQUAL,KEY_MINUS,
	KEY_PLUS,KEY_UNDERLINE,KEY_LT,KEY_COMMA,KEY_GT,KEY_PERIOD
] = map(ord,'BFDIJKLbfdijkl 0=-+_<,>.')

class NGBoardPanel(wx.Panel):
	def __init__(self, parent, frame=None):
		wx.Panel.__init__(
			self, parent, -1,
			style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE
		)
		self.frame = frame
		self.board = NGBoard(self)
		self.SetSizeHintsSz(BOARD_SIZE)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)
		self.Bind(wx.EVT_MOUSE_EVENTS,self.OnMouseEvent)

	def OnPaint(self,event):
		pdc = wx.PaintDC(self)
		self.board.RedrawBoard(pdc)
	def OnMouseEvent(self,event):
		x,y = event.GetPosition()
		board = self.board
		oldI = board.iActive
		oldhlFlag = board.hlFlag
		i = GetIByXY(x,y)
		self.SetFocus()

		if i >=-9 :
			cursor = wx.StockCursor(wx.CURSOR_HAND)
			if i<0:
				evtBTN = event.GetButton()
				#right toggle highlight
				hlBit = 1<<(i+9)
				if evtBTN==wx.MOUSE_BTN_RIGHT and event.RightIsDown():
					board.hlFlag = board.hlFlag^hlBit
				#left set highlight
				elif evtBTN==wx.MOUSE_BTN_LEFT:
					board.hlFlag = hlBit
				elif evtBTN==wx.MOUSE_BTN_MIDDLE:
					board.hlFlag = board.hlFlag|hlBit
		else :
			i = IND_OUTSIDE
			cursor = wx.StockCursor(wx.CURSOR_ARROW)
		self.SetCursor(cursor)

		if i != board.iActive or i != oldI or oldhlFlag!=board.hlFlag:
			board.iActive = i
			board.RedrawBoard()

	def OnKeyDown(self,event):
		key = event.GetKeyCode()
		board = self.board
		iActive = board.iActive
		row,col=GetRC(iActive)
		bFixedNum = key > KEY_0 and key <= (KEY_0 + 9)
		if bFixedNum:
			#Not Numpad means it is a fixed number
			key = key - KEY_0 + wx.WXK_NUMPAD0
		if key > wx.WXK_NUMPAD0 and key <= wx.WXK_NUMPAD9:
			if iActive>= 0:
				num = key - wx.WXK_NUMPAD0
				board.AddMove(iActive,num,True,False)#(bFixedNum)
		elif [KEY_d,KEY_D,wx.WXK_NUMPAD0,wx.WXK_BACK].count(key)==1:
			if iActive>= 0:
				board.AddMove(iActive,0,True,True)
			if key==wx.WXK_BACK:
				row,col=GetRC((iActive-1)%81)
		elif key==KEY_i or key==KEY_I:
			row = (row-1)%9
		elif key==KEY_k or key==KEY_K:
			row = (row+1)%9 #self.MoveForWard(1)
		elif key==KEY_j or key==KEY_J:
			col = (col-1)%9
		elif key==KEY_l or key==KEY_L:
			col = (col+1)%9 #self.MoveForWard(1)
		elif key==KEY_SPACE:
			row,col=GetRC((iActive+1)%81)
		elif key==KEY_b or key==KEY_B:
			row,col=GetRC((iActive-1)%81)
		elif key==KEY_COMMA or key==KEY_LT:
			self.board.LShiftHLFlag(1)
		elif key==KEY_PERIOD or key==KEY_GT:
			self.board.LShiftHLFlag(8)
		elif key==wx.WXK_LEFT:
			board.BackwardMove()
		elif key==wx.WXK_RIGHT:
			board.ForwardMove()
		elif [ord('+'),ord('='),ord('-'),ord('_')].count(key)==1:
			intval = self.aniOrAutoTimer.GetInterval()
			if [ord('+'),ord('=')].count(key)==1:
				intval = intval+10
				if intval>200:
					intval=200
			else:
				intval = intval-10
				if intval<40:
					intval=40
			self.aniOrAutoTimer.Stop()
			self.aniOrAutoTimer.Start(intval)
		else: pass
		i = row*9+col
		if i != iActive:
			board.iActive = i
		board.RedrawBoard()

