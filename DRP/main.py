import wx
import sqlite3
import os
from BaseSelection import BaseSelection
from Case import Case
import pandas as pd
import datetime as DT 
from Field import Field
from Well import Well

SELECT_BASES = """SELECT base_name FROM bases"""
SELECT_CASES_PER_FIELD = """SELECT * FROM cases WHERE base_name_id = ?"""
INSERT_INTO_CASES = """INSERT INTO cases(case_ID, base_name_id, well_name, name_of_the_field, date, P, S, case_status) 
              VALUES(?,?,?,?,?,?,?,?)"""
ADD_BASE = """INSERT INTO bases (base_name) VALUES (?)"""
FIND_BASE = """SELECT id FROM bases WHERE base_name = ?"""
READ_BASE = """SELECT * FROM cases WHERE base_name_id = ?"""

ID_IMP_T = 1
ID_IMP_D = 2
ID_DB = 3

#print(os.getcwd())
DATABASE = os.getcwd() + '/drp.db'

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        # подключение/создание базы данных 
        self.field = Field()
        self.base_name = None
        self.field_id = None
        #self.base_id = 1
        self.norm_case_counter = 0
        self.accident_counter = 0
        self.db = None
        self.cursor = None
        self.create_db()
        
        super().__init__(parent, -1, title)

        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        #Создание меню
        impMenu = wx.Menu()
        #impMenu.Append(ID_IMP_T, "Импорт траекторий")
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
        #Добавление данных в базу
        self.Bind(wx.EVT_MENU, self.onAdd_new_data, id=ID_IMP_D)

        self.mcd_fields = wx.MultiChoiceDialog(self, "Pick some fruit from\nthis list", "wx.MultiChoiceDialog", list(self.field.wells.keys()))

        self.status_bar = wx.StatusBar(self, id=wx.ID_ANY, style=wx.STB_DEFAULT_STYLE, name=wx.StatusBarNameStr)
        self.status_bar.SetStatusText('Выберите базу данных')

    def history(self, directory):
        '''Загрузка данных в базу'''
        well_list = [well for well in os.listdir(directory) if '.xl' in well]
        print(well_list)
        for well in well_list:
            print(well, end = '. ')
            well_name = well.split()[0]
            xlsx_file = pd.ExcelFile(directory+"/"+well)
            sheet_names = xlsx_file.sheet_names
            print(sheet_names)
            for index, sheet in enumerate(sheet_names):
                if 'Норм' in sheet or 'Норм' in sheet:
                    norm_flaq = True
                else:
                    norm_flaq = False
                self.read_cases_from_excel(directory + '/'+ well, index, norm_flaq, well)
            print('Количество штатных динамограмм: ' + str(self.norm_case_counter) + '. Количество аварийных динамограмм: ' + str(self.accident_counter) + '.')

    def read_cases_from_excel(self, directory, sheet, norm_flaq, well):
        '''Чтение .xl файлов в нужном формате'''

        if 'АСПО' in directory:
            sign = 'АСПО,Эмульсия'
        elif 'Низкая подгонка плунжера' in directory:
            sign = 'Низкая подгонка плунжера'
        elif 'Высокая подгонка или подклинка' in directory:
            sign = 'Низкая подгонка плунжера'
        if norm_flaq:
            sign = 'Штатный режим'

        df = pd.read_excel(directory, sheet_name=sheet)
        df.columns = ['time', 'S', 'P']
        df = df[~df['S'].isna()]
        #df['time']=pd.to_datetime( df['time'] )
        case = Case()
        counter = 1
        #print(counter)

        for index, row in df.iterrows():
            if any(list(row)):
                try:
                    #print(list(row))
                    if type(row[1]) is float:
                        case.s_list.append(list(row)[1])
                    else:
                        case.s_list.append(float(list(row)[1].replace(',', '.')))

                    if type(row[2]) is float:
                        case.p_list.append(list(row)[2])
                    else:
                        case.p_list.append(float(list(row)[2].replace(',', '.')))
                    case.time_list.append(list(row)[0])
                    #print(dt, type(dt))
                    #print(DT.datetime.now(), type(DT.datetime.now()))
                    #print(well.split()[1].split('.')[0])
                    #try:
                    task = (
                                    counter+self.norm_case_counter+self.accident_counter,
                                    self.base_id,
                                    well.split()[0],
                                    well.split()[1].split('.')[0],
                                    str(case.time_list[-1]),
                                    case.p_list[-1],
                                    case.s_list[-1],
                                    sign
                                    )
                        #print(task)
                    self.cursor.execute(INSERT_INTO_CASES, task)

                    #except:
                    #    pass

                except ValueError as e:
                    #print(list(row), index)
                    #if index > 305:
                        #raise e
                    #print(list(row))
                    case = Case()
                    counter += 1
        self.db.commit()
        if norm_flaq:
            self.norm_case_counter += counter
        else:
            self.accident_counter += counter
        
    def onAdd_new_data(self, event):
        '''Добавление данных в базу'''
        # Выбор дирректории
        dlg = wx.DirDialog(self, "Выбор директории...", "D:",
        wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
 
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            print("Выбран каталог: "+dlg.GetPath())
        
        self.history(dlg.GetPath())
        
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

    def data_from_base(self):
        '''Считывание данных в оперативную память из базы, формирование для работы'''
        self.cursor.execute(READ_BASE, (self.field_id,))
        data = self.cursor.fetchall()
        self.field.read_data(data)
        self.field.wells['100 Погребняковское'].cases[148].plot_dynamogram()

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