import wx
import array
import copy
import time
import pickle
import thread
import os
import random
import NGRes
ALL_NUM_BITS=0x1ff
#Index increments based on first element in a row,column or region
ROW_INC_IND = range(9)
COL_INC_IND = range(0,81,9)
REG_INC_IND = [
	 0, 1, 2,
	 9,10,11,
	18,19,20
]
#Full board indeice
FULL_IND = range(0,81)
#Row Column boundary
BOUNDARY = wx.Rect(0,0,9,9)
#First index of all regions
REG_1ST_IND = [
	 0, 3, 6,
	27,30,33,
	54,57,60
]

#Square size
REG_SPACE   = 3
SQ_SIZE     = 26
SQ_RECT     = wx.Rect(0,0,SQ_SIZE-2,SQ_SIZE-2)
SQ_OFFSET   = wx.Point(SQ_SIZE*3/2,SQ_SIZE*4/2)

BOARD_SIZE    = wx.Size(SQ_SIZE*23/2,SQ_SIZE*13)

#The whole board row & column & region are from 0 to 8
#Row -1 is used for highlighting toggle buttons

IND_OUTSIDE = -0xff

'''
The bmp source is Numbers.PNG,
Square Number bits 0:8 is used to get source bmp position.
Bits 0:3 are for number, used to get y position
Bits 4:7 are for bitmap type index, used to get x position

Bit 8 indicates if the square is a fixed number, if fixed, user can not enter number
'''
BITMAP_MASK = 0x0f
HIGHL_BIT   = 0x10
FIXED_BIT   = 0x20
LOADED_BIT   = 0x40
ACTIVE_BIT   = 0x80
NUMBER_MASK = 0x0f

'''
Animation (type,steps,srcgn,option)
type:
 0: highlight row one by one
 1: highlight column one by one
 2: highlight region one by one
 3: highlight number one by one
 4: highlight elements in one row
 5: highlight elements in one column
 6: highlight elements in one region
 7: highlight elements num
steps:
 if ANI_CYCLE_BIT is not set in option and steps decrease to 0, stop
srcgn:
 the sub index in row, column, region, number
option:
 can be flicker or cycle.
'''
[ANI_TYPE_ROWS,ANI_TYPE_COLS,ANI_TYPE_REGS,ANI_TYPE_NUMS,
ANI_TYPE_ROW,ANI_TYPE_COL,ANI_TYPE_REG,ANI_TYPE_NUM,ANI_TYPE_NONE] = range(9)
ANIMATION_NONE=(ANI_TYPE_NONE,0,0,0)
ANI_FLICK_BIT = 0x1
ANI_CYCLE_BIT = 0x2
#type,step,rcgn,flicker
MOVE_NONE = [10,-1,0,0]

def RandomRange(start,stop=None,seed=None):
	if seed is not None:
		random.seed(seed)
	if stop is None:
		start,stop = 0,start
	indices = range(start,stop)
	n = stop-start-1
	while n>0:
		i = random.randrange(n)
		#swap i,n
		indices[i],indices[n],n = indices[n],indices[i],n-1
	return indices

def CompressRCGArray(numA,iList):
	numB = [numA[i] for i in iList]
	sortedB = range(1,10)
	i, n = 8, 0
	while i>0:
		num = numB[i]
		ind = sortedB.index(num)
		sortedB.remove(num)
		n = n*(i+1)+ind
		i -= 1
	return n

def DeCompressRCGArray(n):
	iList = []
	i = 2
	while i<10:
		n,ind=n/i,n%i
		iList.append(ind)
		i = i+1
	sortedB = range(1,10)
	numA = range(1,10)
	i = 7
	while i>=0:
		ind = iList[i]
		num = sortedB[ind]
		numA[i+1],i = num,i-1
		sortedB.remove(num)
	numA[0] = sortedB[0]
	return numA

def ParseAnimationState(state):
	return (state&0xf), (state>>4&0xf), (state>>8&0xf), (state>>12&1)
def BuildAnimationState(type,step,rcg,flicker):
	return (type&0xf)|(step&0xf)<<4|(rcg&0xf)<<8|(flicker&1)<<12
