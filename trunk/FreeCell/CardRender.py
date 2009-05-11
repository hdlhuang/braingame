import os
import wx
from Card import *
import CardRes
IMASK = 54

def GetCardMask(w=CARD_W,h=CARD_H):
	mdc = wx.MemoryDC()
	bmp = wx.EmptyBitmap(w,h,-1)
	mdc.SelectObject(bmp)
	mdc.SetBrush(wx.WHITE_BRUSH)
	mdc.SetPen(wx.WHITE_PEN)
	mdc.DrawRoundedRectangle(0,0,w,h,3)
	mdc.SelectObject(wx.NullBitmap)
	return bmp
def GetCardBmp(i,w=CARD_W,h=CARD_H,bFS=True):
	mdc = wx.MemoryDC()
	bmp = wx.EmptyBitmap(w,h,-1)
	mdc.SelectObject(bmp)
	mdc.SetBrush(wx.WHITE_BRUSH)
	mdc.SetPen(wx.BLACK_PEN)
	mdc.DrawRoundedRectangle(0,0,w,h,3)
	name = GetNameByI(i,bFS)
	color,face = GetSFByI(i,bFS)
	if SUIT_COLOR[color]==RED:
		mdc.SetTextForeground(wx.RED)
	else:
		mdc.SetTextForeground(wx.BLACK)
	mdc.DrawLabel(name,wx.Rect(0,0,w,20),wx.ALIGN_CENTER)
	mdc.DrawLabel(name,wx.Rect(0,h-20,w,20),wx.ALIGN_CENTER)
	mdc.SelectObject(wx.NullBitmap)
	return bmp
class CardRender:
	def __init__(self, resPath='.\\res\\'):
		self.InitData(resPath)
	def InitData(self, resPath):
		mask, bmpList = 0, [0]*54
		try:
			allFiles = ListDirFiles(resPath)
			for f in allFiles:
				i = GetIByName(f)
				if i>=0:
		 			bmp = wx.Bitmap(os.path.join(resPath,f),wx.BITMAP_TYPE_ANY)
					bmpList[i] = bmp
				else:
					if f.lower()[0:4]=='mask':
						mask = wx.Bitmap(os.path.join(resPath,f),wx.BITMAP_TYPE_ANY)
		except:
			mask = 0
		if not mask:
			mask = CardRes.catalog['Mask'].getBitmap()
			bmpList = [CardRes.catalog['%02d'%i].getBitmap() for i in xrange(54)]
		self.GetAllBmp(bmpList,mask)

	def GetCardXY(self,cn):
		return cn/4*self.width,(cn%4)*self.height
	def GetAllBmp(self, bmpList, mask):
		w, h = self.width, self.height = mask.GetWidth(), mask.GetHeight()
		self.allCardsBmp = wx.EmptyBitmap(w*16,h*4,-1)
		dDC = wx.MemoryDC(self.allCardsBmp)
		sDC = wx.MemoryDC()
		for cn in xrange(55):
			x, y = cn/4*w,(cn%4)*h
			sDC.SelectObject(mask)
			dDC.Blit(x,y,w,h,sDC,0,0)
			if cn!=IMASK:
				sDC.SelectObject(bmpList[cn])
				dDC.Blit(x,y,w,h,sDC,0,0,rop=wx.AND)
		sDC.SelectObject(wx.NullBitmap)
		self.mdc = dDC

	def DrawCard(self,dc,x,y,card):
		self.DrawCardCN(dc,x,y,card.cn)
	def DrawCardSF(self,dc,x,y,s,f):
		self.DrawCardCN(dc,x,y,GetIBySF(s,f))
	def DrawCardCN(self, dc, x, y, cn,rop=wx.OR):
		if cn>=0:
			sx, sy = self.GetCardXY(54) #MASK
			dc.Blit(x,y,self.width,self.height,self.mdc,sx,sy,rop=wx.AND_INVERT)
			sx, sy = self.GetCardXY(cn)
			dc.Blit(x,y,self.width,self.height,self.mdc,sx,sy,rop=rop)

if __name__ == "__main__":
	global app
	if not wx.GetApp():
		app = wx.PySimpleApp()
	cr = CardRender()
	cr.allCardsBmp.SaveFile('all.bmp',wx.BITMAP_TYPE_BMP)
	#GetCardBmp(1)
	print [GetNameByI(i) for i in xrange(52,55)]
	print GetIByName('JokerS'),GetIByName('JokerB'),GetIByName('1')
	'''app = wx.App()
	cr = CardRender()
	#cr.bmpList[0].SaveFile('bmp0.bmp',wx.BITMAP_TYPE_BMP)
	#cr.mask.SaveFile('m.bmp',wx.BITMAP_TYPE_BMP)
	for i in xrange(54):
		cr.bmpList[i].SaveFile('.\\res\\Animals'+GetNameByI(i,False)+'.jpg',wx.BITMAP_TYPE_JPEG)
	for i in xrange(54):
		fname = '.\\res\\card%02d.bmp' %i
		name = '.\\res\\'+GetNameByI(i,False)+'.bmp'
		if os.path.isfile(fname):
			os.rename(fname, name)
	'''