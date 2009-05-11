# -*- coding: gbk -*-
import wx
import time
import thread
import os
import random
import CardRes
import zipfile
import hashlib
import copy
import traceback
import operator

from Util import *
from Card import *
from CardRender import *
#from SafeThread import *
from array import *

SOLUTIONS_FILE = 'FCSolutions.zip'
#Special shortcut keys
[
	KEY_Q,KEY_W,KEY_E,KEY_R,
	KEY_A,KEY_S,KEY_D,KEY_F,
	KEY_Z,KEY_X,KEY_T,KEY_Y,
	KEY_V,KEY_C,KEY_LA,KEY_LZ
] = map(ord,'QWERASDFZXTYVCaz')

BGD_COLOR = [100,170,90]
#cell index= col<<5+row
MAX_ROW  = (1<<5)-1
#8 pile column, 4 free cell column, 4 target (foundation) column
MAX_COL  = 8
COL_LIST = xrange(MAX_COL)
COL_LIST12 = xrange(12)
ROW_BITS = 0x1F
COL_BITS = 0xE0
COL_IND = [i<<5 for i in COL_LIST]
FREE_IND = COL_IND[0:4]
TARGET_IND = COL_IND[4:8]
COL_IND.extend(COL_IND[:])
TARGET_IND=COL_IND[4:8]
TARGET_1ST_COL = 12
#SC_LIST = range(8,12)
#SC_LIST.extend(xrange(8)) #including 4 free cell column
SC_LIST = range(8)
DC_LIST = range(MAX_COL-1,-1,-1) #including MAX_COL
#DC_LIST.extend([TARGET_1ST_COL, MAX_COL])
ALL_MOVE_LIST = []
#free to pile
for sc in range(8,12):
	for dc in DC_LIST:
		ALL_MOVE_LIST.append([sc,dc])
#pile to pile
for sc in DC_LIST:
	for dc in DC_LIST:
		if sc!=dc:
			ALL_MOVE_LIST.append([sc,dc])
#to foundation
for sc in range(11,-1,-1):
	ALL_MOVE_LIST.append([sc,TARGET_1ST_COL])
#to free
for sc in SC_LIST:
	ALL_MOVE_LIST.append([sc,MAX_COL])
DC_LIST.extend([TARGET_1ST_COL, MAX_COL])
ALL_MOVE_LEN=len(ALL_MOVE_LIST)
_SORTED_COL = range(MAX_COL)
_SORTED_COL12 = range(12)
_ALL_COL = range(MAX_COL*2)

def HashCardTable(cta):
	ctb, ht = range(22), range(MAX_COL)
	for c in COL_LIST:
		i = COL_IND[c]
		for r in xrange(22):
			cn = cta[i]
			#if card is heart or spade, change to diamond or club
			if cn&2:
				ctb[r] = cn^3
			else:
				ctb[r] = cn
			i += 1
		ht[c] = hash(tuple(ctb))
	ht.sort()
	return ht
def GetRCByIC(i):
	return i&ROW_BITS, (i&COL_BITS)>>5
def GetRByIC(i):
	return i&ROW_BITS
def GetCByIC(i):
	return (i&COL_BITS)>>5
def GetICByRC(r,c):
	return (c<<5)|r

#Is index i cell a free cell?
def IsICFree(i):
	#row==0 && col<4
	return (i&ROW_BITS)==0 and (i&COL_BITS)<0x80

#Is row, col a target cell?
def IsRCTarget(row, col):
	return row==0 and col>=4
#Is row, col a free cell?
def IsRCFree(row, col):
	return row==0 and col<4

#Is index i cell a target cell?
def IsICTarget(i):
	#row==0 && col>=4
	return (i&ROW_BITS)==0 and (i&COL_BITS)>=0x80
def IsICEmpty(cardA, i):
	return cardA[i]<=IEMPTY

def Shuffle(gameNo):
	#bFS=True
	cardLeft = 52
	deck = range(52)
	# shuffle cards
	rn = gameNo #gameNo is seed for rand()
	for i in xrange(52):
		#MFC的rand()源码
		rn = rn*214013L + 2531011L
		j = ((rn >> 16) & 0x7fff) % cardLeft
		cardLeft -= 1
		deck[cardLeft],deck[j]=deck[j],deck[cardLeft]
	deck.reverse()
	return deck
