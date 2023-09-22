import wx
import sqlite3
import os
from BaseSelection import BaseSelection
from Case import Case
import pandas as pd
import datetime as DT 
from Field import Field
from Well import Well
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker
import numpy as _Numeric
import random

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
ID_SPLIT_SAMPLE = 4

#print(os.getcwd())
DATABASE = os.getcwd() + '/drp.db'



class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        # подключение/создание базы данных 
        self.choiced_well = None
        self.choiced_cases = None

        self.field = Field()
        self.base_name = None
        self.field_id = None
        #self.base_id = 1
        self.norm_case_counter = 0
        self.accident_counter = 0
        self.db = None
        self.cursor = None
        self.create_db()
        #self.SetMinSize((250, 150))

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



        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetStatusText('Выберите базу данных')

        #Расположение виджетов
        tabs = wx.Notebook(self, id=wx.ID_ANY)

        #2я вкладка --------------------------------------------------------------------------------------------------------------------------
        self.alphabet_panel = wx.Panel(tabs)
        alphabet_vbox = wx.BoxSizer(wx.VERTICAL)
        alphabet_hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.training_list = wx.ListBox(self.alphabet_panel, choices=[], style=wx.LB_EXTENDED)
        self.testing_list = wx.ListBox(self.alphabet_panel, choices=[], style=wx.LB_EXTENDED)
        self.alphabet_bottom = wx.Button(self.alphabet_panel, ID_SPLIT_SAMPLE, "Сформировать выборки")

        alphabet_listbox_sizer = wx.BoxSizer(wx.VERTICAL)
        alphabet_listbox_sizer.Add(self.training_list, 1, wx.EXPAND)
        alphabet_listbox_sizer.Add(self.testing_list, 1, wx.EXPAND)

        alphabet_bottoms_sizer = wx.BoxSizer(wx.HORIZONTAL)
        alphabet_bottoms_sizer.Add(self.alphabet_bottom, 0, wx.EXPAND)
        alphabet_listbox_sizer.Add(alphabet_bottoms_sizer, 0, wx.EXPAND)

        alphabet_plotsizer1 = wx.BoxSizer(wx.VERTICAL)
        alphabet_plotsizer2 = wx.BoxSizer(wx.VERTICAL)

        self.canvas_shtatplot = PlotCanvas(self.alphabet_panel)
        self.canvas_ASPOplot = PlotCanvas(self.alphabet_panel)
        self.canvas_hightplot = PlotCanvas(self.alphabet_panel)
        self.canvas_lowplot = PlotCanvas(self.alphabet_panel)

        alphabet_plotsizer1.Add(self.canvas_shtatplot, 1, wx.EXPAND)
        alphabet_plotsizer1.Add(self.canvas_ASPOplot, 1, wx.EXPAND)
        alphabet_plotsizer2.Add(self.canvas_hightplot, 1, wx.EXPAND)
        alphabet_plotsizer2.Add(self.canvas_lowplot, 1, wx.EXPAND)

        self.canvas_mainplot = PlotCanvas(self.alphabet_panel)
        alphabet_hbox1.Add(alphabet_listbox_sizer, 0, wx.EXPAND)
        alphabet_hbox1.Add(alphabet_plotsizer1, 0, wx.EXPAND)
        alphabet_hbox1.Add(alphabet_plotsizer2, 0, wx.EXPAND)

        alphabet_vbox.Add(alphabet_hbox1, 1, wx.EXPAND)
        
        self.alphabet_panel.SetSizer(alphabet_vbox)        
        tabs.InsertPage(0, self.alphabet_panel, "Алфавит", select=True)

        self.alphabet_bottom.Bind(wx.EVT_BUTTON, self.alphabet_create)

        #1я вкладка --------------------------------------------------------------------------------------------------------------------------
        self.database_panel = wx.Panel(tabs)
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        #splitter = wx.SplitterWindow(tabs, wx.ID_ANY, style=wx.SP_LIVE_UPDATE)
        
        #Виджеты 1й вкладки
        self.listbox_wells = wx.ListBox(self.database_panel, choices=[])

        self.listbox_cases = wx.ListBox(self.database_panel, choices=[], style=wx.LB_EXTENDED)
        hbox1.Add(self.listbox_wells, 0, wx.EXPAND)
        hbox1.Add(self.listbox_cases, 0, wx.EXPAND)

        #_mainplot
        mainSizer_mainplot = wx.BoxSizer(wx.VERTICAL)
        checkSizer_mainplot = wx.BoxSizer(wx.HORIZONTAL)
        self.canvas_mainplot = PlotCanvas(self.database_panel)
        self.toggleGrid = wx.CheckBox(self.database_panel, label="Отображать сетку")
        self.toggleGrid.Bind(wx.EVT_CHECKBOX, self.onToggleGrid)
        self.toggleLegend = wx.CheckBox(self.database_panel, label="Отображать легенду")
        self.toggleLegend.Bind(wx.EVT_CHECKBOX, self.onToggleLegend)
        self.toggleNormed = wx.CheckBox(self.database_panel, label="Нормировка")
        self.toggleNormed.Bind(wx.EVT_CHECKBOX, self.onToggleNormed)
        self.toggleCustomNormed = wx.CheckBox(self.database_panel, label="Кастомная нормировка")
        self.toggleCustomNormed.Bind(wx.EVT_CHECKBOX, self.onToggleCustomNormed)

        # Размещаем виджеты
        mainSizer_mainplot.Add(self.canvas_mainplot, 1, wx.EXPAND)
        checkSizer_mainplot.Add(self.toggleGrid, 0, wx.ALL, 5)
        checkSizer_mainplot.Add(self.toggleLegend, 0, wx.ALL, 5)
        checkSizer_mainplot.Add(self.toggleNormed, 0, wx.ALL, 5)
        checkSizer_mainplot.Add(self.toggleCustomNormed, 0, wx.ALL, 5)
        mainSizer_mainplot.Add(checkSizer_mainplot)
 
        hbox1.Add(mainSizer_mainplot, 1, wx.EXPAND)
        
        

        tabs.InsertPage(0, self.database_panel, "База данных", select=True)

        #Выбор скважины
        self.listbox_wells.Bind(wx.EVT_LISTBOX, self.database_choice_well)

        #Выбор динамограммы
        self.listbox_cases.Bind(wx.EVT_LISTBOX, self.database_choice_case)    

        #_subplots
        mainSizer_subplot = wx.BoxSizer(wx.VERTICAL)
        self.canvas_subplot_1 = PlotCanvas(self.database_panel)
        self.canvas_subplot_2 = PlotCanvas(self.database_panel)

        # Размещаем виджеты
        mainSizer_subplot.Add(self.canvas_subplot_1, 1, wx.EXPAND)
        mainSizer_subplot.Add(self.canvas_subplot_2, 1, wx.EXPAND)
        hbox1.Add(mainSizer_subplot, 1, wx.EXPAND)

        vbox.Add(hbox1, 1, wx.EXPAND)
        self.database_panel.SetSizer(vbox)
        
    def alphabet_create(self, e):
        self.all_cases = {}
        shtat_cases = {}
        hight_cases = {}
        low_cases = {}
        ASPO_cases = {}
        for well in self.field.wells.keys():
            for case in self.field.wells[well].cases.keys():
                self.all_cases[well + ' ' + self.field.wells[well].name_of_the_fields + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                if self.field.wells[well].cases[case].case_status == 'Штатный режим':
                    shtat_cases[well + ' ' + self.field.wells[well].name_of_the_fields + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                elif self.field.wells[well].cases[case].case_status == 'АСПО,Эмульсия':
                    ASPO_cases[well + ' ' + self.field.wells[well].name_of_the_fields + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                elif self.field.wells[well].cases[case].case_status == 'Низкая подгонка плунжера':
                    low_cases[well + ' ' + self.field.wells[well].name_of_the_fields + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                elif self.field.wells[well].cases[case].case_status == 'Высокая подгонка или подклинка':
                    hight_cases[well + ' ' + self.field.wells[well].name_of_the_fields + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]


        self.train_cases = {}
        self.test_cases = {}
        for case_type in [shtat_cases, hight_cases, low_cases, ASPO_cases]:
            test_len = len(list(case_type.keys())) // 2
            test_count = 0
            while test_count < test_len:
                case_name = random.choice(list(case_type.keys()))
                if case_name not in self.test_cases.keys():
                    self.test_cases[case_name] = case_type[case_name]
                    test_count += 1
        for case_name in self.all_cases.keys():
            if case_name not in self.test_cases.keys():
                    self.train_cases[case_name] = self.all_cases[case_name]

        print('train: ', list(self.train_cases.keys())[:10], len(list(self.train_cases.keys())))
        print('test: ', list(self.test_cases.keys())[:10], len(list(self.test_cases.keys())))
        
        self.training_list.InsertItems(sorted([case for case in list(self.train_cases.keys())]),0)
        self.testing_list.InsertItems(sorted([case for case in list(self.test_cases.keys())]),0)



    def database_choice_case(self, e):
        self.choiced_cases = [e.GetEventObject().GetString(case) for case in e.GetEventObject().GetSelections()]
        self.canvas_mainplot.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, self.toggleNormed.IsChecked(), "all", self.toggleCustomNormed.IsChecked()))
        self.canvas_subplot_1.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, self.toggleNormed.IsChecked(), "P", self.toggleCustomNormed.IsChecked()))
        self.canvas_subplot_2.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, self.toggleNormed.IsChecked(), "S", self.toggleCustomNormed.IsChecked()))

    def database_choice_well(self, e):
        self.choiced_well = e.GetEventObject().GetString(e.GetEventObject().GetSelection())
        self.listbox_cases.Clear()
        self.listbox_cases.InsertItems([str(case) for case in self.field.wells[self.choiced_well].cases.keys()],0)

    def onToggleCustomNormed(self, event):
        self.canvas_mainplot.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, self.toggleNormed.IsChecked(), "all", event.IsChecked()))
        self.canvas_subplot_1.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, self.toggleNormed.IsChecked(), "P", event.IsChecked()))
        self.canvas_subplot_2.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, self.toggleNormed.IsChecked(), "S", event.IsChecked()))

    def onToggleNormed(self, event):
        self.canvas_mainplot.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, event.IsChecked(), "all", self.toggleCustomNormed.IsChecked()))
        self.canvas_subplot_1.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, event.IsChecked(), "P", self.toggleCustomNormed.IsChecked()))
        self.canvas_subplot_2.Draw(self.plot_dynamogram_mainplot(self.choiced_well, self.choiced_cases, event.IsChecked(), "S", self.toggleCustomNormed.IsChecked()))

    def onToggleGrid(self, event):
        """"""
        self.canvas_mainplot.SetEnableGrid(event.IsChecked())
        self.canvas_subplot_1.SetEnableGrid(event.IsChecked())
        self.canvas_subplot_2.SetEnableGrid(event.IsChecked())
 
    def onToggleLegend(self, event):
        """"""
        self.canvas_mainplot.SetEnableLegend(event.IsChecked())

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
        self.listbox_wells.Clear()
        self.listbox_wells.InsertItems([well for well in self.field.wells.keys()],0)

    def read_cases_from_excel(self, directory, sheet, norm_flaq, well):
        '''Чтение .xl файлов в нужном формате'''

        if 'АСПО' in directory:
            sign = 'АСПО,Эмульсия'
        elif 'Низкая подгонка плунжера' in directory:
            sign = 'Низкая подгонка плунжера'
        elif 'Высокая подгонка или подклинка' in directory:
            sign = 'Высокая подгонка или подклинка'
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
                                    self.field_id,
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
        print(2)
        self.cursor.execute(READ_BASE, (self.field_id,))
        data = self.cursor.fetchall()
        self.field.read_data(data)
        self.listbox_wells.Clear()
        self.listbox_wells.InsertItems([well for well in self.field.wells.keys()],0)

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

    def plot_dynamogram_mainplot(self, well, cases, normalize, key, custom):
        # Отрисовка динамограмм из базы
        lines = []
        for case in cases:
            case_data = self.field.wells[well].cases[case]
            if custom:
                s_max = max(case_data.s_list)
                s_min = min(case_data.s_list)
                s = [(s - s_min)/(s_max - s_min) for s in case_data.s_list]
                p_max = max(case_data.p_list)
                p_min = min(case_data.p_list)
                p = [p - p_min for p in case_data.p_list]
            elif normalize:
                s_max = max(case_data.s_list)
                s_min = min(case_data.s_list)
                s = [(s - s_min)/(s_max - s_min) for s in case_data.s_list]
                p_max = max(case_data.p_list)
                p_min = min(case_data.p_list)
                p = [(p - p_min)/(p_max - p_min) for p in case_data.p_list]
            else:
                s = case_data.s_list
                p = case_data.p_list

            if key == "S":
                dynamogram = list(zip([ind for ind in range(len(s))], s))
            elif key == "P":
                dynamogram = list(zip([ind for ind in range(len(p))], p))
            else:
                dynamogram = list(zip(s, p))
            
            if case_data.case_status == 'Штатный режим':
                lines.append(PolyLine(dynamogram, legend='Штатный режим', colour='green', width=5))
            elif case_data.case_status == 'Низкая подгонка плунжера':
                lines.append(PolyLine(dynamogram, legend='Низкая подгонка плунжера', colour='blue', width=5))
            elif case_data.case_status == 'АСПО,Эмульсия':
                lines.append(PolyLine(dynamogram, legend='АСПО,Эмульсия', colour='red', width=5))
            elif case_data.case_status == 'Высокая подгонка или подклинка':
                lines.append(PolyLine(dynamogram, legend='Высокая подгонка или подклинка', colour='black', width=5))

        if key == "S":
            return PlotGraphics(lines, "", "time", "S")
        elif key == "P":
            return PlotGraphics(lines, "", "time", "P")
        else:
            return PlotGraphics(lines, well + "   " + str(cases), "S", "P")

    


app = wx.App()
frame = MyFrame(None, 'РС к ШГН')
frame.Show()
app.MainLoop()
frame.db.close()