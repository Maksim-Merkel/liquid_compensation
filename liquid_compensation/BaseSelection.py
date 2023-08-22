import wx
ID_CB = 1
ID_BTN_CHOICE = 2
ID_BTN_NEW = 3
class BaseSelection(wx.Frame):
    def __init__(self, parent, title, combolist):
        super().__init__(parent, -1, title)

        self.base = None

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        bases_combo = wx.ComboBox(panel, ID_CB, value="", choices=combolist)
        vbox.Add(bases_combo, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        btn1 = wx.Button(panel, label="Выбрать базу")
        btn2 = wx.Button(panel, label="Добавить базу")
        hbox1.Add(btn1, proportion=1, flag=wx.LEFT | wx.BOTTOM, border=10)
        hbox1.Add(btn2, proportion=1, flag=wx.RIGHT | wx.BOTTOM, border=10)
        vbox.Add(hbox1, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        panel.SetSizer(vbox)


        btn1.Bind(wx.EVT_BUTTON, self.onBtn_choice)
        btn2.Bind(wx.EVT_BUTTON, self.onBtn_new)
        #print(combolist)

    def onBtn_choice(self, e):
        print(1)

    def onBtn_new(self, e):
        print(2)


app = wx.App()
frame = BaseSelection(None, 'Hello World', ['Тест', 'Хуест'])
frame.Show()
app.MainLoop()
frame.db.close()