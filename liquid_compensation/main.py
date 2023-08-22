import wx
import sqlite3
import os
from BaseSelection import BaseSelection

SELECT_BASES = """SELECT base_name from bases"""

ID_IMP_T = 1
ID_IMP_D = 2
ID_DB = 3

os.getcwd()
DATABASE = os.getcwd() + '/conpensation.db'
class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        # подключение/создание базы данных
        self.db = None
        self.cursor = None
        self.create_db()
        super().__init__(parent, -1, title)

        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        #Создание меню
        impMenu = wx.Menu()
        impMenu.Append(ID_IMP_T, "Импорт траекторий")
        impMenu.Append(ID_IMP_D, "Импорт истории")


        item = wx.MenuItem(fileMenu, ID_DB, "База данных", "Подключение к базе данных")
        fileMenu.Append(item)

        fileMenu.AppendSubMenu(impMenu, "&Импорт")

        item = wx.MenuItem(fileMenu, wx.ID_EXIT, "Выход", "Выход из программы")
        fileMenu.Append(item)

        menubar.Append(fileMenu, "Меню")
        self.SetMenuBar(menubar)
        #Закрытие программы
        self.Bind(wx.EVT_MENU, self.onQuit, id=wx.ID_EXIT)
        #Выбор месторождения
        self.Bind(wx.EVT_MENU, self.onDB, id=ID_DB)

    def onQuit(self, event):
        self.Close()

    def onDB(self, event):
        """Выбор месторождения"""
        if self.cursor:
            bases = self.cursor.execute(SELECT_BASES)
            combolist = []
            for row in bases:
                combolist.append(row[0])
            BaseSelection(self, "Выбор базы данных", combolist).Show()
        else:
            print('База данных неопределена')
    def connect_db(self):
        '''Подключение к базе данных'''
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

    def create_db(self):
        """Вспомогательная функция для создания таблиц БД"""
        self.db = self.connect_db()
        with open('sq_db.sql', mode='r') as f:
            self.db.cursor().executescript(f.read())
        self.db.commit()
        self.cursor = self.db.cursor()





app = wx.App()
frame = MyFrame(None, 'Hello World')
frame.Show()
app.MainLoop()
frame.db.close()