def PrintArray(a):
	for r in xrange(9):
		i = r*9
		print ','.join([GetBitString(a[i+c]) for c in xrange(9)])
		#print ','.join(['%03x' % a[i+c] for c in xrange(9)])

def GetIBmpByFlag(flag):
	if flag&HIGHL_BIT:
		return 1
	elif flag&FIXED_BIT:
		return 3
	else:
		return flag&BITMAP_MASK
#Function name
#R:row C:col G:region
#IR, IC, IG means index of row, col, region
#Get region index 0 to 8
def GetGByRC(row,col):
	return row/3*3+col/3

def GetGByI(i):
	return i/27*3+(i%9)/3

def GetRC(i):
	return i/9,i%9

def GetRCG(i):
	r,c=i/9,i%9
	return r,c,r/3*3+c/3
#Get region start square index 0 to 81
def GetGI1ByRC(row,col):
	return row/3*27+col/3*3

def GetGI1ByI(i):
	return i/27*27+(i%3)*3
def GetGI1ByG(g):
	return g/3*27+g%3*3

#RI, CI, GI means index in row, col, region
def GetGIByI(i):
	return (i/9%3)*3+(i%3)

#return col,row,GetGIByI(i)
def GetIInRCG(i):
	r,c=i/9,i%9
	return c,r,(r%3)*3+(c%3)

def GetOffsetOfRC(rc):
	return rc*SQ_SIZE + rc/3*REG_SPACE
def GetRCOfOffset(rc):
	return rc*SQ_SIZE + rc/3*REG_SPACE

def GetRectByRC(r,c):
	rect = copy.copy(SQ_RECT)
	rect.SetPosition((GetOffsetOfRC(c),GetOffsetOfRC(r)))
	rect.Offset(SQ_OFFSET)
	return rect

def GetRectByI(i):
	r,c = GetRC(i)
	return GetRectByRC(r,c)

def GetIByXY(x,y):
	n,y,x = 0,y-SQ_OFFSET.y, x-SQ_OFFSET.x
	#Check Row
	for i in xrange(-1,9):
		xy = GetRCOfOffset(i)
		if y>=xy and y<=xy + SQ_SIZE:
			y,n = i,1
			break
	#Check Col
	for i in xrange(9):
		xy = GetRCOfOffset(i)
		if x>=xy and x<=xy + SQ_SIZE:
			x,n = i,n+1
			break
	if n == 2:
		return y*9 + x
	else:
		return IND_OUTSIDE

def GetAllIInRCG(i,type):
	if type==0:
		i = i*9
		indice = xrange(i,i+9)
	elif type==1:
		indice = xrange(i,81,9)
	else:
		i = GetGI1ByG(i)
		#indice = copy.copy(REG_INC_IND)
		indice = [x+i for x in REG_INC_IND]
		#indice = map(lambda x:x+i, REG_INC_IND)
	return indice
def GetAllIInRCGByI(i,type):
	if type==0:
		i = i/9*9
		indice = xrange(i,i+9)
	elif type==1:
		indice = xrange(i%9,81,9)
	else:
		i = GetGI1ByI(i)
		#indice = copy.copy(REG_INC_IND)
		indice = [x+i for x in REG_INC_IND]
		#indice = map(lambda x:x+i, REG_INC_IND)
	return indice

def GetAllIByRCGFlag(rf,cf,gf):
	iList = []
	for r in xrange(9):
		if (1<<r)& rf:
			g0 = 1<<(r/3*3)
			for c in xrange(9):
				if (1<<c) & cf and g0<<(c/3) & gf:
					iList.append(r*9+c)
	return iList

def UpdateRCGFlagA(flagA,i,num,numGrid,indice):
	old = flagA[i]
	bFound = False
	if num > 0: # Add mask
		flagA[i] = old | (1<<(num-1))
	elif num < 0: # Del mask
		num = -num
		for j in indice:
			if numGrid[j]==num: #Find if other squre contains this num
				bFound = True; break
		if not bFound:
			flagA[i] &= 0xffff-(1<<(num-1)) #No found, remove mask
	#else:
	#    flagA[i] = 0 #reset
	return old!=flagA[i]

def GetI1Bit(i,bitv=0,bits=9):
	for j in xrange(bits):
		if (i&1)==bitv:
			return j
		i>>=1
	return -1

