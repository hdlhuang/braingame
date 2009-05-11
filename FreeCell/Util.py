import array
import os
import wx

def Get1stV(a,v,iList):
	for i in iList:
		if a[i]==v:
			return i
	return -1
def Get1stNV(a,v,iList):
	for i in iList:
		if a[i]!=v:
			return i
	return -1
def GetI1Bit(i,bitv=0,bits=8):
	for j in xrange(bits):
		if (i&1)==bitv:
			return j
		i>>=1
	return -1

def GetBitCount(i,bitv=0,bits=8):
	t,i1 = 0,-1
	for j in xrange(bits):
		if (i&1)==bitv:
			t+=1
			if i1<0:i1=j
		i>>=1
	return t,i1

def NextIBit0(flag,i1,bits=8):
	#i1bit = 1<<i1
	#flag |= i1bit
	bits-=1
	while i1<bits:
		i1+=1
		if flag&(1<<i1)==0:
			return i1
	return -1
def NextIBit1(flag,i1,bits=8):
	bits-=1
	while i1<bits:
		i1+=1
		if flag&(1<<i1):
			return i1
	return -1

def GetAllIBit(i,bitv=0,bits=8):
	iList = []
	for j in xrange(bits):
		if (i&1)==bitv:
			iList.append(j)
		i>>=1
	return iList

def CreateArray(size,type="i",defval=0):
	a = array.array(type)
	a.extend([defval]*size)
	return a
def CreateList(size,defval=0):
	return [defval]*size #[defval for i in xrange(size)]
def GetBitmapByName(bmpName):
	if os.path.isfile(bmpName):
		try:
			return wx.Image(bmpName,wx.BITMAP_TYPE_ANY).ConvertToBitmap()
		except:
			return wx.NullBitmap
	else:
		return wx.ArtProvider.GetBitmap(bmpName,size=(16,16))

def ListDirFiles(path):
	flist = []
	for f in os.listdir(path):
		if os.path.isfile(os.path.join(path,f)):
			flist.append(f)
	return flist

def LogicOpBmp(aBmp, bBmp, op):
	adc = wx.MemoryDC(aBmp)
	bdc = wx.MemoryDC(bBmp)
	#adc.SelectObject(aBmp)
	#bdc.SelectObject(bBmp)
	adc.Blit(0,0,bBmp.GetWidth(),bBmp.GetHeight(),bdc,0, 0, rop=op)
	#Release it
	adc.SelectObject(wx.NullBitmap)
	bdc.SelectObject(wx.NullBitmap)
	return aBmp
def GetPen(rgb):
	r,g,b = rgb
	return wx.Pen(wx.Colour(r,g,b))
def GetBrush(rgb):
	r,g,b = rgb
	return wx.Brush(wx.Colour(r,g,b,255))
if __name__ == "__main__":
	print ListDirFiles('.\\res\\')
