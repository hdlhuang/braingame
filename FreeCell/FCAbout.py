# -*- coding: gbk -*-
import sys

import wx
import wx.html
import wx.lib.wxpTag

#---------------------------------------------------------------------------

class FCAboutBox(wx.Dialog):

    FCOverview = """<html><body>
<h2><center>FreeCell Game</center></h2>
空档接龙游戏规则：
五十二张牌分布在八列，左上四格为空格，右上四格为目标格
需把所有牌由小到大分花色移动到目标格
移动规则:
每个空位可以放一张牌
列续接，当一列有牌时，只有异色且牌面小一的牌可以续接
空列可以放任何牌
快捷键(不分大小写)
<center>
<p>Q 下局, W 上局, E 快存, R 快读
<p>A 起始, S 上步, D 下步, F 最后
<p>Z 存解, X 读解, C 下局, V 重玩 
<p>Platform: %s</p>
<p>Python verion: %s</p>
<p><b>Written by Lei Huang highlertech@gmail.com</p></b>
<p><wxp module="wx" class="Button">
    <param name="label" value="Okay">
    <param name="id"    value="ID_OK">
</wxp></p>
</center>
</body></html>
"""
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About The FreeCell Game',)
        html = wx.html.HtmlWindow(self, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()
        py_version = sys.version.split()[0]
        txt = self.FCOverview % (", ".join(wx.PlatformInfo[1:]),py_version)
        html.SetPage(txt)
        btn = html.FindWindowById(wx.ID_OK)
        ir = html.GetInternalRepresentation()
        html.SetSize( (ir.GetWidth()+25, ir.GetHeight()+25) )
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    dlg = FCAboutBox(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