class FCGamePanel(wx.Panel):
	def __init__(self, parent, frame=None):
		wx.Panel.__init__(
			self, parent, -1,
			style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE
		)
		self.SetCardResPath('.\\res\\Animals\\')
		self.parent = parent
		self.SetSizeHintsSz((800,600))
		self.frame = frame
		self.focusePen = wx.Pen(wx.GREEN,width=2)
		self.searchThreadActive = self.timerThreadActive = False
		self.DownCursor = wx.CursorFromImage(CardRes.getdaImage())
		#self.timerThread = SafeThread(self.TimerRun)
		#self.searchThread = SafeThread(self.SearchRun)
		self.enableDraw = True
		self.InitData()
		self.timerEnabled = False
		self.StartTimerThread(100)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)
		self.Bind(wx.EVT_MOUSE_EVENTS,self.OnMouseEvent)
		#self.Bind(wx.EVT_CLOSE, self.OnClose)

	def SetCardResPath(self,path):
		cardRender = CardRender(path)
		self.cardRender = cardRender
		self.cwidth,self.cheight = cardRender.width,cardRender.height
		self.spacex,self.spacey  = cardRender.width+10,20
		self.offsetx,self.offsety = 10,10
	def InitData(self):
		self.bFastMode = self.bAutoMove = False
		wx.MilliSleep(10)
		self.gameNo = 0
		self.bApplyMove = True
		self.cardTable = CreateArray(MAX_COL<<5,"i",IEMPTY)
		#self.cards = [Card(i) for i in xrange(58)]
		for c in xrange(4):
			self.cardTable[COL_IND[c+4]] = c-4
		#Info of columns
		#each info contains, num card, max chain
		self.colInfo  = [[0,0]]*MAX_COL
		self.emptyCols = MAX_COL
		self.freePlus1 = 5
		self.iLastMove = self.iMove = 0
		self.moveList = [0]*160
		self.cardIndice = CreateArray(26,"i",0)
		#self.bAutoDockMove = [False]*160
		self.timeTick = 0
		self.SetSelCol(-1)
	def SetSelCol(self, col):
		if col>=0 and col<TARGET_1ST_COL and self.GetCNByCol(col)>IEMPTY:
			self.selCol = col
			self.selColMoveFlag = 0
			if col>=0:
				if col<MAX_COL:
					self.ShowDataInfo(self.GetColState(col),1)
				for c in DC_LIST:
					if self.CanMove(col, c):
						if c<MAX_COL: c = 1<<c
						elif c<TARGET_1ST_COL: c = 0xf00
						else: c = 0xf000
						self.selColMoveFlag |= c
		else:
			self.selCol = -1
			self.Redraw()

	def GetXByC(self,col):
		if col<4:
			return col*self.spacex+self.offsetx
		else:
			return col*self.spacex+self.offsetx*3

	def GetYByR(self,row):
		if row>0:
			return (row-0.5)*self.spacey+self.cheight+self.offsety
		else:
			return self.offsety

	def GetXYByRC(self, row, col):
		return self.GetXByC(col),self.GetYByR(row)

	def GetCByX(self, x):
		for c in COL_LIST:
			x0 = self.GetXByC(c)
			if x>=x0 and x<=x0+self.cwidth:
				return c
		return -1
	def GetRCByXY(self,x,y):
		col = self.GetCByX(x)
		if col >=0:
			n, t = self.colInfo[col]
			istart = COL_IND[col]
			if n==0: n=1
			for r in xrange(n,-1,-1):
				row = istart + r
				y0 = self.GetYByR(r)
				if y>=y0 and y<=y0+self.cheight:
					return r, col
		return -1,-1
	def GetColByXY(self,x,y):
		return self.GetColByRC(self.GetRCByXY(x,y))

	def GetICByCol(self,c):
		if c<MAX_COL:
			return COL_IND[c]+self.colInfo[c][0]
		else:
			return COL_IND[c-MAX_COL]
	def GetRCByCol(self,col):
		if col<MAX_COL:
			n = self.colInfo[col][0]
			if n>0:
				return n, col
			else:
				return -1,-1
		else:
			return 0, col-MAX_COL
	def GetCNByCol(self,col):
		if col<MAX_COL:
			n = self.colInfo[col][0]
			if n>0:
				return self.cardTable[COL_IND[col]+n]
			else:
				return -1
		else:
			return self.cardTable[COL_IND[col-MAX_COL]]
	def GetColByRC(self,rc):
		r,c=rc
		if r==0:
			return c+MAX_COL
		else:return c
	def GetColCardString(self, c):
		n, t = self.colInfo[c]
		ic = COL_IND[c]
		str = ''.join([GetShortNameByI(self.cardTable[ic+i]) for i in xrange(n+1)])
		return str
	def PrintTable(self):
		print self.iMove
		for c in COL_LIST:
			print self.GetColCardString(c)
	def GetColState(self, c):
		''' Column state contains 2 item
			1st item is face value
			2nd item is number of all suit
		'''
		n, t = self.colInfo[c]
		if n:
			ic = COL_IND[c]+1
			ct = self.cardTable
			#face and suit value
			fv, sv, n1 = 0, 0, n - t + 1
			for i in xrange(n1):
				cn = ct[ic+i]
				fv = (fv<<4) + 12 - (cn>>2)
				sv = (sv<<2) + (cn&3)
			ic = ic + n1
			for i in xrange(t-1):
				sv = (sv<<2) + (ct[ic+i]&3)
			return (fv<<4)+13-t, sv
		return 0,0 #1<<32, 0
	def GetGameState(self):
		''' returns gameState, sortedColumns'''
		#game state, smaller is better
		gameState = array('d',xrange(17))
		colStates = map(self.GetColState, COL_LIST)
		#def CMPState(i,j):
		#compare 1st item fv of each state
		#	return cmp(colStates[i][0],colStates[j][0])
		def StateSortKey(i):
			return colStates[i][0]
		_SORTED_COL.sort(key=StateSortKey)
		#_ALL_COL[0:MAX_COL] = _SORTED_COL
		for c in COL_LIST:
			c1 = _SORTED_COL[c]
			fv, sv = colStates[c1]
			gameState[1+c] = fv
			gameState[9+c] = sv
		gameState[0] = max(-8, -self.nCanMove)
		#sortedCol.extend(xrange(MAX_COL,MAX_COL*2))
		return [gameState, _SORTED_COL[:]]
	def GetColValue(self, c):
		ct = self.cardTable
		if c<MAX_COL:
			n, t = self.colInfo[c]
			if n:
				ic = COL_IND[c]+1
				#face and suit value, fv1 is sued for save table state
				fv, fv1, n1 = 0, 0, n - t + 1
				for i in xrange(n1):
					cn = ct[ic+i]
					f = 14 - (cn>>2)
					#each card no cn has 6 bit
					fv1 = (fv1<<6) + cn
					n1mip1 = n1-i+1+t/3.0
					fv = fv + f*n1mip1
					ff = f - ct[COL_IND[(cn&3)+4]]
					if ff<=12:
						if self.CanAutoDockCN(cn):
							fv -= 52*n1mip1
						fv += (3-ff/4)*13*n1mip1
						#fv += 26*(n1-i)
				if n==t:
					fv -= ct[ic]>>2
				ic = ic + n1
				for i in xrange(t-1):
					#the card in chain, only need save last bit.
					fv1 = (fv1<<1) + (ct[ic+i]&1)
				return fv + t, fv1
		else:
			cn = ct[COL_IND[c-MAX_COL]]
			if cn>=0:
				return 28 - (cn>>2), cn
		return -1, -1

	def GetStateValue(self):
		gameState = array('d',COL_LIST12)
		colValues = map(self.GetColValue, COL_LIST12)
		def ValueSortKey(i):
			return colValues[i][1]
		_SORTED_COL12.sort(key=ValueSortKey,reverse=True)
		v = 0
		for c in COL_LIST12:
			c1 = _SORTED_COL12[c]
			gameState[c] = colValues[c1][1]
			v += colValues[c1][0]
		#v smaller is better
		return [gameState, v-min(self.nCanMove,8)*4]
	def AddState(self, gs):
		'return -1 when exist already, otherwise return the slot index'
		sts = self.allStates
		n = self.nStates
		if n==len(sts):
			sts.extend([0]*800)
		while n:
			n -= 1
			if gs==sts[n]: return n
		n = self.nStates
		sts[n], self.nStates = gs, n+1
		return 0
	def StartSearch(self):
		self.bDebug = self.parent.debugCB.IsChecked()
		if not self.searchThreadActive:
			self.bAutoMove = self.bFastMode = True
			self.searchThreadActive = True
			if self.bDebug: self.SearchRun()
			else: thread.start_new_thread(self.SearchRun,())
	def InitSearch(self):
		self.stateList = [0]*len(self.moveList)
		self.allStates = [0]*len(self.moveList)
		self.nStates = 0
		self.SetSelCol(-1)
	def SearchRun(self):
		try:
			bDebug = self.bDebug
			self.InitSearch()
			#methods SearchLoop3,SearchLoop3 are same, 3 is recursive func call while 32 all seach is in one func
			#if the solution is too long, method 3 may meet max recusive call
			#Timer thread will redraw cards at time interval 100mS
			allFunc = [self.SearchLoop1,self.SearchLoop2,self.SearchLoop3]
			func = allFunc[self.parent.scSpin.GetValue()-1]
			if func(): self.GameDone()
			self.Redraw()
			self.searchThreadActive = False
		except Exception, e:
			if bDebug:
				exstr = traceback.format_exc()
				print exstr
				print self
				print self.cardTable,self.moveList
		#self.bAutoMove = self.bFastMode = False

	def StopSearch(self):
		self.bAutoMove = self.bFastMode = False
		#while self.searchThreadActive:
		#	wx.MilliSleep(100)

	def SearchLoop1(self):
		seachedMove = [0]*len(self.allStates)
		iMove, nBreadDepth = 0, 2
		nAllMove = len(ALL_MOVE_LIST)
		canMove = [0]*pow(nAllMove,nBreadDepth)
		nDrawMove = 0
		def MoveKey(item):
			# 1st is game state, 2nd is game value
			return item[2]
		while self.bAutoMove:
			if self.IsGameDone(): return True
			jMove = self.iMove
			iDepth = iCanMove = 0
			iMoveOfBD = [0]*(nBreadDepth+1)
			moveOfBD  = [0]*(nBreadDepth+1)
			jMoveOfBD = [0]*nBreadDepth
			#Find all possible moves in nBreadDepth, bread depth seach
			while iDepth>=0:
				if not self.bAutoMove:
					self.searchThreadActive = False
					return self.IsGameDone()
				sc,dc = ALL_MOVE_LIST[iMoveOfBD[iDepth]]
				iMoveOfBD[iDepth] += 1
				move = self.CanMove(sc,dc)
				if move:
					moveOfBD[iDepth] = move
					jMoveOfBD[iDepth]= self.iMove
					self.AddMove(move,0)
					iDepth += 1
					self.ShowDataInfo([self.iMove,self.nStates],2)
					if self.IsGameDone():
						canMove[0],iCanMove = [moveOfBD[:iDepth],0,0],1
						#backward to orignal
						while self.iMove>jMoveOfBD[0]:
							self.BackwardMove()
						break
					if iDepth==nBreadDepth or iDepth==1:
						gs, v = self.GetStateValue()
						if not self.AddState(gs): #game state not exists
							canMove[iCanMove],iCanMove=[moveOfBD[:iDepth],gs,v],iCanMove+1
					if iDepth==nBreadDepth:
						iMoveOfBD[iDepth] = nAllMove
					else:
						iMoveOfBD[iDepth] = 0
				while iMoveOfBD[iDepth]>=nAllMove:
					#backward to previous step
					iDepth -= 1
					if iDepth<0: break
					while self.iMove>jMoveOfBD[iDepth]:
						self.BackwardMove()
			if iCanMove==0:
				while iMove>0:
					#Backward last move,Parent Child move seperation
					iMove-=1; jMove = seachedMove[iMove]
					#beccause there may be autodock move
					#need seperation to record the parent iMove in moveList
					while self.iMove>jMove:
						self.BackwardMove()
						self.ShowDataInfo([self.iMove,self.nStates],2)
					iMove-=1; move = seachedMove[iMove-1]
					if not isinstance(move,int):#Another child move
						seachedMove[iMove] = jMove
						iMove = iMove+1
						break
				if iMove<=0: return False
			else:
				iMove += iCanMove
				if len(seachedMove)<=iMove:
					seachedMove.extend([0]*800)
				#sort moves
				sortedCanMove = sorted(canMove[0:iCanMove],key=MoveKey,reverse=True)[:]
				seachedMove[iMove-iCanMove:iMove] = map(operator.itemgetter(0), sortedCanMove)
				move = seachedMove[iMove-1]
				seachedMove[iMove] = self.iMove; iMove += 1
			for smove in move:
				self.AddMove(smove,0)
				nDrawMove+=1
				if nDrawMove==40: self.Redraw();nDrawMove=0
			self.ShowDataInfo([self.iMove,self.nStates],2)
		self.searchThreadActive = False
		return self.IsGameDone()
	def SearchLoop2(self):
		canMove = [0]*len(ALL_MOVE_LIST)
		seachedMove = [0]*len(self.allStates)
		nDrawMove = iMove = 0
		def MoveKey(item):
			# 1st is game state, 2nd is game value
			return item[2]

		while self.bAutoMove and not self.IsGameDone():
			iCanMove = 0 #Find all possible moves
			jMove = self.iMove
			for sc,dc in ALL_MOVE_LIST:
				move = self.CanMove(sc, dc)
				if move:
					self.AddMove(move,0)
					#self.ApplyMove(move)
					#gs, v = self.GetGameState()
					gs, v = self.GetStateValue()
					while self.iMove>jMove:
						self.BackwardMove()
					#self.ApplyMove(move,True)
					if not self.AddState(gs): #game state not exists
						canMove[iCanMove],iCanMove=[move,gs,v],iCanMove+1
			if iCanMove==0:
				while iMove>0:
					#Backward last move,Parent Child move seperation
					iMove-=1; jMove = seachedMove[iMove]
					#beccause there may be autodock move
					#need seperation to record the parent iMove in moveList
					while self.iMove>jMove:
						self.BackwardMove()
						self.ShowDataInfo([self.iMove,self.nStates],2)
					iMove-=1; move = seachedMove[iMove-1]
					if not isinstance(move,int):#Another child move
						seachedMove[iMove] = jMove
						iMove = iMove+1
						break
				if iMove<=0: return False
			else:
				iMove += iCanMove
				if len(seachedMove)<=iMove:
					seachedMove.extend([0]*800)
				#sort moves
				sortedCanMove = sorted(canMove[0:iCanMove],key=MoveKey,reverse=True)[:]
				seachedMove[iMove-iCanMove:iMove] = map(operator.itemgetter(0), sortedCanMove)
				if self.bDebug:
					pass
					#self.PrintTable()
					#print seachedMove[iMove-iCanMove:iMove]
					#print map(MoveKey, sortedCanMove)
				move = seachedMove[iMove-1]
				#for item in sorted(canMove[0:iCanMove],key=MoveKey,reverse=True):
				#	seachedMove[iMove] = item[0]; iMove += 1
				#move = item[0]
				#Add child and parent move seperation.
				seachedMove[iMove] = self.iMove; iMove += 1
			self.AddMove(move,0)
			nDrawMove+=1
			if nDrawMove==40: self.Redraw();nDrawMove=0
        	self.ShowDataInfo([self.iMove,self.nStates],2)
		return self.IsGameDone()
	def SearchLoop3(self):
		canMove = [0]*len(ALL_MOVE_LIST)
		seachedMove = [0]*len(self.allStates)
		fcl, iMove = range(8,12), 0
		ct = self.cardTable
		nDrawMove = 0
		def FreeColSortKey(i):
			return ct[COL_IND[i]]
		while self.bAutoMove and not self.IsGameDone():
			gs, cl = self.GetGameState()
			fcl.sort(key=FreeColSortKey,reverse=True)
			cl.extend(fcl); cl.extend(xrange(12,16))
			iCanMove = 0
			if not self.AddState(gs): #game state not exists
				for sc, dc in ALL_MOVE_LIST:  #Find all possible moves
					sc1, dc1 = cl[sc], cl[dc]
					move = self.CanMove(sc1, dc1)
					if move:
						iCanMove-=1; canMove[iCanMove] = move
			if iCanMove==0:
				while iMove>0:
					#Backward last move
					iMove-=1; jMove = seachedMove[iMove]
					while self.iMove>jMove:
						self.BackwardMove()
					iMove-=1; move = seachedMove[iMove-1]
					if not isinstance(move,int):#Another child move
						seachedMove[iMove] = jMove
						iMove = iMove+1
						break
				if iMove<=0: return False
			else:
				iMove -= iCanMove #iCanMove is negative
				if len(seachedMove)<=iMove:
					seachedMove.extend([0]*800)
				seachedMove[iMove+iCanMove:iMove] = canMove[iCanMove:]
				#Add child and parent move seperation.
				seachedMove[iMove] = self.iMove
				move, iMove = canMove[-1], iMove+1
			self.AddMove(move,0)
			nDrawMove+=1
			if nDrawMove==40: self.Redraw();nDrawMove=0
			self.ShowDataInfo([self.iMove,self.nStates],2)
		return self.IsGameDone()
	def SearchLoop32(self):
		gs, cl = self.GetGameState()
		iMove = self.iMove
		if self.AddState(gs):
			self.ShowDataInfo([iMove,self.nStates,1],2)
			return False
		def FreeColSortKey(i):
			return self.cardTable[COL_IND[i]]
		fcl = range(8,12)
		fcl.sort(key=FreeColSortKey,reverse=True)
		cl.extend(fcl)
		cl.extend(xrange(12,16))
		for [sc,dc] in ALL_MOVE_LIST:
			if not self.bAutoMove: return False
			sc1, dc1 = cl[sc], cl[dc]
			move = self.CanMove(sc1, dc1)
			if move:
				self.ShowDataInfo([iMove,self.nStates],2)
				self.AddMove(move,0)
				if self.IsGameDone():
					return True
				if self.SearchLoop32():
					return True
				else:
					#backward
					if not self.bAutoMove: return False
					while self.iMove>iMove:
						self.BackwardMove()
		return False

	def CanMove(self,sc,dc):
		if sc==dc: return 0
		n, ct = 0, self.cardTable
		if sc<MAX_COL: #src is normal column
			sn, st = self.colInfo[sc]
			#All pile in chain and first is K, move to other pile is redundant
			if sn==0: return 0 #or sn==st and ct[COL_IND[sc]+1]>=48 and dc<MAX_COL
			ics = COL_IND[sc]+sn
		else:
			ics = COL_IND[sc-MAX_COL]
			if sc<TARGET_1ST_COL and dc>=MAX_COL and dc<TARGET_1ST_COL or ct[ics]<0:
				return 0
			sn, st = 2, 1
		if dc<MAX_COL: #dest
			dn, dt = self.colInfo[dc]
			icd = COL_IND[dc]+dn
			canMoveN = self.nCanMove
			if dn==0:
				#if dest col is empty, canMoveN need >> 1
				n = min(canMoveN>>1,st)
				if n and n==sn: # Move entire column to a empty column is not allowed
					return 0
			else:
				cnd = ct[icd]
				for it in xrange(st):
					cns = ct[ics-it]
					if IsNextFCFace(cns,cnd):
						if it < canMoveN:
							n = it+1
							break
		else:
			if dc<TARGET_1ST_COL:#Free cell
				#Find 1st empty free cell
				icd = Get1stV(ct,IEMPTY,FREE_IND)
				if icd>=0:
					n, dc = 1, (icd>>5)+MAX_COL
				else: dc=-1
			else: #Target
				cns = ct[ics]
				dc = cns%4
				icd, dc = TARGET_IND[dc], dc+TARGET_1ST_COL
				if IsNextFace(ct[icd],cns): n=1
			icd -= 1
		if n>0:
			return sc,dc,n
		else:
			return 0
	def ApplyMove(self,(sc,dc,n),bBackWard=False):
		if bBackWard:
			sc,dc=dc,sc
		ics = self.GetICByCol(sc)
		icd = self.GetICByCol(dc)
		if dc>=MAX_COL: icd-=1
		ct = self.cardTable
		#Move cards && Update col Info
		if sc<TARGET_1ST_COL:
			if sc<MAX_COL:
				for i in xrange(n):
					ct[icd+n-i],ct[ics-i]=ct[ics-i],IEMPTY
				sn, st =self.colInfo[sc]
				if sn==n:
					self.emptyCols+=1
				if st<=n:
					self.colInfo[sc] = self.GetColInfo(sc)
				else:
					self.colInfo[sc] = [sn-n,st-n]
			else:
				ct[icd+1],ct[ics]=ct[ics],IEMPTY
				self.freePlus1+=1
		else:
			ct[icd+1],ct[ics]=ct[ics],ct[ics]-4
		if dc<MAX_COL:
			dn, dt =self.colInfo[dc]
			if dn==0:
				self.emptyCols-=1
			if bBackWard and dn>0:
				self.colInfo[dc] = self.GetColInfo(dc)
			else:
				self.colInfo[dc] = [dn+n, dt+n]
		elif dc<TARGET_1ST_COL:#Free Cell
			self.freePlus1-=1
		if self.emptyCols<0:
			print self.colInfo,self.freePlus1
			self.UpdateCountInfo()
		self.nCanMove = self.freePlus1<<self.emptyCols
		#self.PrintTable()

	def GetColInfo(self, c):
		#Get column info
		#number of cards, max chain number
		ct = self.cardTable
		i = COL_IND[c]+1
		#col info
		n, t = 0, 0
		for r in xrange(MAX_ROW):
			j = i + r
			cn1 = ct[j]
			if cn1==IEMPTY:
				break
			if r==0:
				n = t = 1
			else:
				if IsNextFCFace(cn1,cn2):
					t += 1
				else:
					t = 1
				n += 1
			cn2 = cn1
		return [n, t]
	def UpdateCountInfo(self):
		ne, nf = 0, 1
		for c in COL_LIST:
			if self.colInfo[c][0]==0:
				ne+=1
			if c<4 and self.cardTable[COL_IND[c]]<=IEMPTY:
				nf+=1
		self.emptyCols, self.freePlus1 = ne, nf
		self.nCanMove = self.freePlus1<<self.emptyCols
	def UpdateAllInfo(self):
		self.colInfo = [self.GetColInfo(c) for c in COL_LIST]
		self.UpdateCountInfo()

	def ApplyMoveAndRedraw(self, move, timeDelay=20):
		self.ApplyMove(move)
		wx.MilliSleep(timeDelay)
		self.Redraw()
	#Need make sure it can work before call it
	def ChainCard(self, (scol, dcol, n)):
		if n > self.freePlus1:
			for c in COL_LIST:
				if c!=dcol and self.colInfo[c][0]==0:
					self.ChainCard((scol,c,n/2))
					self.ChainCard((scol,dcol,n-n/2))
					self.ChainCard((c,dcol,n/2))
					return
		else:
			if self.bAutoMove:
				self.ApplyMove((scol,dcol,n))
			elif self.bFastMode:
				self.ApplyMoveAndRedraw((scol,dcol,n))
			else:
				ct = self.cardTable
				icd = range(4)
				for c in xrange(n-1): #move to free
					icd[c] = (Get1stV(ct,IEMPTY,FREE_IND)>>5)+MAX_COL
					self.ApplyMove((scol,icd[c],1))
				self.ApplyMoveAndRedraw((scol,dcol,1))
				for c in xrange(n-1): #move from free to dest
					self.ApplyMoveAndRedraw((icd[n-2-c],dcol,1))
	#If method name has Try in it, it will check if it is feasible.
	def AddMove(self, move, timeDelay=50):
		if self.bFastMode or move[2]==1:
			timeDelay = min(1,timeDelay)
			self.ApplyMove(move)
		else:
			self.ChainCard(move)
		iMove = self.iMove
		if iMove==len(self.moveList):
			self.moveList.extend([0]*160)
			#self.bAutoDockMove.extend([0]*160)
		self.moveList[iMove] = move
		self.iMove = self.iLastMove = iMove+1
		if timeDelay>0:
			self.ShowDataInfo(self.iMove,2)
			if not self.bAutoMove:
				wx.MilliSleep(timeDelay)
				self.Redraw()
		self.TryAutoDock(timeDelay)
	def CanAutoDockCN(self, cn):
		if cn>=0:
			ct = self.cardTable
			suit = cn%4
			ict = TARGET_IND[suit]
			cnt = ct[ict]
			if cnt+4!=cn: return 0
			cn0 = cn-suit-4
			cn1,cn2,cn3 = ct[TARGET_IND[suit^1]],ct[TARGET_IND[suit^2]],ct[TARGET_IND[3-suit]]
			cn12min = min(cn1,cn2)
			#this card has smaller other color, we need check
			if cn12min >= cn0 or min(cn12min,cn3) >= cn0-4:
				return TARGET_1ST_COL+suit
		return 0
	def CanAutoDockCol(self,col):
		ct = self.cardTable
		if col<MAX_COL:
			n = self.colInfo[col][0]
			if n>0:
				cn = ct[COL_IND[col]+n]
			else: return 0
		else:
			cn = ct[COL_IND[col-MAX_COL]]
		dcol = self.CanAutoDockCN(cn)
		if dcol:
			return [col,dcol,1]
		return 0
	def TryAutoDock(self,timeDelay = 20):
		for col in xrange(TARGET_1ST_COL):
			move = self.CanAutoDockCol(col)
			if move:
				#self.bAutoDockMove[self.iMove] = True
				#if self.bFastMode:
				#	self.AddMove(move,1)
				#else:
				self.AddMove(move,timeDelay)
	def ShowDataInfo(self,data,idx):
		if not isinstance(data,str):
			data = repr(data)
		self.frame.ShowMessage(data,idx)
	def OnBackward(self):
		self.SetSelCol(-1)
		self.BackwardMove()
		self.ShowDataInfo(self.iMove,2)
		self.Redraw()
	def OnForward(self):
		self.SetSelCol(-1)
		self.ForwardMove()
		self.ShowDataInfo(self.iMove,2)
		self.Redraw()
	def BackwardMove(self):
		if self.iMove>0:
			self.iMove -= 1
			move = self.moveList[self.iMove]
			self.ApplyMove(move,True)
			if not self.bAutoMove:
				self.Redraw()
	def ForwardMove(self):
		if self.iMove<self.iLastMove:
			move = self.moveList[self.iMove]
			self.ApplyMove(move)
			self.iMove += 1
			self.Redraw()
	def IsGameDone(self):
		#ct = self.cardTable
		#for col in xrange(4):
		#	cn = ct[TARGET_IND[col]]
		#	if cn<48: #Club K card # is 48
		#		return False
		#return True
		return self.emptyCols==8 and self.freePlus1==5

	def LoadGame(self,gn):
		if gn<0:
			random.seed(time.clock())
			gn = random.randrange(1,100000)
		cardDeck = Shuffle(gn)
		self.InitData()
		for i in xrange(52):
			row, col = i/MAX_COL+1, i%MAX_COL
			self.cardTable[COL_IND[col]+row] = cardDeck[i]
		self.UpdateAllInfo()
		self.gameNo = gn
		self.UpdateGameNoTitle()
		self.Redraw()
	def UpdateGameNoTitle(self, gn=None):
		if gn is None: gn = self.gameNo
		self.parent.gnSpin.SetValue(gn)
		self.frame.SetTitle('FreeCell Game # %d' % gn)
		self.SetFocus()
	def SaveToFile(self, fileName):
		file = open(fileName,"w")
		data = repr(
			[
				self.cardTable,
				self.gameNo,
				self.iMove,
				self.iLastMove,
				self.moveList
			]
		)
		file.write(data)
		file.close()
	def LoadFromData(self,data):
		self.InitData()
		[
			self.cardTable,
			self.gameNo,
			self.iMove,
			self.iLastMove,
			self.moveList
		] = eval(data)
		self.UpdateAllInfo()
		self.UpdateGameNoTitle()
		for i in xrange(self.iLastMove):
			move = self.moveList[i]
			if len(move)==5:
				scol,srow,dcol,drow,n = move
				sc = self.GetColByRC((srow,scol))
				dc = self.GetColByRC((drow,dcol))
				if n>1: n-=1
				self.moveList[i] = [sc,dc,n]
		self.Redraw()
	def LoadFromFile(self, fileName):
		try:
			data = open(fileName,"r").read()
			self.LoadFromData(data)
		except:pass
	def GetSolutionName(self, gn=None):
		if gn is None:
			gn = self.gameNo
		return '%03d/%03d' % ((gn>>10)&1023, gn&1023)

	def NextUnsolvedGame(self,gn):
		gn = gn + 1
		try:
			zf = zipfile.ZipFile(SOLUTIONS_FILE,'r')
			namelist = zf.namelist()
			while gn<100000:
				name = self.GetSolutionName(gn)
				if not (name in namelist):
					break
				gn += 1
		finally:
			self.LoadGame(gn)

	def LoadSolution(self):
		try:
			zf = zipfile.ZipFile(SOLUTIONS_FILE,'r')
			data = zf.read(self.GetSolutionName())
			zf.close()
			self.LoadFromData(data)
		except:
			pass

	def SaveSolution(self):
		if os.path.isfile(SOLUTIONS_FILE):
			mode = 'a'
		else:
			mode = 'w'
		zf = zipfile.ZipFile(SOLUTIONS_FILE,mode,compression=zipfile.ZIP_DEFLATED)
		fname = self.GetSolutionName()
		if zf.namelist().count(fname):
			dlg = wx.MessageDialog(self, 'Still Save?', 'Solution Exists!', style=wx.YES_NO)
			#dlg.CenterOnParent()
			if dlg.ShowModal()!=wx.ID_YES:
				fname = 0
			dlg.Destroy()
		if fname:
			zf.writestr(fname, repr([
				self.cardTable,
				self.gameNo,
				self.iMove,
				self.iLastMove,
				self.moveList[:self.iLastMove] #only saved valid moves
			]))
		zf.close()
	def DrawAllCards(self,dc):
		render = self.cardRender
		dc.SetBrush(GetBrush(BGD_COLOR))
		#dc.SetBrush(wx.GREEN_BRUSH)
		windowSize  = self.GetSizeTuple()
		dc.DrawRectangle(0, 0,  windowSize[0], windowSize[1])
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		dc.SetPen(wx.RED_PEN)
		for col in COL_LIST:
			#Free cell or Target cell rects
			row, ic = 0, COL_IND[col]
			while True:
				x,y = self.GetXYByRC(row,col)
				cardNo = self.cardTable[ic + row]
				if cardNo <= IEMPTY:
					if row == 0:
						dc.DrawRoundedRectangle(x,y,render.width,render.height,3)
					else:
						break
				else:
					#if (row,col)==self.selCol and (self.timeTick&4):
					#	dc.DrawRoundedRectangle(x-2,y-2,render.width+4,render.height+4,3)
					render.DrawCardCN(dc,x,y,cardNo)
				row = row + 1
	def GetBufferedDC(self,pdc):
		try:
			if pdc is None:
				pdc = wx.ClientDC(self)
			dc = wx.BufferedDC(pdc)
		except:
			dc = pdc
		return dc
	def DrawFocusRect(self):
		if self.selCol>=0:
			row,col = self.GetRCByCol(self.selCol)
			if row>=0:
				render = self.cardRender
				dc = wx.ClientDC(self)
				dc.SetBrush(wx.TRANSPARENT_BRUSH)
				dc.SetPen(self.focusePen)
				dc.SetLogicalFunction(wx.XOR)
				x,y = self.GetXYByRC(row,col)
				dc.DrawRoundedRectangle(x-2,y-2,render.width+4,render.height+4,3)
				dc.SetPen(wx.GREEN_PEN)
				#dc.DrawRoundedRectangle(x-3,y-3,render.width+5,render.height+5,3)
	def Redraw(self,pdc = None):
		if self.enableDraw:
			self.enableDraw = False
			try:
				if pdc is None:
					pdc = wx.ClientDC(self)
				dc = wx.BufferedDC(pdc)
				self.DrawAllCards(dc)
			finally:
				self.enableDraw = True
	def OnExit(self,evt=None):
		busy = wx.BusyInfo("One moment please, waiting for threads to die...")
		wx.Yield()
		del self.focusePen
		self.OnKeyDown('e')
		self.StopTimerThread() #
		self.StopSearch()
		wx.MilliSleep(max(200,self.timerInterval+100))
		#self.Destroy()
	def OnPaint(self,event):
		pdc = wx.PaintDC(self)
		self.Redraw(pdc)
	def GameDone(self):
		self.Redraw()
		self.SaveSolution()
		dlg = wx.MessageDialog(self, 'Next Game?', 'Good Job!', style=wx.YES_NO)
		#dlg.CenterOnParent()
		if dlg.ShowModal()==wx.ID_YES:
			self.LoadGame(self.gameNo+1)
		dlg.Destroy()

	def GetFastMoveMode(self):
		self.bFastMode = self.parent.fastModeCB.IsChecked()

	def OnMouseEvent(self,event):
		self.SetFocus()
		if self.bAutoMove: return
		x,y = event.GetPosition()
		r,c=self.GetRCByXY(x,y)
		if c >= 0:
			cn = self.cardTable[COL_IND[c]+r]
			if cn>IEMPTY:
				self.ShowDataInfo(GetNameByI(cn),0)
				#self.frame.ShowMessage(GetNameByI(cn))
		col = self.GetColByRC((r,c))
		sc = self.selCol
		if sc == -1 and col>=TARGET_1ST_COL: #Target
			col = -1
		if col>=0:
			if sc == -1:
				self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
			else:
				if self.selColMoveFlag & (1<<col):
					self.SetCursor(self.DownCursor)
				else:
					self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
			dc = -1
			evtBTN = event.GetButton()
			if event.ButtonDClick(wx.MOUSE_BTN_LEFT):
				if col<TARGET_1ST_COL:
					sc, dc = col, MAX_COL
			elif evtBTN==wx.MOUSE_BTN_RIGHT and event.RightIsDown():
				sc,dc = col,TARGET_1ST_COL
			elif evtBTN==wx.MOUSE_BTN_LEFT and event.LeftIsDown():
				dc = col
			if dc >= 0:
				if sc!=-1:
					move = self.CanMove(sc,dc)
					if move:
						self.GetFastMoveMode()
						self.SetSelCol(-1)
						self.AddMove(move)
						if self.IsGameDone():
							self.GameDone()
					else:
						if dc<TARGET_1ST_COL:
							self.SetSelCol(col)
						else:self.SetSelCol(-1)
						self.Redraw()
				else:
					self.SetSelCol(col)
			#self.Redraw()
		else:
			self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
		#For Debug
		#message = "%3d,%3d, R:%2d, C:%2d F:%d,E:%d N:%d,T%d" % \
		#	(x,y,row,col,self.freePlus1-1,self.emptyCols,self.colInfo[col][0],self.colInfo[col][1])

	def OnKeyDown(self,event):
		if isinstance(event,int):
			key = event
		elif isinstance(event,str):
			key = ord(event)
		else:
			key = event.GetKeyCode()
		if key<=KEY_LZ and key>=KEY_LA:
			key = key + KEY_A - KEY_LA
		if key==KEY_A:
			self.SetSelCol(-1)
			while self.iMove:
				self.BackwardMove()
			self.Redraw()
		elif key==KEY_F:
			self.SetSelCol(-1)
			while self.iMove<self.iLastMove:
				self.ForwardMove()
			self.Redraw()
		elif key==KEY_S: self.OnBackward()
		elif key==KEY_D: self.OnForward()
		elif key==KEY_E: self.SaveToFile('QuickSave.fcf')
		elif key==KEY_R: self.LoadFromFile('QuickSave.fcf')
		elif key==KEY_Q: self.LoadGame(self.gameNo+1)
		elif key==KEY_W: self.LoadGame(self.gameNo-1)
		elif key==KEY_Z: self.SaveSolution()
		elif key==KEY_X: self.LoadSolution()
		elif key==KEY_T: self.StartSearch()
		elif key==KEY_Y: self.StopSearch()
		elif key==KEY_V: self.LoadGame(self.gameNo)
		elif key==KEY_C: self.NextUnsolvedGame(self.gameNo)
		else: return

	def StartTimerThread(self,timeInterval):
		self.timerInterval = timeInterval
		if not self.timerThreadActive:
			self.timerThreadActive = True
			self.timeTick = 0
			self.timerEnabled = True
			self.timerThread = thread.start_new_thread(self.RunTimerThread,())

	def StopTimerThread(self):
		self.timerEnabled = False
		while self.timerThreadActive:
			wx.MilliSleep(self.timerInterval+10)

	def RunTimerThread(self):
		self.timerThreadActive = True
		try:
			while self.timerEnabled:
				wx.MilliSleep(self.timerInterval)
				#print 'Timer'
				self.timeTick=(self.timeTick+1)&0xff
				tick = self.timeTick&32
				if tick == 16 and self.bAutoMove:
					self.Redraw()
				if tick&15 == 0:
					self.DrawFocusRect()
			self.timerThreadActive = False
		except: pass
