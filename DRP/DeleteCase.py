import wx

ID_DEL_BOT = 201

DELETE_CASE = """DELETE FROM cases WHERE case_ID = ?"""

class DeleteCases(wx.Frame):
    def __init__(self, parent,title):
        super().__init__(parent, -1, title)
        self.cases = {}
        for well in self.Parent.field.wells.keys():
            for case in self.Parent.field.wells[well].cases.keys():
                self.cases[well + ' ' + self.Parent.field.wells[well].name_of_the_fields + ' ' + str(case)] = self.Parent.field.wells[well].cases[case]

        self.panel = wx.Panel(self)
        Text_1 = wx.StaticText(self.panel, label="Выберите события для удаления", style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.hit_list = wx.ListBox(self.panel, choices=list(self.cases.keys()), style=wx.LB_EXTENDED, name='hit_list')
        del_bottom = wx.Button(self.panel, ID_DEL_BOT, "Удалить")
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(Text_1, 0, wx.EXPAND|wx.ALL, border=10)
        vbox.Add(self.hit_list, 1, wx.EXPAND|wx.ALL, border=10)
        vbox.Add(del_bottom, 0, wx.EXPAND|wx.ALL, border=10)
        self.panel.SetSizer(vbox)
        del_bottom.Bind(wx.EVT_BUTTON, self.del_cases)

    def del_cases(self, e):
        choiced_cases = [self.hit_list.GetString(case) for case in self.hit_list.GetSelections()]
        print(choiced_cases)
        print([self.cases[case].case_id for case in choiced_cases])
        for case_id in [self.cases[case].case_id for case in choiced_cases]:
            self.Parent.cursor.execute(DELETE_CASE, (case_id,))
        self.Parent.db.commit()
        self.Parent.data_from_base()

        self.cases = {}
        for well in self.Parent.field.wells.keys():
            for case in self.Parent.field.wells[well].cases.keys():
                self.cases[well + ' ' + self.Parent.field.wells[well].name_of_the_fields + ' ' + str(case)] = self.Parent.field.wells[well].cases[case]

        self.hit_list.InsertItems(list(self.cases.keys()),0)