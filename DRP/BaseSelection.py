import wx
ID_CB = 111
ID_BTN_CHOICE = 112
ID_BTN_NEW = 113

FIND_BASE = """SELECT id FROM bases WHERE base_name = ?"""
ADD_BASE = """INSERT INTO bases (base_name) VALUES (?);"""

class BaseSelection(wx.Frame):
    def __init__(self, parent, title, combolist):
        super().__init__(parent, -1, title)
        self.SetSize(400, 120)
        self.base = None
        self.combolist = combolist

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.bases_combo = wx.ComboBox(panel, ID_CB, value="", choices=combolist)
        vbox.Add(self.bases_combo, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        btn1 = wx.Button(panel, label="Выбрать базу")
        btn2 = wx.Button(panel, label="Добавить базу")
        hbox1.Add(btn1, proportion=1)
        hbox1.Add(btn2, proportion=1)
        vbox.Add(hbox1, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        panel.SetSizer(vbox)

        self.bases_combo.Bind(wx.EVT_COMBOBOX, self.OnCombo)
        btn1.Bind(wx.EVT_BUTTON, self.onBtn_choice)
        btn2.Bind(wx.EVT_BUTTON, self.onBtn_new)
        #print(combolist)

    def OnCombo(self, e):
        self.base = self.bases_combo.GetValue()

    def onBtn_choice(self, e):
        self.Parent.base = self.base
        print(self.Parent.base)
        self.onQuit()
        self.Parent.cursor.execute(FIND_BASE, (self.Parent.base,))
        self.Parent.field_id = self.Parent.cursor.fetchone()[0]
        print(self.Parent.field_id)
        self.Parent.status_bar.SetStatusText(self.Parent.base)
        self.Parent.data_from_base()

    def onBtn_new(self, e):
        self.Parent.base = self.bases_combo.GetValue()
        print(self.Parent.base)
        self.onQuit()
        if self.Parent.base not in self.combolist and self.Parent.base:
            self.Parent.cursor.execute(ADD_BASE, (self.Parent.base,))
            self.Parent.db.commit()
            print('Добавлена новая база: ', self.Parent.base)
        self.Parent.cursor.execute(FIND_BASE, (self.Parent.base,))
        self.Parent.field_id = self.Parent.cursor.fetchone()[0]
        print(self.Parent.field_id)
        self.Parent.status_bar.SetStatusText(self.Parent.base)
        self.Parent.data_from_base()

    def onQuit(self):
        self.Close()

if __name__ == 'main':
    app = wx.App()
    frame = BaseSelection(None, 'Hello World', ['Тест', 'Хуест'])
    frame.Show()
    app.MainLoop()
    frame.db.close()