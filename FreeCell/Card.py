# -*- coding: gbk -*-
import wx
import os
import re
from Util import *

IEMPTY = -1
[BLACK,RED] = [0, 1]
[CLUB,DIAMOND,HEART,SPADE,JOKER] = range(5)
SUIT_COLOR  = [BLACK,RED,RED,BLACK,-1]
SUIT_STR = ['Club', 'Diamond', 'Heart', 'Spade', "Joker","Invalid"] #'\5\4\3\6'
SUIT_STR_CS = ['梅花', '方块','红桃' ,'黑桃', '无效' ]
FACE_STR = 'A23456789TJQKSB '
FACE_STR_DICT={'10':9, '0':9, '1':0, 'SMALL':13, 'BIG':14, 'KN':10}

NEXT_FC_CARD=CreateArray(56,defval=IEMPTY)
PREV_FC_CARD=CreateArray(56,defval=IEMPTY)
THIS_FC_CARD=CreateArray(56,defval=IEMPTY)

for cn in xrange(52):
	#change heart,spade to diamond,club, same color
	color,face = SUIT_COLOR[cn%4],cn/4
	face0 = color*13
	THIS_FC_CARD[cn] = face0+face
	if face<13:
		NEXT_FC_CARD[cn] = 14-face0+face
	if face>0:
		PREV_FC_CARD[cn] = 12-face0+face

CARD_W,  CARD_H  = 71,  96
CARD_RECT = wx.Rect(0, 0, CARD_W,  CARD_H)
#'knave' or j is J, 'A' '1' is Ace, '10' '0' is 10
CARD_RE_PATTERN = re.compile('(?P<suit>((club)|(diamond)|(heart)|(spade)|(joker)|[cdhsj]){1}[s]{0,1})[_\- ]*(?P<face>((10)|(kn)|[a1234567890jqksb]){1}).*')
#Get suit face by card #
def GetSFByI(i,bFS=True):
	if i<0 or i>53:
		return -1,-1
	if i>51:
		return JOKER,i-52+13
	if bFS: #Card # 0 1 2 3 are four ACE
		return i%4, i/4
	else: #Card # 0 13 26 39 are four ACE
		return i/13, i%13
#Get card # by suit face
def GetIBySF(s,f,bFS=True):
	if s<0 or s>JOKER:
		return IEMPTY
	if s==JOKER:
		return f+52-13
	if bFS: #Card # 0 1 2 3 are four ACE
		return f*4+s
	else: #Card # 0 13 26 39 are four ACE
		return s*13+f
#Get card name by card #
def GetNameByI(i, bFS=True):
	s, f = GetSFByI(i, bFS)
	if s<0:
		return ''
	return SUIT_STR[s]+FACE_STR[f]

def GetShortNameByI(i, bFS=True):
	s, f = GetSFByI(i, bFS)
	if s<0:
		return '   '
	return SUIT_STR[s][0]+FACE_STR[f][0]+' '

def GetIByName(name, bFS=True):
	b = CARD_RE_PATTERN.match(name.lower())
	if b is None:
		return IEMPTY
	else:
		suit, face = b.group('suit').upper(),b.group('face').upper()
		for s in xrange(5):
			if suit[0]==SUIT_STR[s][0]:
				break
		if FACE_STR_DICT.has_key(face):
			f = FACE_STR_DICT[face]
		else:
			for f in xrange(15):
				if face==FACE_STR[f]:
					break
	return GetIBySF(s, f, bFS)

def NotSameColor(s1,s2):
	return SUIT_COLOR[s1]+SUIT_COLOR[s2]==1
#Is card i2 the next face of i1 in FreeCell game
'''def IsNextFCFace(i1,i2):
	return (i1/4+1==i2/4) and (i1<0 or NotSameColor(i1&3, i2&3))
'''
def IsNextFCFace(i1,i2):
	return THIS_FC_CARD[i1]==PREV_FC_CARD[i2]

def IsNextFace(i1,i2):
	if i1>=0:
		return i1+4==i2
	else:
		return i2>=0 and i2<4

class Card:
	def __init__(self, cn, bFS=True):
		#Translate card no to face*4 + suit
		self.suit, self.face = s,f = GetSFByI(cn,bFS)
		self.color, self.cn  = SUIT_COLOR[s], GetIBySF(s,f,True)
		self.rank = f
	def IsNextFace(self,card2):
		return self.face+1==card2.face and (self.suit==-1 or self.suit==card2.suit)
	def IsNextFCFace(self,card2): #for FreeCell
		return self.face+1==card2.face and (self.suit==-1 or self.color!=card2.color)

if __name__ == "__main__":
	print [GetNameByI(i) for i in xrange(52,55)]
	print GetIByName('Jocker - b Liger'),GetIByName('JokerB'),GetIByName('1')

