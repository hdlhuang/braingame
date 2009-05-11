# -*- coding: gbk -*-
import sys

import wx
import wx.html
import wx.lib.wxpTag

#---------------------------------------------------------------------------

class FCAboutBox(wx.Dialog):

    FCOverview = """<html><body>
<h2><center>FreeCell Game</center></h2>
�յ�������Ϸ����
��ʮ�����Ʒֲ��ڰ��У������ĸ�Ϊ�ո������ĸ�ΪĿ���
�����������С����ֻ�ɫ�ƶ���Ŀ���
�ƶ�����:
ÿ����λ���Է�һ����
�����ӣ���һ������ʱ��ֻ����ɫ������Сһ���ƿ�������
���п��Է��κ���
��ݼ�(���ִ�Сд)
<center>
<p>Q �¾�, W �Ͼ�, E ���, R ���
<p>A ��ʼ, S �ϲ�, D �²�, F ���
<p>Z ���, X ����, C �¾�, V ���� 
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