def GetBitCount(i,bitv=0,bits=9):
	t,i1 = 0,-1
	for j in xrange(bits):
		if (i&1)==bitv:
			t+=1
			if i1<0:i1=j
		i>>=1
	return t,i1

def NextIBit0(flag,i1,bits=9):
	#i1bit = 1<<i1
	#flag |= i1bit
	bits-=1
	while i1<bits:
		i1+=1
		if flag&(1<<i1)==0:
			return i1
	return -1
def NextIBit1(flag,i1,bits=9):
	bits-=1
	while i1<bits:
		i1+=1
		if flag&(1<<i1):
			return i1
	return -1

def GetAllIBit(i,bitv=0,bits=9):
	iList = []
	for j in xrange(bits):
		if (i&1)==bitv:
			iList.append(j)
		i>>=1
	return iList

def GetArrayBitsAndCount(flagA,bitmask,indice):
	t,i1 = 0,-1
	for i in indice:
		if flagA[i]&bitmask:
			t+=1
			if i1<0:i1=i
	return t,i1

def GetArrayBitsOrCount(flagA,bitmask,indice):
	t,i1 = 0,-1
	bitmask = ~bitmask
	for i in indice:
		if flagA[i]|bitmask == bitmask:
			t+=1
			if i1<0:i1=i
	return t,i1

def CreateArray(size,type="i",defval=0):
	a = array.array(type)
	a.extend([defval]*size)
	return a

def GetBitString(i):
	#return "%X"%i
	s = ''
	for j in xrange(9):
		s = "%d"%(i&1)+s
		i = i>>1
	return s

def AndArray(flagA, iList):
	flag = ALL_NUM_BITS
	for i in iList:
		flag&=flagA[i]
	return flag

def AndArrayExceptI(flagA, iList, i):
	flag = ALL_NUM_BITS
	for j in iList:
		if j!=i:
			flag&=flagA[j]
	return flag

NUM_PEN_COLOR = [(178,  34,  34), (255, 0, 0)]
NUM_BRUSH_COLOR = [(140, 140, 35), (240,240,35), (170, 170, 35),(200, 200,  35)]

