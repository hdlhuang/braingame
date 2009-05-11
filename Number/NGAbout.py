# -*- coding: gbk -*-
import sys

import wx
import wx.html
import wx.lib.wxpTag

#---------------------------------------------------------------------------

class NGAboutBox(wx.Dialog):

    NGOverview = """<html><body>
<h2><center>Number Game</center></h2>
填数字游戏规则：
九行九列共八十一格，分成九个三乘三的九宫格
需要将一到九数字填入八十一格中，使得每行每列
和每个九宫中包含一到九所有数字。

This is a game to enter numbers from 1 to 9.
It has one board which has 9 rows and 9 columns. Total 81 squares.
Rows and columns are using index 0 to 8
The board is also divided into 9 regions, each region has 3 rows and 3 columns.
region=[startRow,endRow,startColumn,endColumn]
9 regions are
<center>
<p>[0,2,0,2],[0,2,3,5],[0,2,5,8]
<p>[3,5,0,2],[3,5,3,5],[3,5,5,8]
<p>[5,8,0,2],[5,8,3,5],[5,8,5,8]
</center>
The game rule is simple:
Each number must appear in rows,columns and regions once.

<font color="#0f67ae">
<h4>Additional shortcut keys:</h4>
<ul>
<li>Move cursor: i,j,k,l,space</li>
<li>Enter number: 1,2,..9</li>
<li>Delete number: d,backspace</li>
<li>Highlight number: ,.</li>
</ul>
</font>

<center>
<p>Platform: %s</p>
<p>Python verion: %s</p>
<p><b>Written by highlertech@gmail.com</p></b>
<p><wxp module="wx" class="Button">
    <param name="label" value="Okay">
    <param name="id"    value="ID_OK">
</wxp></p>
</center>
</body></html>
"""
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About The Number Game',)
        html = wx.html.HtmlWindow(self, -1, size=(420, -1))
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()
        py_version = sys.version.split()[0]
        txt = self.NGOverview % (", ".join(wx.PlatformInfo[1:]),py_version)
        html.SetPage(txt)
        btn = html.FindWindowById(wx.ID_OK)
        ir = html.GetInternalRepresentation()
        html.SetSize( (ir.GetWidth()+25, ir.GetHeight()+25) )
        self.SetClientSize(html.GetSize())
        self.CentreOnParent(wx.BOTH)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    dlg = NGAboutBox(None)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
