import wx
import sqlite3
import os


os.getcwd()
DATABASE = os.getcwd() + '/conpensation.db'
class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        # подключение/создание базы данных
        self.create_db()
        super().__init__(parent, -1, title)

        menubar = wx.MenuBar()
        fileMenu = wx.Menu()

        item = wx.MenuItem(fileMenu, wx.ID_EXIT, "База данных", "Подключение к базе данных")
        fileMenu.Append(item)

        item = wx.MenuItem(fileMenu, wx.ID_EXIT, "Выход", "Выход из программы")
        fileMenu.Append(item)



        menubar.Append(fileMenu, "Меню")
        self.SetMenuBar(menubar)

    def connect_db(self):
        '''Подключение к базе данных'''
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        print(conn)
        return conn

    def create_db(self):
        """Вспомогательная функция для создания таблиц БД"""
        db = self.connect_db()
        with open('sq_db.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        db.close()





app = wx.App()
frame = MyFrame(None, 'Hello World')
frame.Show()
app.MainLoop()