def GetBitmapByName(bmpName):
	if os.path.isfile(bmpName):
		try:
			return wx.Image(bmpName,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
		except:
			return wx.NullBitmap
	else:
		return wx.ArtProvider.GetBitmap(bmpName,size=(16,16))

def GetPen(rgb):
	r,g,b = rgb
	return wx.Pen(wx.Colour(r,g,b))
def GetBrush(rgb):
	r,g,b = rgb
	return wx.Brush(wx.Colour(r,g,b,255))

class NGBoard:
	def __init__(self,window):
		self.window = window
		self.InitData()
		self.numBitmap = NGRes.getNumbersBitmap()
		#self.numBitmap = GetBitmapByName('Numbers.png')#wx.Image('Numbers.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		self.penList   = map(GetPen,NUM_PEN_COLOR)
		self.brushList = map(GetBrush,NUM_BRUSH_COLOR)
		self.memdc = wx.MemoryDC()
		self.memdc.SelectObject(self.numBitmap)
		self.timerEnabled = False
		self.StartThreadTimer(100)

	def NextAniType(self):
		if self.aniType != ANI_TYPE_NONE:
			self.aniList[self.aniType]=ANIMATION_NONE
		self.aniType = (self.aniType+1)%(ANI_TYPE_NONE+1)
		if self.aniType != ANI_TYPE_NONE:
			self.aniList[self.aniType]=(self.aniType,17,1,ANI_CYCLE_BIT)

	def NextAniStep(self):
		for i in xrange(len(self.aniList)):
			type,step,ircgn,options = self.aniList[i]
			step=step-1
			if type!=ANI_TYPE_NONE:
				if step<0:
					if options&ANI_CYCLE_BIT:
						step = 17
					else:
						type=ANI_TYPE_NONE
					pass
				self.aniList[i] = (type,step,ircgn,options)

	def LoadFromFile(self, fileName):
		file = open(fileName,"r")
		self.InitData()
		[
			self.numGridA,
			self.drawFlagA,
			self.iMove,
			self.iLastMove,
			self.moveList,
			self.rcgFlagList,
			self.squareFlagA
		] = pickle.load(file)
		self.rowFlagA,self.colFlagA,self.regFlagA,self.numFinished = self.rcgFlagList
		file.close()
		self.RedrawBoard()
	def LShiftHLFlag(self,step):
		hlFlag,step = self.hlFlag & ALL_NUM_BITS,step%9
		hlFlag = (hlFlag>>step) | (hlFlag<<9>>step) & ALL_NUM_BITS
		if hlFlag==0:
			#Get first unfinished & highlight it
			for inum in xrange(9):
				if not self.numFinished[inum+1]:
					self.hlFlag = 1<<inum
					break
		else:
			self.hlFlag = hlFlag

	def SaveToFile(self, fileName):
		file = open(fileName,"w")
		pickle.dump(
			[
				self.numGridA,
				self.drawFlagA,
				self.iMove,
				self.iLastMove,
				self.moveList,
				self.rcgFlagList,
				self.squareFlagA
			],
			file
		)
		file.close()

	def InitData(self):
		self.iActive = -10
		self.hlFlag = 0
		self.numGridA = CreateArray(81,'i',0)
		self.drawFlagA = CreateArray(81,'i',0)
		self.ClearFlagArray()
		self.iLastMove = 0
		self.iMove = 0
		self.bAutoMove = False
		self.inTimerEvent = False
		self.sortedMoveI = range(81)
		self.canMoveList = range(81)
		self.moveList = range(300)
		self.iGameFound = 0
		self.aniType = ANI_TYPE_NONE
		self.timeTick = 0
		self.totalGames = 0
		self.bInSearching = False
		self.ClearAnimation()
		self.UpdateCanMoveList()
		self.enableDraw = True

	def ClearAnimation(self):
		self.aniList = [ANIMATION_NONE for type in xrange(ANI_TYPE_NONE)]

	def ClearFlagArray(self):
		#Flag arryas
		#If Flag n bit is set, means n can not be in this row, col, reqgion or square.
		self.numFinished = [False for i in xrange(10)]
		self.colFlagA = CreateArray(9,'i',0)
		self.rowFlagA = CreateArray(9,'i',0)
		self.regFlagA = CreateArray(9,'i',0)
		self.squareFlagA = CreateArray(81,'i',0)
		self.invSqFlagA = CreateArray(81,'i',ALL_NUM_BITS)
		self.rcgFlagList = [self.rowFlagA,self.colFlagA,self.regFlagA,self.numFinished]

	def UpdateGridSearchFlag(self, i):
		r,c,g=GetRCG(i)
		num = self.numGridA[i]
		if num>0:
			num = (1<<num)-1
			if r==0:
				irc = c/3*3
				for ic in xrange(irc,irc+3):
					if ic>c:
						self.squareFlagA[ic] |= num
					elif ic<c:
						self.squareFlagA[ic] |= ALL_NUM_BITS-num
			if c==0:
				irc = r/3*27
				for ir in xrange(irc,irc+27,9):
					if ir>c:
						self.squareFlagA[ir] |= num
					elif ir<c:
						self.squareFlagA[ir] |= ALL_NUM_BITS-num
	def UpdateGridFlag(self, i):
		r,c,g=GetRCG(i)
		num = self.numGridA[i]
		if num==0:
			self.squareFlagA[i] = self.rowFlagA[r]|self.colFlagA[c]|self.regFlagA[g]

	def UpdateAllFlags(self,i,num):
		#Update Row,Col, Region Flag Array
		rcg = GetRCG(i)
		indice = [0,0,0];  bChanged = [0,0,0]
		#Update RCG Flags
		rcgTypes = [0,1,2]
		for type in rcgTypes:
			indice[type] = GetAllIInRCG(rcg[type],type)
			#indice[type] = GetAllIInRCGByI(i,type)
			bChanged[type] = UpdateRCGFlagA(self.rcgFlagList[type],rcg[type],num,self.numGridA,indice[type])
		#Update Grid Flags
		for type in rcgTypes:
			if bChanged[type]:
				#If row, col, region finished, fliker it.
				if self.rcgFlagList[type][rcg[type]]==ALL_NUM_BITS:
					self.aniList[type]=(ANI_TYPE_ROW+type,9,1<<rcg[type],ANI_FLICK_BIT)
				for j in indice[type]:
					self.UpdateGridFlag(j)
		if self.bInSearching:
			for type in rcgTypes:
				if bChanged[type]:
					for j in indice[type]:
						self.UpdateGridSearchFlag(j)
		if num>0:
			self.squareFlagA[i] = ALL_NUM_BITS

	def AddINum(self,i,num):
		self.numGridA[i] = num
		self.UpdateAllFlags(i, num)

	def DelINum(self,i):
		num = self.numGridA[i]
		self.numGridA[i] = 0
		self.squareFlagA[i] = 0
		self.UpdateAllFlags(i, -num)

	def GetDrawNumFlag(self,i):
		if i<0:
			num = i+10
			if self.numFinished[num]:
				drawFlag = 3
			else:
				drawFlag = 0
		else:
			num,drawFlag = self.numGridA[i],self.drawFlagA[i]
		n = num - 1
		r,c,g = GetRCG(i)
		ircgn = [r,c,g,n]
		srcgn = [c,r,(r%3)*3+(c%3),n]
		for ani in self.aniList:
			type,step,arcgn,options = ani
			if type<ANI_TYPE_NONE:
				itype = type & 3
				if type<ANI_TYPE_ROW:
					#cyclely highlight row,colum,region,num
					istep=ircgn[itype]
				elif arcgn<0:
					if arcgn==-i:
						istep = 1
					else:
						istep = -1
				elif ircgn[itype]>=0 and arcgn&(1<<ircgn[itype]):
					istep=srcgn[itype]
				else:
					istep =-1
				if options&ANI_FLICK_BIT:
					#Flicker single cell
					if step&1 and istep>=0:
						drawFlag |= HIGHL_BIT
				else:
					if 8-(step%9)==istep:
						drawFlag |= HIGHL_BIT
		if i==self.iActive:
			drawFlag |= ACTIVE_BIT
		return num,drawFlag

	def DrawNumBase(self, dc, mdc, rect, num, drawFlag):
		bActive = drawFlag&ACTIVE_BIT
		if bActive:
			rect.Inflate(-1,-1)
		if num>0:
			if self.hlFlag&(1<<(num-1)):
				x = 26
			else:
				x = GetIBmpByFlag(drawFlag)*25+1
			dc.Blit(rect.Left,rect.Top,25,25,mdc,x,num*25-25)
		else:
			if bActive:
				iPen,iBrush = 1,3
			else:
				iPen,iBrush = 0,0
			dc.SetPen(self.penList[iPen])
			dc.SetBrush(self.brushList[iBrush])
			dc.DrawRoundedRectangleRect(rect, 2)

	def RedrawBoard(self,pdc = None):
		if self.enableDraw:
			try:
				if pdc is None:
					pdc = wx.ClientDC(self.window)
				dc = wx.BufferedDC(pdc)
			except:
				dc = pdc
			try:
				mdc = self.memdc
				dc.SetBrush(wx.Brush(wx.BLACK))
				#wx.Brush("BLACK", wx.CROSSDIAG_HATCH))
				#dc.Clear()
				windowSize  = self.window.GetSizeTuple()
				dc.DrawRectangle(0, 0,  windowSize[0], windowSize[1])
				#dc.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL,    wx.BOLD, False))
				for i in xrange(-9,81):
					num,drawFlag = self.GetDrawNumFlag(i)
					self.DrawNumBase(dc,mdc,GetRectByI(i),num,drawFlag)
				dc.SetBrush(wx.TRANSPARENT_BRUSH)
				dc.SetPen(wx.Pen(wx.GREEN))
				regSize = SQ_SIZE*3+1
				for i in xrange(9):
					if self.rowFlagA[i]==ALL_NUM_BITS:
						dc.SetTextForeground(wx.GREEN)
					else:
						dc.SetTextForeground(wx.WHITE)
					dc.DrawLabel(chr(ord('A')+i),GetRectByRC(i,-1),wx.ALIGN_CENTRE)
					if self.colFlagA[i]==ALL_NUM_BITS:
						dc.SetTextForeground(wx.GREEN)
					else:
						dc.SetTextForeground(wx.WHITE)
					dc.DrawLabel(chr(ord('1')+i),GetRectByRC(9,i),wx.ALIGN_CENTRE)
					if self.regFlagA[i]==ALL_NUM_BITS:
						r,c = GetRC(GetGI1ByG(i))
						#i9 = i1+REG_INC_IND[8]
						#rect = wx.Rect(GetOffsetOfRC(r),GetOffsetOfRC(c),GetOffsetOfRC(r+3),GetOffsetOfRC(c+3))
						#rect.Offset(SQ_OFFSET)
						dc.DrawRectangle(GetOffsetOfRC(c)+SQ_OFFSET.x-1,GetOffsetOfRC(r)+SQ_OFFSET.y-1,regSize,regSize)
				if self.iActive>=0 and self.timeTick&0x2:
					rect = GetRectByI(self.iActive)
					rect.Inflate(1,1)
					dc.DrawRectangleRect(rect)
			finally: pass

	def FindMoveInIList(self,iList=xrange(81)):
		for i in iList:
			if self.numGridA[i]>0:
				self.canMoveList[i]=MOVE_NONE
			else:
				rcg,flag = GetRCG(i),0
				for type in [0,1,2]:
					allI = GetAllIInRCG(rcg[type],type)
					flag |= AndArrayExceptI(self.squareFlagA,allI,i)-self.rcgFlagList[type][rcg[type]]
					#allI.remove(i)
				if flag:
					np,i1 = GetBitCount(flag,1)
					if np>1:
						np = -1
					else:
						if self.squareFlagA[i]&flag:
							np=-1
						else:
							flag=~flag&ALL_NUM_BITS
				else:
					flag = self.squareFlagA[i]
					np,i1 = GetBitCount(flag,0)
				self.canMoveList[i] = [np,i,i1,flag]
	def SortMoveList(self):
		#self.sortedMoveI[0]=iList[0]
		def CMPMove(i,j):
			return cmp(self.canMoveList[i],self.canMoveList[j])
		self.sortedMoveI.sort(CMPMove)

	def ForwardMove(self):
		if self.iMove<self.iLastMove:
			np,i,i1,flag,oldNum = self.moveList[self.iMove]
			self.AddINum(i,i1+1)
			self.iMove += 1
			if not self.bInSearching:
				self.UpdateNumFinishedFlags([i1+1,oldNum])

	def BackwardMove(self):
		#last move
		if self.iMove:
			self.iMove -= 1
			np,i,i1,flag,oldNum = self.moveList[self.iMove]
			if i1>=0:
				self.DelINum(i)
				self.drawFlagA[i] &= ~FIXED_BIT
			if oldNum>0:
				self.AddINum(i,oldNum)
			if not self.bInSearching:
				self.UpdateNumFinishedFlags([i1+1,oldNum])

	def IsNumFinished(self,num):
		numBit, t = 1<<(num-1), 0
		for i in [0,1,2]:
			if AndArray(self.rcgFlagList[i],xrange(9))&numBit==0:
				return False
		for i in xrange(81):
			if self.numGridA[i]==num:
				t += 1
				if t>9: return False
		return t==9
	def UpdateNumFinishedFlags(self,numList=xrange(1,10)):
		for inum in numList:
			if inum>0:
				self.numFinished[inum] = self.IsNumFinished(inum)
				if self.numFinished[inum]:
					#Flick finished number
					self.hlFlag = self.hlFlag & ~(1<<inum>>1)
					self.aniList[ANI_TYPE_NUM]=(ANI_TYPE_NUM,9,1<<(inum-1),ANI_FLICK_BIT)

	def AddMove(self,i,num,bUserInput=True,bFixed=False):
		#if self.numGridA[i]==0:
		oldNum = self.numGridA[i]
		if bUserInput:
			if num!=oldNum and (not (self.drawFlagA[i]&FIXED_BIT) or bFixed):
				np,i2,i1,flag = self.canMoveList[i]
				if oldNum>0:
					self.DelINum(i)
					self.drawFlagA[i] &= ~FIXED_BIT
				i1 = num-1
				if bFixed and num>0:
					self.drawFlagA[i] |= FIXED_BIT
				bAdd,np = True,np+1
			else:
				bAdd = False
		else:
			#Auto move
			oldNum = -1
			bAdd = True
		if bAdd:
			if self.iMove<300:
				self.iMove += 1
				self.AddINum(i,num)
				if bUserInput:
					self.moveList[self.iMove-1] = (np,i,i1,flag,oldNum)
				self.iLastMove = self.iMove
				self.aniList[ANI_TYPE_ROW]=(ANI_TYPE_ROW,4,-i,ANI_FLICK_BIT)
				if not self.bInSearching:
					if self.IsNumFinished(num) and self.hlFlag&(1<<num>>1):
						self.LShiftHLFlag(8)
					self.UpdateNumFinishedFlags([num,oldNum])
					#self.UpdateNumFinishedFlags(xrange(1,10))
					if self.IsGameFinished() and not self.bAutoMove:
						#wx.MilliSleep(50)
						wx.MessageBox("Congratulations, well done!",'Number Game')
					#self.UpdateNumFinishedFlags([num,oldNum])
				#Flick current cell
			else:
				pass #no move valid
	def IsGameFinished(self):
		for type in [0,1,2]:
			flagA = self.rcgFlagList[type]
			for i in xrange(9):
				if ALL_NUM_BITS!= flagA[i]:
					return False
		return True
	def CompressFinishedBoard(self):
		if self.IsGameFinished():
			return [CompressRCGArray(self.numGridA,xrange(r*9,r*9+9)) for r in xrange(8)]
		else:
			return []
	def SaveBoardByI(self,i,numA):
		try:
			file = open('NGData.ngb','r+b')
		except:
			file = open('NGData.ngb','w+b')
		file.seek(i*20,0)
		pos=file.tell()
		numB = array.array('B',xrange(20))
		for i in xrange(0,8,2):
			j = i/2*5
			numB[j+1:j+4]=array.array('B',[numA[i]&0xff,(numA[i]>>8)&0xff,numA[i+1]&0xff,(numA[i+1]>>8)&0xff])
			numB[j]=((numA[i+1]>>12)&0xf0) + (numA[i]>>16) & 0xff
		file.write(numB.tostring())
		#numB.write(file)
		file.close()
	def LoadBoardByI(self,i):
		file = open('NGData.ngb','rb')
		file.seek(i*20,0)
		numA=array.array('B',[])
		astr = file.read(20)
		numA.fromstring(astr)
		numB = range(8)
		for i in xrange(0,8,2):
			j = i/2*5
			numB[i] = ((numA[j]&0xf)<<16) + numA[j+1] + (numA[j+2]<<8)
			numB[i+1]=((numA[j]>>4) <<16) + numA[j+3] + (numA[j+4]<<8)
		return numB

	def ShuffleBoard(self,seed):
		ib = range(81)
		random.seed(seed)
		rr = [RandomRange(3) for i in xrange(8)]
		ri,ci = range(9),range(9)
		for i in xrange(3):
			for j in xrange(3):
				ri[i*3+j] = rr[3][i]*3+rr[i][j]
				ci[i*3+j] = rr[7][i]*3+rr[i+4][j]
		rotate = random.randrange(2)==0
		for i in xrange(81):
			r,c = GetRC(i)
			if rotate:
				r,c=ci[c],ri[r]
			else:
				r,c=ri[r],ci[c]
			ib[i] = r*9+c
		return ib

	def LoadBoard(self,gn,pn):
		self.InitData()
		self.enableDraw = False
		numA = self.LoadBoardByI(gn)
		ib = self.ShuffleBoard(gn+pn)
		ni = [0]
		ni.extend(RandomRange(1,10))
		for r in xrange(8):
			cA = DeCompressRCGArray(numA[r])
			for c in xrange(9):
				self.AddINum(ib[r*9+c],ni[cA[c]])
		for i in xrange(9):
			j = ib[i+72]
			num = GetI1Bit(self.squareFlagA[j],0)+1
			self.AddINum(j,num)
		ib = RandomRange(0,81,pn)
		n = pn/30+30
		for i in xrange(n):
			self.DelINum(ib[i])
		for i in xrange(n,81):
			self.drawFlagA[ib[i]] |= FIXED_BIT|LOADED_BIT
		self.ClearAnimation()
		self.UpdateNumFinishedFlags()
		self.enableDraw = True
		self.RedrawBoard()

	def RunSearch(self,maxGames):
		while self.keepGoing and self.iGameFound < maxGames:
			count = self.iGameFound
			while count==self.iGameFound:
				self.FindNextMove()
				if not self.keepGoing:break
				if self.bAutoMove:
					wx.MilliSleep(self.timerInterval)

	def SearchAllGames(self,maxGames=100000):
		self.bInSearching = maxGames>10
		self.bAutoMove = not self.bInSearching
		self.keepGoing = True
		self.iGameFound = 0

		msg = "Searching Games..."
		dlg = wx.ProgressDialog(
			"Number Game",
			msg,
			maximum = maxGames,
			parent=self.window,
			style = wx.PD_CAN_ABORT | #wx.PD_APP_MODAL |
			wx.PD_ELAPSED_TIME #| wx.PD_REMAINING_TIME
		)
		self.FindFirstMove()
		thread.start_new_thread(self.RunSearch,(maxGames,))
		while self.keepGoing:
			newmsg = msg+',%d found'%self.iGameFound
			(self.keepGoing, skip) = dlg.Update(self.iGameFound,newmsg)
			if self.iGameFound >= maxGames:
				break
			wx.MilliSleep(50)
		self.bInSearching = False
		self.bAutoMove = False
		#if self.keepGoing:
		#	wx.MessageBox("Auto Search is done!",'Number Game')
		dlg.Destroy()

	def FindNextMove(self):
		np,i,i1,flag,oldNum = self.moveList[self.iMove]
		if np==10:#done
			self.aniList[ANI_TYPE_ROW] = ANIMATION_NONE
			self.iGameFound += 1
			if self.bInSearching:
				boardArray = [CompressRCGArray(self.numGridA,xrange(r*9,r*9+9)) for r in xrange(8)]
				self.SaveBoardByI(self.iGameFound,boardArray)
				self.moveList[self.iMove]=(-1,i,i1,flag,oldNum)
		else:
			if np>0 and oldNum<0:
				self.AddMove(i,i1+1,False)
				self.FindFirstMove()
			else:
				self.BackwardMove()
				np,i,i1,flag,oldNum = self.moveList[self.iMove]
				if oldNum>0:
					np = 0
				else:
					i1 = NextIBit0(flag,i1)
				self.moveList[self.iMove] = (np-1,i,i1,flag,oldNum)
	def ShowHint(self):
		self.UpdateCanMoveList()
		i = self.sortedMoveI[0]
		np,i,i1,flag = self.canMoveList[i]
		if np<=0:
			wx.MessageBox('No possible move','Number Game')
		elif np>9:
			wx.MessageBox('Game finished','Number Game')
		else:
			self.AddMove(i,i1+1,True)

	def UpdateCanMoveList(self):
		self.FindMoveInIList()
		self.SortMoveList()

	def FindFirstMove(self):
		self.UpdateCanMoveList()
		i = self.sortedMoveI[0]
		self.moveList[self.iMove] = self.canMoveList[i][:]
		self.moveList[self.iMove].append(-1)

	def StartThreadTimer(self,timeInterval):
		if not self.timerEnabled:
			self.timerInterval = timeInterval
			self.timerEnabled = True
			self.timerThread = thread.start_new_thread(self.OnThreadTimer,())

	def StopThreadTimer(self):
		self.timerEnabled = False

	def OnThreadTimer(self):
		while self.timerEnabled:
			self.timeTick=(self.timeTick+1)&0xff
			self.NextAniStep()
			if self.bAutoMove and self.timeTick&0x7==0x0:
				pass#self.FindNextMove()
			try:
				self.RedrawBoard()
				wx.MilliSleep(self.timerInterval)
			except:
				pass

if __name__ == "__main__":
	#a =range(1,10)
	#b = CompressRCGArray(a,xrange(9))
	#c = DeCompressRCGArray(b)
	a=RandomRange(10,seed=100)
	b=RandomRange(10,seed=101)
	c=RandomRange(10,seed=100)
	numB = Shuffle(1000)
	print a

