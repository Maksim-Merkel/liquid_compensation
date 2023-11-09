import wx
import sqlite3
import os
from BaseSelection import BaseSelection
from DeleteCase import DeleteCases
from Case import Case
import pandas as pd
import datetime as DT 
from Field import Field
from Well import Well
from wx.lib.plot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker
import numpy as _Numeric
import random

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC

import matplotlib.pyplot as plt
import seaborn as sns



SELECT_BASES = """SELECT base_name FROM bases"""
SELECT_CASES_PER_FIELD = """SELECT * FROM cases WHERE base_name_id = ?"""
INSERT_INTO_CASES = """INSERT INTO cases(case_ID, base_name_id, well_name, name_of_the_field, date, P, S, case_status) 
              VALUES(?,?,?,?,?,?,?,?)"""
ADD_BASE = """INSERT INTO bases (base_name) VALUES (?)"""
FIND_BASE = """SELECT id FROM bases WHERE base_name = ?"""
READ_BASE = """SELECT * FROM cases WHERE base_name_id = ?"""
DELETE_CASE = """DELETE FROM cases WHERE case_ID = ?"""

ID_IMP_T = 1
ID_IMP_D = 2
ID_DEL_D = 3
ID_DB = 4
ID_SPLIT_SAMPLE = 5

B_ORD = 6
B_NORM_MIN = 7
B_NORM = 8
B_NORM_FIT = 9
B_HYBRID = 10

BOT_CASES = 11
BOT_WELLS = 12

ML_MAX_POOL = 13
ML_MIN_POOL = 14
ML_AVG_POOL = 15
ML_DELTHA_MAX_POOL = 16
ML_DELTHA_MIN_POOL = 17
ML_DELTHA_AVG_POOL = 18

BOT_ML_WELLS = 19
BOT_ML_CLASSIFICATION = 20

DATABASE = os.getcwd() + '/drp.db'



class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        # подключение/создание базы данных 
        self.case_counter = 0
        self.choiced_well = None
        self.choiced_cases = None
        self.random_counter = 0
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
        self.choiced_test_case = {}
        super().__init__(parent, -1, title)

        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        #Создание меню
        impMenu = wx.Menu()
        #impMenu.Append(ID_IMP_T, "Импорт траекторий")
        impMenu.Append(ID_IMP_D, "Импорт истории")
        impMenu.Append(ID_DEL_D, "Удаление событий")
        
        item = wx.MenuItem(fileMenu, ID_DB, "Выбор базы данных", "Подключение к базе данных")
        fileMenu.Append(item)

        fileMenu.AppendSubMenu(impMenu, "&Работа с базой данных")

        item = wx.MenuItem(fileMenu, wx.ID_EXIT, "Выход", "Выход из программы")
        fileMenu.Append(item)

        menubar.Append(fileMenu, "Меню")
        self.SetMenuBar(menubar)
        #Закрытие программы
        self.Bind(wx.EVT_MENU, self.onQuit, id=wx.ID_EXIT)
        #Выбор месторождения
        self.Bind(wx.EVT_MENU, self.onDB, id=ID_DB)
        #Удаление случаев
        self.Bind(wx.EVT_MENU, self.onDel_cases, id=ID_DEL_D)
        #Добавление данных в базу
        self.Bind(wx.EVT_MENU, self.onAdd_new_data, id=ID_IMP_D)

        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetStatusText('Выберите базу данных')

        #Расположение виджетов
        tabs = wx.Notebook(self, id=wx.ID_ANY)
        #3я вкладка --------------------------------------------------------------------------------------------------------------------------
        self.ml_panel = wx.Panel(tabs)
        ml_vbox = wx.BoxSizer(wx.VERTICAL)
        ml_hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        ml_Text_2 = wx.StaticText(self.ml_panel, label="Тестовая выборка", style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.testing_ml_list = wx.ListBox(self.ml_panel, choices=[], style=wx.LB_EXTENDED, name='Тестовая выборка')
        self.testing_ml_list.Bind(wx.EVT_LISTBOX, self.choice_ml_test_case) 

        self.ml_max_pooling = wx.ToggleButton(self.ml_panel, id = ML_MAX_POOL, label='Объединение по максимуму')
        self.ml_min_pooling = wx.ToggleButton(self.ml_panel, id = ML_MIN_POOL, label='Объединение по минимуму')
        self.ml_avg_pooling = wx.ToggleButton(self.ml_panel, id = ML_AVG_POOL, label='Объединение по среднему')
        self.ml_d_max_pooling = wx.ToggleButton(self.ml_panel, id = ML_DELTHA_MAX_POOL, label='Изменение по максимуму')
        self.ml_d_min_pooling = wx.ToggleButton(self.ml_panel, id = ML_DELTHA_MIN_POOL, label='Изменение по минимуму')
        self.ml_d_avg_pooling = wx.ToggleButton(self.ml_panel, id = ML_DELTHA_AVG_POOL, label='Изменение по среднему')
        self.ml_max_pooling.SetValue(True)

        self.ml_max_pooling.Bind(wx.EVT_TOGGLEBUTTON, self.pooling_func)
        self.ml_min_pooling.Bind(wx.EVT_TOGGLEBUTTON, self.pooling_func)         
        self.ml_avg_pooling.Bind(wx.EVT_TOGGLEBUTTON, self.pooling_func)
        self.ml_d_max_pooling.Bind(wx.EVT_TOGGLEBUTTON, self.pooling_func)
        self.ml_d_min_pooling.Bind(wx.EVT_TOGGLEBUTTON, self.pooling_func)         
        self.ml_d_avg_pooling.Bind(wx.EVT_TOGGLEBUTTON, self.pooling_func)
        self.ml_pooling_id = ML_MAX_POOL
        self.ml_choise_wells = wx.Button(self.ml_panel, BOT_ML_WELLS, "Выборка по скважинам")
        self.ml_classification = wx.Button(self.ml_panel, BOT_ML_CLASSIFICATION, "Классификация")

        self.ml_classification.Bind(wx.EVT_BUTTON, self.ml_classification_func)
        self.ml_choise_wells.Bind(wx.EVT_BUTTON, self.alphabet_wells_cases)

        ml_listbox_sizer = wx.BoxSizer(wx.VERTICAL)
        ml_listbox_sizer.Add(ml_Text_2, 0, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(self.testing_ml_list, 1, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(self.ml_choise_wells, 0, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(self.ml_classification, 0, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(wx.StaticLine(self.ml_panel), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
        ml_listbox_sizer.Add(self.ml_max_pooling, 0, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(self.ml_min_pooling, 0, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(self.ml_avg_pooling, 0, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(wx.StaticLine(self.ml_panel), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
        ml_listbox_sizer.Add(self.ml_d_max_pooling, 0, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(self.ml_d_min_pooling, 0, wx.EXPAND, border=10)
        ml_listbox_sizer.Add(self.ml_d_avg_pooling, 0, wx.EXPAND, border=10)

        ml_plotsizer1 = wx.BoxSizer(wx.VERTICAL)
        ml_plotsizer2 = wx.BoxSizer(wx.VERTICAL)
        self.ml_Result_Text1 = wx.StaticText(self.ml_panel, label="", style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.ml_Result_Text2 = wx.StaticText(self.ml_panel, label="", style=wx.ALIGN_CENTRE_HORIZONTAL)
        ml_Text_3 = wx.StaticText(self.ml_panel, label="Штатный режим", style=wx.ALIGN_CENTRE_HORIZONTAL)
        ml_Text_4 = wx.StaticText(self.ml_panel, label="АСПО, Эмульсия", style=wx.ALIGN_CENTRE_HORIZONTAL)
        ml_Text_5 = wx.StaticText(self.ml_panel, label="Высокая подгонка плунжера", style=wx.ALIGN_CENTRE_HORIZONTAL)
        ml_Text_6 = wx.StaticText(self.ml_panel, label="Низкая подгонка плунжера", style=wx.ALIGN_CENTRE_HORIZONTAL)

        self.ml_canvas_shtatplot = PlotCanvas(self.ml_panel)
        self.ml_canvas_ASPOplot = PlotCanvas(self.ml_panel)
        self.ml_canvas_hightplot = PlotCanvas(self.ml_panel)
        self.ml_canvas_lowplot = PlotCanvas(self.ml_panel)

        ml_plotsizer1.Add(ml_Text_3, 0, wx.EXPAND, border=10)
        ml_plotsizer1.Add(self.ml_canvas_shtatplot, 1, wx.EXPAND, border=10)
        ml_plotsizer1.Add(ml_Text_4, 0, wx.EXPAND, border=10)
        ml_plotsizer1.Add(self.ml_canvas_ASPOplot, 1, wx.EXPAND, border=10)
        ml_plotsizer1.Add(self.ml_Result_Text1, 0, wx.EXPAND, border=10)

        ml_plotsizer2.Add(ml_Text_5, 0, wx.EXPAND, border=10)
        ml_plotsizer2.Add(self.ml_canvas_hightplot, 1, wx.EXPAND, border=10)
        ml_plotsizer2.Add(ml_Text_6, 0, wx.EXPAND, border=10)
        ml_plotsizer2.Add(self.ml_canvas_lowplot, 1, wx.EXPAND, border=10)
        ml_plotsizer2.Add(self.ml_Result_Text2, 0, wx.EXPAND, border=10)

        self.canvas_mainplot = PlotCanvas(self.ml_panel)
        ml_hbox1.Add(ml_listbox_sizer, 0, wx.EXPAND, border=10)
        ml_hbox1.Add(ml_plotsizer1, 1, wx.EXPAND, border=10)
        ml_hbox1.Add(ml_plotsizer2, 1, wx.EXPAND, border=10)

        ml_vbox.Add(ml_hbox1, 1, wx.EXPAND|wx.ALL, border=10)
        
        self.ml_panel.SetSizer(ml_vbox)  

        tabs.InsertPage(0, self.ml_panel, "Машинное обучение", select=True)
        #2я вкладка --------------------------------------------------------------------------------------------------------------------------
        self.alphabet_panel = wx.Panel(tabs)
        alphabet_vbox = wx.BoxSizer(wx.VERTICAL)
        alphabet_hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        #alphabet_Text_1 = wx.StaticText(self.alphabet_panel, label="Обучающая выборка", style=wx.ALIGN_CENTRE_HORIZONTAL)
        #self.training_list = wx.ListBox(self.alphabet_panel, choices=[], style=wx.LB_EXTENDED, name='Обучающая выборка')
        alphabet_Text_2 = wx.StaticText(self.alphabet_panel, label="Тестовая выборка", style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.testing_list = wx.ListBox(self.alphabet_panel, choices=[], style=wx.LB_EXTENDED, name='Тестовая выборка')
        self.testing_list.Bind(wx.EVT_LISTBOX, self.choice_alphabet_test_case) 

        self.alphabet_ordinary_symbols = wx.ToggleButton(self.alphabet_panel, id = B_ORD, label='Стандартный алфавит')
        self.alphabet_normed_with_min_symbols = wx.ToggleButton(self.alphabet_panel, id = B_NORM_MIN, label='Алфавит с учетом минимума')
        self.alphabet_normed_symbols = wx.ToggleButton(self.alphabet_panel, id = B_NORM, label='Нормированный алфавит')
        self.alphabet_normed_with_fit = wx.ToggleButton(self.alphabet_panel, id = B_NORM_FIT, label='Нормированный алфавит с подгонкой')
        self.alphabet_hybrid_solution = wx.ToggleButton(self.alphabet_panel, id = B_HYBRID, label='Гибридное решение')
        self.alphabet_hybrid_solution.SetValue(True)
        self.alphabet_normed_flaq = 'HYBRID'
        self.write_results_logs(self.alphabet_normed_flaq)

        self.alphabet_bottom_cases = wx.Button(self.alphabet_panel, BOT_CASES, "Выборка по событиям")
        self.alphabet_bottom_wells = wx.Button(self.alphabet_panel, BOT_WELLS, "Выборка по скважинам")
        self.create_key = 'cases'

        self.alphabet_ordinary_symbols.Bind(wx.EVT_TOGGLEBUTTON, self.alphabet_normed_func)
        self.alphabet_normed_with_min_symbols.Bind(wx.EVT_TOGGLEBUTTON, self.alphabet_normed_func)
        self.alphabet_normed_symbols.Bind(wx.EVT_TOGGLEBUTTON, self.alphabet_normed_func)
        self.alphabet_normed_with_fit.Bind(wx.EVT_TOGGLEBUTTON, self.alphabet_normed_func)         
        self.alphabet_hybrid_solution.Bind(wx.EVT_TOGGLEBUTTON, self.alphabet_normed_func)

        alphabet_listbox_sizer = wx.BoxSizer(wx.VERTICAL)
        #alphabet_listbox_sizer.Add(alphabet_Text_1, 0, wx.EXPAND, border=10)
        #alphabet_listbox_sizer.Add(self.training_list, 1, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(alphabet_Text_2, 0, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(self.testing_list, 1, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(self.alphabet_bottom_cases, 0, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(self.alphabet_bottom_wells, 0, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(wx.StaticLine(self.alphabet_panel), flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
        alphabet_listbox_sizer.Add(self.alphabet_ordinary_symbols, 0, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(self.alphabet_normed_with_min_symbols, 0, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(self.alphabet_normed_symbols, 0, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(self.alphabet_normed_with_fit, 0, wx.EXPAND, border=10)
        alphabet_listbox_sizer.Add(self.alphabet_hybrid_solution, 0, wx.EXPAND, border=10)

        alphabet_plotsizer1 = wx.BoxSizer(wx.VERTICAL)
        alphabet_plotsizer2 = wx.BoxSizer(wx.VERTICAL)
        self.alphabet_Result_Text1 = wx.StaticText(self.alphabet_panel, label="", style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.alphabet_Result_Text2 = wx.StaticText(self.alphabet_panel, label="", style=wx.ALIGN_CENTRE_HORIZONTAL)
        alphabet_Text_3 = wx.StaticText(self.alphabet_panel, label="Штатный режим", style=wx.ALIGN_CENTRE_HORIZONTAL)
        alphabet_Text_4 = wx.StaticText(self.alphabet_panel, label="АСПО, Эмульсия", style=wx.ALIGN_CENTRE_HORIZONTAL)
        alphabet_Text_5 = wx.StaticText(self.alphabet_panel, label="Высокая подгонка плунжера", style=wx.ALIGN_CENTRE_HORIZONTAL)
        alphabet_Text_6 = wx.StaticText(self.alphabet_panel, label="Низкая подгонка плунжера", style=wx.ALIGN_CENTRE_HORIZONTAL)

        self.canvas_shtatplot = PlotCanvas(self.alphabet_panel)
        self.canvas_ASPOplot = PlotCanvas(self.alphabet_panel)
        self.canvas_hightplot = PlotCanvas(self.alphabet_panel)
        self.canvas_lowplot = PlotCanvas(self.alphabet_panel)

        alphabet_plotsizer1.Add(alphabet_Text_3, 0, wx.EXPAND, border=10)
        alphabet_plotsizer1.Add(self.canvas_shtatplot, 1, wx.EXPAND, border=10)
        alphabet_plotsizer1.Add(alphabet_Text_4, 0, wx.EXPAND, border=10)
        alphabet_plotsizer1.Add(self.canvas_ASPOplot, 1, wx.EXPAND, border=10)
        alphabet_plotsizer1.Add(self.alphabet_Result_Text1, 0, wx.EXPAND, border=10)

        alphabet_plotsizer2.Add(alphabet_Text_5, 0, wx.EXPAND, border=10)
        alphabet_plotsizer2.Add(self.canvas_hightplot, 1, wx.EXPAND, border=10)
        alphabet_plotsizer2.Add(alphabet_Text_6, 0, wx.EXPAND, border=10)
        alphabet_plotsizer2.Add(self.canvas_lowplot, 1, wx.EXPAND, border=10)
        alphabet_plotsizer2.Add(self.alphabet_Result_Text2, 0, wx.EXPAND, border=10)

        self.canvas_mainplot = PlotCanvas(self.alphabet_panel)
        alphabet_hbox1.Add(alphabet_listbox_sizer, 0, wx.EXPAND, border=10)
        alphabet_hbox1.Add(alphabet_plotsizer1, 1, wx.EXPAND, border=10)
        alphabet_hbox1.Add(alphabet_plotsizer2, 1, wx.EXPAND, border=10)

        alphabet_vbox.Add(alphabet_hbox1, 1, wx.EXPAND|wx.ALL, border=10)
        
        self.alphabet_panel.SetSizer(alphabet_vbox)        
        tabs.InsertPage(0, self.alphabet_panel, "Алфавит", select=True)

        self.alphabet_bottom_cases.Bind(wx.EVT_BUTTON, self.alphabet_wells_cases)
        self.alphabet_bottom_wells.Bind(wx.EVT_BUTTON, self.alphabet_wells_cases)
        self.create_key = None

        #1я вкладка --------------------------------------------------------------------------------------------------------------------------
        self.database_panel = wx.Panel(tabs)
        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox_well = wx.BoxSizer(wx.VERTICAL)
        vbox_case = wx.BoxSizer(wx.VERTICAL)
        #splitter = wx.SplitterWindow(tabs, wx.ID_ANY, style=wx.SP_LIVE_UPDATE)
        
        #Виджеты 1й вкладки
        self.listbox_wells_text = wx.StaticText(self.database_panel, label="Скважины", style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.listbox_wells = wx.ListBox(self.database_panel, choices=[])
        self.listbox_cases_text = wx.StaticText(self.database_panel, label="События", style=wx.ALIGN_CENTRE_HORIZONTAL)    
        self.listbox_cases = wx.ListBox(self.database_panel, choices=[], style=wx.LB_EXTENDED)
        
        vbox_well.Add(self.listbox_wells_text, 0, wx.EXPAND|wx.ALL)
        vbox_well.Add(self.listbox_wells, 1, wx.EXPAND|wx.ALL)
        vbox_case.Add(self.listbox_cases_text, 0, wx.EXPAND|wx.ALL)
        vbox_case.Add(self.listbox_cases, 1, wx.EXPAND|wx.ALL)
        hbox1.Add(vbox_well, 0, wx.EXPAND|wx.ALL)
        hbox1.Add(vbox_case, 0, wx.EXPAND|wx.LEFT, border=10)

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
 
        hbox1.Add(mainSizer_mainplot, 1, wx.EXPAND|wx.ALL, border=10)
        
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
        hbox1.Add(mainSizer_subplot, 1, wx.EXPAND|wx.ALL)

        vbox.Add(hbox1, 1, wx.EXPAND|wx.ALL, border=10)
        self.database_panel.SetSizer(vbox)

    def ml_classification_func(self, e):
        print('Классификация')
        self.y_keys = {'Штатный режим': 0, 'Высокая подгонка или подклинка': 1, 'Низкая подгонка плунжера': 2, 'АСПО,Эмульсия': 3}
        #clf_model = KNeighborsClassifier(n_neighbors=3)
        
        #best----------------------------------------------------------------
        rf_clf = RandomForestClassifier()
        parameters = {
                'max_depth': list(range(2, 3)), 
                'n_estimators' : list(range(40, 90, 10)), 
                'criterion':['entropy'],  
                'min_samples_split': list(range(2, 5))
                }
                #'max_depth': list(range(2, 5)), 
                #'n_estimators' : list(range(10, 90, 10)), 
                #'criterion':['entropy'],  
                #'min_samples_split': list(range(2, 5))
        clf_model = GridSearchCV(rf_clf, parameters)
        #---------------------------------------------------------------------------
        
        #gb_clf = GradientBoostingClassifier()
        #parameters = {
        #        'n_estimators' : list(range(1, 10, 1)), 
        #        'min_samples_split': list(range(1, 60, 10))
        #        }
        #clf_model = GridSearchCV(gb_clf, parameters)
        #clf_model = SVC()

        X, y = self.create_training_set()
        clf_model.fit(X, y)
        #print(X)
        #print(y)
        data = [X[i] + [y[i]] for i in range(len(X))]
        complication = []
        shtat_complication = []
        ASPO_complication = []
        low_complication = []
        hight_complication = []
        self.choiced_test_case_ml = []
        for key in self.test_cases.keys():
            self.choiced_test_case_ml.append(key)
            test_s, test_p = self.just_pooling(self.test_cases[key])
            areas = self.additional_signs(self.test_cases[key])
            #print(key, test_p, areas)
            pred = clf_model.predict([test_p + areas])[0]
            fact_complication_ind = self.y_keys[self.test_cases[key].case_status]
            fact_complication = self.test_cases[key].case_status
            #МЕГАКОСТЫЛЬ-----------------------------------------------------------------------------------------------
            
            min_p = min(self.test_cases[key].p_list)
            max_p = max(self.test_cases[key].p_list)
            high_p = [(point - min_p)/(max_p-min_p) for point in self.test_cases[key].p_list]

            if 1 in high_p[125:175] and sum(high_p[100:125])/25 < 0.9:
                pred = self.y_keys['Высокая подгонка или подклинка']
                print('Высокая подгонка или подклинка')
            #МЕГАКОСТЫЛЬ-----------------------------------------------------------------------------------------------

            if pred == fact_complication_ind:
                complication.append(True)
                if fact_complication == 'Штатный режим':
                    shtat_complication.append(True)
                elif fact_complication == 'Низкая подгонка плунжера':
                    ASPO_complication.append(True)
                elif fact_complication == 'АСПО,Эмульсия':
                    low_complication.append(True)
                elif fact_complication == 'Высокая подгонка или подклинка':
                    hight_complication.append(True)
            else:
                complication.append(False)
                if fact_complication == 'Штатный режим':
                    shtat_complication.append(False)
                elif fact_complication == 'Низкая подгонка плунжера':
                    low_complication.append(False)
                elif fact_complication == 'АСПО,Эмульсия':
                    ASPO_complication.append(False)
                elif fact_complication == 'Высокая подгонка или подклинка':
                    hight_complication.append(False)
        
        #columns = list(range(len(X[0]))) + ['mode']
        #index = range(len(data))
        #df = pd.DataFrame(data, index, columns)

        #sns.pairplot(df, kind="scatter", hue="mode", plot_kws=dict(s=80, edgecolor="white", linewidth=1))
        #plt.savefig(os.getcwd() + '/Параметры' + '.png')
        #plt.clf()
        
        self.ml_canvas_shtatplot.Draw(self.plot_symbols_for_case('Штатный режим', self.choiced_test_case_ml, complication))
        self.ml_canvas_ASPOplot.Draw(self.plot_symbols_for_case('АСПО,Эмульсия', self.choiced_test_case_ml, complication))
        self.ml_canvas_hightplot.Draw(self.plot_symbols_for_case('Высокая подгонка или подклинка', self.choiced_test_case_ml, complication))
        self.ml_canvas_lowplot.Draw(self.plot_symbols_for_case('Низкая подгонка плунжера', self.choiced_test_case_ml, complication))
            
        all_percent = str(int(sum(complication)/len(complication)*100))
        shtat_percent = self.percent_calculator(shtat_complication)
        ASPO_percent = self.percent_calculator(ASPO_complication)
        low_percent = self.percent_calculator(low_complication)
        hight_percent = self.percent_calculator(hight_complication)

        self.ml_Result_Text1.SetLabel('Доля верно определенных событий: ' + all_percent + '%')
        self.ml_Result_Text2.SetLabel('Штатные: ' + shtat_percent + '.    АСПО: ' + ASPO_percent + '.    Высокая подгонка: ' + hight_percent + '.    Низкая подгонка: ' + low_percent)
        self.ml_Result_Text1.SetExtraStyle(wx.ALIGN_CENTRE_HORIZONTAL)
        self.ml_Result_Text2.SetExtraStyle(wx.ALIGN_CENTRE_HORIZONTAL)

        self.write_results_logs('Доля верно определенных событий:\t' + all_percent + '\tШтатные:\t' + shtat_percent + '\tАСПО:\t' + ASPO_percent + '\tВысокая подгонка:\t' + hight_percent + '\tНизкая подгонка:\t' + low_percent)

    def additional_signs(self, case):
        areas = [0, 0, 0, 0]
        for symbol in self.alphabet.keys():
            if symbol in ['Штатный режим', 'АСПО,Эмульсия']:
                S_symbol = [min(case.p_list[i], self.alphabet[symbol][i]) for i in range(len(case.p_list))]
                if symbol == 'Штатный режим':
                    areas[0] = 2*sum(S_symbol)/(sum(case.p_list) + sum(self.alphabet[symbol]))
    
                if symbol == 'АСПО,Эмульсия':
                    areas[1] = 2*sum(S_symbol)/(sum(case.p_list) + sum(self.alphabet[symbol]))
                    
            else:
                max_S = 0
                for factor in range(int(max(case.p_list)) - 500, int(max(case.p_list)) + 500, 50):
                    S_symbol = [min(case.p_list[i], self.alphabet[symbol][i] * factor) for i in range(len(case.p_list))]
                    if 2*sum(S_symbol)/(sum(case.p_list) + sum([i * factor for i in self.alphabet[symbol]])) > max_S:
                        if symbol == 'Низкая подгонка плунжера':
                            areas[2] = 2*sum(S_symbol)/(sum(case.p_list) + sum([i * factor for i in self.alphabet[symbol]]))
                            
                        if symbol == 'Высокая подгонка или подклинка':
                            areas[3] = 2*sum(S_symbol)/(sum(case.p_list) + sum([i * factor for i in self.alphabet[symbol]]))
                            
        return areas

    def create_training_set(self):
        X = []
        y = []
        count = 30
        for key in self.train_cases.keys():
            test_s, test_p = self.just_pooling(self.train_cases[key])
            test_p += self.additional_signs(self.train_cases[key])
            X.append(test_p)
            y.append(self.y_keys[self.train_cases[key].case_status])
        
        return X, y

    def choice_ml_test_case(self, e):
        self.choiced_test_case = [e.GetEventObject().GetString(case) for case in e.GetEventObject().GetSelections()]
        dict_cases = {}
        for case in self.choiced_test_case:
            if case not in dict_cases.keys():
                dict_cases[case] = self.test_cases[case]

        self.plot_pooling(self.ml_pooling_id, dict_cases)

    def pooling_func(self, e):
        btn = e.GetEventObject()
        self.pooling_flaq = 'MAX' if btn.GetValue() else 0
        id = btn.GetId()

        if id == ML_MAX_POOL:
            self.ml_min_pooling.SetValue(False)
            self.ml_avg_pooling.SetValue(False)
            self.ml_d_max_pooling.SetValue(False)
            self.ml_d_min_pooling.SetValue(False)
            self.ml_d_avg_pooling.SetValue(False) 
        elif id == ML_MIN_POOL:
            self.ml_max_pooling.SetValue(False)
            self.ml_avg_pooling.SetValue(False)
            self.ml_d_max_pooling.SetValue(False)
            self.ml_d_min_pooling.SetValue(False)
            self.ml_d_avg_pooling.SetValue(False)
        elif id == ML_AVG_POOL:
            self.ml_min_pooling.SetValue(False)
            self.ml_max_pooling.SetValue(False)
            self.ml_d_max_pooling.SetValue(False)
            self.ml_d_min_pooling.SetValue(False)
            self.ml_d_avg_pooling.SetValue(False) 
        elif id == ML_DELTHA_MAX_POOL:
            self.ml_min_pooling.SetValue(False)
            self.ml_max_pooling.SetValue(False)
            self.ml_avg_pooling.SetValue(False)
            self.ml_d_min_pooling.SetValue(False)
            self.ml_d_avg_pooling.SetValue(False) 
        elif id == ML_DELTHA_MIN_POOL:
            self.ml_min_pooling.SetValue(False)
            self.ml_max_pooling.SetValue(False)
            self.ml_avg_pooling.SetValue(False)
            self.ml_d_max_pooling.SetValue(False)
            self.ml_d_avg_pooling.SetValue(False) 
        elif id == ML_DELTHA_AVG_POOL:
            self.ml_min_pooling.SetValue(False)
            self.ml_max_pooling.SetValue(False)
            self.ml_avg_pooling.SetValue(False)
            self.ml_d_max_pooling.SetValue(False)
            self.ml_d_min_pooling.SetValue(False)

        self.ml_pooling_id = id
        
        dict_cases = {}
        if self.choiced_test_case:
            for case in self.choiced_test_case:
                if case not in dict_cases.keys():
                    dict_cases[case] = self.test_cases[case]

            self.plot_pooling(self.ml_pooling_id, dict_cases)

    def plot_pooling(self, POOL_ID, case_dict):
        lines_shtat = []
        lines_ASPO = []
        lines_low = []
        lines_hight = []
        count = 30
        for case in case_dict.keys():
            test_s, test_p = self.just_pooling(case_dict[case])

            key = case_dict[case].case_status
            if key == 'Штатный режим':
                lines_shtat.append(PolyLine(list(zip([ind for ind in range(len(test_p))], test_p)), 
                                            legend='Символ штатного режима', colour='green', width=0.1))#, size = 1))

            elif key == 'Низкая подгонка плунжера':
                lines_low.append(PolyLine(list(zip([ind for ind in range(len(test_p))], test_p)), 
                                            legend='Символ низкой подгонки плунженра', colour='blue', width=0.1))#, size = 1))

            elif key == 'АСПО,Эмульсия':
                lines_ASPO.append(PolyLine(list(zip([ind for ind in range(len(test_p))], test_p)), 
                                            legend='Символ АСПО,Эмульсии', colour='red', width=0.1))#, size = 1))

            elif key == 'Высокая подгонка или подклинка':
                lines_hight.append(PolyLine(list(zip([ind for ind in range(len(test_p))], test_p)), 
                                        legend='Символ высокой подгонки или подклинки', colour='black', width=0.1))#, size = 1))
        try:        
            self.ml_canvas_shtatplot.Draw(PlotGraphics(lines_shtat, "", "S", "P"))
        except:
            print('Отсутствуют случаи штатного режима')
        
        try:        
            self.ml_canvas_ASPOplot.Draw(PlotGraphics(lines_ASPO, "", "S", "P"))
        except:
            print('Отсутствуют случаи АСПО')
        
        try:        
            self.ml_canvas_hightplot.Draw(PlotGraphics(lines_hight, "", "S", "P"))
        except:
            print('Отсутствуют случаи Высокой подгонки')
        
        try:        
            self.ml_canvas_lowplot.Draw(PlotGraphics(lines_low, "", "S", "P"))
        except:
            print('Отсутствуют случаи Низкой подгонки')

    def just_pooling(self, case):
        count = 30
        if self.ml_pooling_id == ML_MAX_POOL:
            test_s, test_p = case.max_pooling(count)
        elif self.ml_pooling_id == ML_MIN_POOL:
            test_s, test_p = case.min_pooling(count)
        elif self.ml_pooling_id == ML_AVG_POOL:
            test_s, test_p = case.avg_pooling(count)
            test_s_1, test_p_1 = case.d_avg_pooling(count)
            test_p = test_p + test_p_1
            test_s = test_s + test_s_1
        elif self.ml_pooling_id == ML_DELTHA_MAX_POOL:
            test_s, test_p = case.d_max_pooling(count)
        elif self.ml_pooling_id == ML_DELTHA_MIN_POOL:
            test_s, test_p = case.d_min_pooling(count)
        elif self.ml_pooling_id == ML_DELTHA_AVG_POOL:
            test_s, test_p = case.d_avg_pooling(count)

        return test_s, test_p

    def alphabet_wells_cases(self, e):
        #print('id = ', e.GetEventObject().GetId())
        if e.GetEventObject().GetId() == BOT_WELLS or BOT_ML_WELLS:
            self.create_key = 'wells'
        elif e.GetEventObject().GetId() == BOT_CASES:
            self.create_key = 'cases'
        self.alphabet_create()
        self.alphabet_plot_symbols()
    
    def alphabet_normed_func(self, e):
        btn = e.GetEventObject()
        self.alphabet_normed_flaq = 'ORD' if btn.GetValue() else 0
        id = btn.GetId()
 
        if id == B_ORD:
            self.alphabet_normed_flaq = 'ORD'
            self.alphabet_normed_with_min_symbols.SetValue(False)
            self.alphabet_normed_symbols.SetValue(False)
            self.alphabet_normed_symbols.SetValue(False)
            self.alphabet_normed_with_fit.SetValue(False)
            self.alphabet_hybrid_solution.SetValue(False)
        elif id == B_NORM_MIN:
            self.alphabet_normed_flaq = 'NORM_MIN'
            self.alphabet_ordinary_symbols.SetValue(False)
            self.alphabet_normed_symbols.SetValue(False) 
            self.alphabet_normed_with_fit.SetValue(False)
            self.alphabet_hybrid_solution.SetValue(False)
        elif id == B_NORM:
            self.alphabet_normed_flaq = 'NORM'
            self.alphabet_ordinary_symbols.SetValue(False)
            self.alphabet_normed_with_min_symbols.SetValue(False)
            self.alphabet_normed_with_fit.SetValue(False)
            self.alphabet_hybrid_solution.SetValue(False)
        elif id == B_NORM_FIT:
            self.alphabet_normed_flaq = 'NORM_FIT'
            self.alphabet_ordinary_symbols.SetValue(False)
            self.alphabet_normed_symbols.SetValue(False) 
            self.alphabet_normed_with_min_symbols.SetValue(False)
            self.alphabet_hybrid_solution.SetValue(False)
        elif id == B_HYBRID:
            self.alphabet_normed_flaq = 'HYBRID'
            self.alphabet_ordinary_symbols.SetValue(False)
            self.alphabet_normed_symbols.SetValue(False) 
            self.alphabet_normed_with_min_symbols.SetValue(False)
            self.alphabet_normed_with_fit.SetValue(False)

        self.write_results_logs(self.alphabet_normed_flaq + '\t' + self.create_key)
        self.write_typos_logs(self.alphabet_normed_flaq + '\t' + self.create_key)
        self.alphabet_create()

    def choice_alphabet_test_case(self, e):
        if e:
            self.choiced_test_case = [e.GetEventObject().GetString(case) for case in e.GetEventObject().GetSelections()]
        else:
            self.choiced_test_case = [self.testing_list.GetString(case) for case in self.testing_list.GetSelections()]
        complication = []
        shtat_complication = []
        ASPO_complication = []
        low_complication = []
        hight_complication = []
        self.write_typos_logs('----------------------------------------------------------------------------')
        for case in self.choiced_test_case:
            if self.alphabet_normed_flaq == 'ORD':
                test_p = self.test_cases[case].p_list
            elif self.alphabet_normed_flaq in ['NORM_MIN', 'NORM_FIT']:
                min_p = min(self.test_cases[case].p_list)
                test_p = [p - min_p for p in self.test_cases[case].p_list]
            elif self.alphabet_normed_flaq == 'NORM':
                min_p = min(self.test_cases[case].p_list)
                max_p = max(self.test_cases[case].p_list)
                test_p = [(p - min_p) / (max_p - min_p) for p in self.test_cases[case].p_list]
            elif self.alphabet_normed_flaq == 'HYBRID':
                min_p = min(self.test_cases[case].p_list)
                test_p_ord = self.test_cases[case].p_list
                test_p_fit = [p - min_p for p in self.test_cases[case].p_list]
            
            if self.alphabet_normed_flaq == 'HYBRID':
                max_S = 0
                predict_complication = None
                fact_complication = self.test_cases[case].case_status
                for key in self.alphabet.keys():
                    if key in ['Штатный режим', 'АСПО,Эмульсия']:
                        S_symbol = [min(test_p_ord[i], self.alphabet[key][i]) for i in range(len(test_p_ord))]
                        if 2*sum(S_symbol)/(sum(test_p_ord) + sum(self.alphabet[key])) > max_S:
                            predict_complication = key
                            max_S = 2*sum(S_symbol)/(sum(test_p_ord) + sum(self.alphabet[key]))
                    else:
                        for factor in range(int(max(test_p_fit)) - 500, int(max(test_p_fit)) + 500, 50):
                            S_symbol = [min(test_p_fit[i], self.alphabet[key][i] * factor) for i in range(len(test_p_fit))]
                            if 2*sum(S_symbol)/(sum(test_p_fit) + sum([i * factor for i in self.alphabet[key]])) > max_S:
                                predict_complication = key
                                max_S = 2*sum(S_symbol)/(sum(test_p_fit) + sum([i * factor for i in self.alphabet[key]]))
            elif self.alphabet_normed_flaq == 'NORM_FIT':
                max_S = 0
                predict_complication = None
                fact_complication = self.test_cases[case].case_status
                for factor in range(int(max(test_p)) - 500, int(max(test_p)) + 500, 50):
                    for key in self.alphabet.keys():
                        S_symbol = [min(test_p[i], self.alphabet[key][i] * factor) for i in range(len(test_p))]
                        if 2*sum(S_symbol)/(sum(test_p) + sum([i * factor for i in self.alphabet[key]])) > max_S:
                            predict_complication = key
                            max_S = 2*sum(S_symbol)/(sum(test_p) + sum([i * factor for i in self.alphabet[key]]))
            else:
                max_S = 0
                predict_complication = None
                fact_complication = self.test_cases[case].case_status
                for key in self.alphabet.keys():
                    S_symbol = [min(test_p[i], self.alphabet[key][i]) for i in range(len(test_p))]
                    if 2*sum(S_symbol)/(sum(test_p) + sum(self.alphabet[key])) > max_S:
                        predict_complication = key
                        max_S = 2*sum(S_symbol)/(sum(test_p) + sum(self.alphabet[key]))

            #print('Предполагаемый режим: ', predict_complication, '. Фактический режим: ', fact_complication)
            
            if predict_complication == fact_complication:
                complication.append(True)
                if fact_complication == 'Штатный режим':
                    shtat_complication.append(True)
                elif fact_complication == 'Низкая подгонка плунжера':
                    ASPO_complication.append(True)
                elif fact_complication == 'АСПО,Эмульсия':
                    low_complication.append(True)
                elif fact_complication == 'Высокая подгонка или подклинка':
                    hight_complication.append(True)
            else:
                complication.append(False)
                self.write_typos_logs('Случай\t' + case + '\tФакт\t' + fact_complication + '\tПредсказание\t' + predict_complication)
                
                if fact_complication == 'Штатный режим':
                    shtat_complication.append(False)
                elif fact_complication == 'Низкая подгонка плунжера':
                    low_complication.append(False)
                elif fact_complication == 'АСПО,Эмульсия':
                    ASPO_complication.append(False)
                elif fact_complication == 'Высокая подгонка или подклинка':
                    hight_complication.append(False)

        
        self.canvas_shtatplot.Draw(self.plot_symbols_for_case('Штатный режим', self.choiced_test_case, complication))
        self.canvas_ASPOplot.Draw(self.plot_symbols_for_case('АСПО,Эмульсия', self.choiced_test_case, complication))
        self.canvas_hightplot.Draw(self.plot_symbols_for_case('Высокая подгонка или подклинка', self.choiced_test_case, complication))
        self.canvas_lowplot.Draw(self.plot_symbols_for_case('Низкая подгонка плунжера', self.choiced_test_case, complication))
        if len(self.choiced_test_case) == 1:
            self.alphabet_Result_Text1.SetLabel('Фактический режим:   ' + fact_complication)
            self.alphabet_Result_Text2.SetLabel('Предполагаемый режим:   ' + predict_complication)
            self.alphabet_Result_Text1.SetExtraStyle(wx.ALIGN_CENTRE_HORIZONTAL)
            self.alphabet_Result_Text2.SetExtraStyle(wx.ALIGN_CENTRE_HORIZONTAL)
        else:
            all_percent = str(int(sum(complication)/len(complication)*100))
            shtat_percent = self.percent_calculator(shtat_complication)
            ASPO_percent = self.percent_calculator(ASPO_complication)
            low_percent = self.percent_calculator(low_complication)
            hight_percent = self.percent_calculator(hight_complication)

            self.alphabet_Result_Text1.SetLabel('Доля верно определенных событий: ' + all_percent + '%')
            self.alphabet_Result_Text2.SetLabel('Штатные: ' + shtat_percent + '.    АСПО: ' + ASPO_percent + '.    Высокая подгонка: ' + hight_percent + '.    Низкая подгонка: ' + low_percent)
            self.alphabet_Result_Text1.SetExtraStyle(wx.ALIGN_CENTRE_HORIZONTAL)
            self.alphabet_Result_Text2.SetExtraStyle(wx.ALIGN_CENTRE_HORIZONTAL)

            self.write_results_logs('Доля верно определенных событий:\t' + all_percent + '\tШтатные:\t' + shtat_percent + '\tАСПО:\t' + ASPO_percent + '\tВысокая подгонка:\t' + hight_percent + '\tНизкая подгонка:\t' + low_percent)

    def plot_symbols_for_case(self, key, choiced_test_case, complication):
        if len(self.choiced_test_case) == 1:
            case = self.choiced_test_case[0]
            
            if self.alphabet_normed_flaq == 'ORD':
                test_p = self.test_cases[case].p_list
            elif self.alphabet_normed_flaq == 'NORM_MIN':
                min_p = min(self.test_cases[case].p_list)
                test_p = [p - min_p for p in self.test_cases[case].p_list]
            elif self.alphabet_normed_flaq in ['NORM', 'NORM_FIT']:
                min_p = min(self.test_cases[case].p_list)
                max_p = max(self.test_cases[case].p_list)
                test_p = [(p - min_p) / (max_p - min_p) for p in self.test_cases[case].p_list]
            elif self.alphabet_normed_flaq == 'HYBRID' and key in ['Штатный режим', 'АСПО,Эмульсия']:
                test_p = self.test_cases[case].p_list
            elif self.alphabet_normed_flaq == 'HYBRID' and key in ['Низкая подгонка плунжера', 'Высокая подгонка или подклинка']:    
                min_p = min(self.test_cases[case].p_list)
                max_p = max(self.test_cases[case].p_list)
                test_p = [(p - min_p) / (max_p - min_p) for p in self.test_cases[case].p_list]
                

            lines = []
            if key == 'Штатный режим':
                lines.append(PolyMarker(list(zip([ind for ind in range(len(self.alphabet[key]))], self.alphabet[key])), 
                                        legend='Символ штатного режима', colour='green', width=0.1, size = 0.6))
                lines.append(PolyLine(list(zip([ind for ind in range(len(test_p))], test_p)), 
                                      legend='Фактическое поведение', colour=wx.Colour(100, 200, 250), width=3))

            elif key == 'Низкая подгонка плунжера':
                lines.append(PolyMarker(list(zip([ind for ind in range(len(self.alphabet[key]))], self.alphabet[key])), 
                                        legend='Символ низкой подгонки плунженра', colour='blue', width=0.1, size = 0.6))
                lines.append(PolyLine(list(zip([ind for ind in range(len(test_p))], test_p)), 
                                      legend='Фактическое поведение', colour=wx.Colour(100, 200, 250), width=3))

            elif key == 'АСПО,Эмульсия':
                lines.append(PolyMarker(list(zip([ind for ind in range(len(self.alphabet[key]))], self.alphabet[key])), 
                                        legend='Символ АСПО,Эмульсии', colour='red', width=0.1, size = 0.6))
                lines.append(PolyLine(list(zip([ind for ind in range(len(test_p))], test_p)), 
                                      legend='Фактическое поведение', colour=wx.Colour(100, 200, 250), width=3))

            elif key == 'Высокая подгонка или подклинка':
                lines.append(PolyMarker(list(zip([ind for ind in range(len(self.alphabet[key]))], self.alphabet[key])), 
                                        legend='Символ высокой подгонки или подклинки', width=0.1, size = 0.6))
                lines.append(PolyLine(list(zip([ind for ind in range(len(test_p))], test_p)), 
                                      legend='Фактическое поведение', colour=wx.Colour(100, 200, 250), width=3))

            return PlotGraphics(lines, "", "time", "P")
        else:
            lines = []
            for index, case in enumerate(choiced_test_case):
                if self.test_cases[case].case_status == key:
                    if self.alphabet_normed_flaq == 'ORD':
                        test_p = self.test_cases[case].p_list

                    elif self.alphabet_normed_flaq == 'NORM_MIN':
                        min_p = min(self.test_cases[case].p_list)
                        test_p = [p - min_p for p in self.test_cases[case].p_list]

                    elif self.alphabet_normed_flaq in ['NORM', 'NORM_FIT']:
                        min_p = min(self.test_cases[case].p_list)
                        max_p = max(self.test_cases[case].p_list)
                        test_p = [(p - min_p) / (max_p - min_p) for p in self.test_cases[case].p_list]

                    elif self.alphabet_normed_flaq == 'HYBRID' and key in ['Штатный режим', 'АСПО,Эмульсия']:
                        test_p = self.test_cases[case].p_list

                    elif self.alphabet_normed_flaq == 'HYBRID' and key in ['Низкая подгонка плунжера', 'Высокая подгонка или подклинка']: 
                        min_p = min(self.test_cases[case].p_list)
                        max_p = max(self.test_cases[case].p_list)
                        test_p = [(p - min_p) / (max_p - min_p) for p in self.test_cases[case].p_list]

                    min_s = min(self.test_cases[case].s_list)
                    max_s = max(self.test_cases[case].s_list)
                    test_s = [(s - min_s) / (max_s - min_s) for s in self.test_cases[case].s_list]

                    if complication[index]:
                        lines.append(PolyLine(list(zip(test_s, test_p)), 
                                              legend='Фактическое поведение', colour='green', width=3))
                    else:    
                        lines.append(PolyLine(list(zip(test_s, test_p)), 
                                              legend='Фактическое поведение', colour='red', width=3))
            #if key == 'Штатный режим':
            #    lines.append(PolyMarker(list(zip(test_s, self.alphabet[key])), 
            #                            legend='Символ штатного режима', colour='black', width=0.1, size = 0.6))

            #elif key == 'Низкая подгонка плунжера':
            #    lines.append(PolyMarker(list(zip(test_s, self.alphabet[key])), 
            #                            legend='Символ низкой подгонки плунженра', colour='black', width=0.1, size = 0.6))

            #elif key == 'АСПО,Эмульсия':
            #    lines.append(PolyMarker(list(zip(test_s, self.alphabet[key])), 
            #                            legend='Символ АСПО,Эмульсии', colour='black', width=0.1, size = 0.6))

            #elif key == 'Высокая подгонка или подклинка':
            #    lines.append(PolyMarker(list(zip(test_s, self.alphabet[key])), 
            #                            legend='Символ высокой подгонки или подклинки', colour='black', width=0.1, size = 0.6))
                
            return PlotGraphics(lines, "", "time", "P")
        
    def alphabet_create(self):
        random.seed(self.random_counter)
        self.random_counter += 10
        
        self.all_cases = {}
        shtat_cases = {}
        hight_cases = {}
        low_cases = {}
        ASPO_cases = {}
        if self.create_key == 'cases':
            for well in self.field.wells.keys():
                for case in self.field.wells[well].cases.keys():
                    self.all_cases[well + ' ' + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                    if self.field.wells[well].cases[case].case_status == 'Штатный режим':
                        shtat_cases[well + ' ' + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                    elif self.field.wells[well].cases[case].case_status == 'АСПО,Эмульсия':
                        ASPO_cases[well + ' ' + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                    elif self.field.wells[well].cases[case].case_status == 'Низкая подгонка плунжера':
                        low_cases[well + ' ' + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                    elif self.field.wells[well].cases[case].case_status == 'Высокая подгонка или подклинка':
                        hight_cases[well + ' ' + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
        if self.create_key == 'wells':
            well_ASPO = {}
            well_low = {}
            well_hight = {}
            for well in self.field.wells.keys():
                for case in self.field.wells[well].cases.keys():
                    self.all_cases[well + ' ' + ' ' + str(self.field.wells[well].cases[case].case_id)] = self.field.wells[well].cases[case]
                    if self.field.wells[well].cases[case].case_status == 'АСПО,Эмульсия':
                        if well not in well_ASPO.keys():
                            well_ASPO[well] = self.field.wells[well]
                    elif self.field.wells[well].cases[case].case_status == 'Низкая подгонка плунжера':
                        if well not in well_low.keys():
                            well_low[well] = self.field.wells[well]
                    elif self.field.wells[well].cases[case].case_status == 'Высокая подгонка или подклинка':
                        if well not in well_hight.keys():
                            well_hight[well] = self.field.wells[well]

        self.train_cases = {}
        self.test_cases = {}
        train_shtat_cases = []
        train_hight_cases = []
        train_low_cases = []
        train_ASPO_cases = []
        
        self.trains = [train_shtat_cases, train_hight_cases, train_low_cases, train_ASPO_cases]
        if self.create_key == 'cases':
            for index, case_type in enumerate([shtat_cases, hight_cases, low_cases, ASPO_cases]):
                test_len = len(list(case_type.keys())) // 2
                test_count = 0
                while test_count < test_len:
                    case_name = random.choice(list(case_type.keys()))
                    if case_name not in self.test_cases.keys():
                        self.train_cases[case_name] = case_type[case_name]
                        self.trains[index].append(case_type[case_name])
                        test_count += 1
            
        if self.create_key == 'wells':
            wells_types = [well_hight, well_low, well_ASPO]
            well_list = []
            for index, wells_type in enumerate(wells_types):
                test_len = len(wells_type.keys()) // 2
                train_count = 0
                while train_count < test_len:
                    well_name = random.choice(list(wells_type.keys()))
                    if well_name not in well_list:
                        well_list.append(well_name)
                        for case in wells_type[well_name].cases.keys():
                            if wells_type[well_name].cases[case].case_status == 'Штатный режим':
                                self.train_cases[well_name + ' ' + ' ' + str(wells_type[well_name].cases[case].case_id)] = wells_type[well_name].cases[case]
                                train_shtat_cases.append(wells_type[well_name].cases[case])
                            if wells_type[well_name].cases[case].case_status == 'Высокая подгонка или подклинка':
                                self.train_cases[well_name + ' ' + ' ' + str(wells_type[well_name].cases[case].case_id)] = wells_type[well_name].cases[case]
                                train_hight_cases.append(wells_type[well_name].cases[case])
                            if wells_type[well_name].cases[case].case_status == 'Низкая подгонка плунжера':
                                self.train_cases[well_name + ' ' + ' ' + str(wells_type[well_name].cases[case].case_id)] = wells_type[well_name].cases[case]
                                train_low_cases.append(wells_type[well_name].cases[case])
                            if wells_type[well_name].cases[case].case_status == 'АСПО,Эмульсия':
                                self.train_cases[well_name + ' ' + ' ' + str(wells_type[well_name].cases[case].case_id)] = wells_type[well_name].cases[case]
                                train_ASPO_cases.append(wells_type[well_name].cases[case])
                        
                        train_count += 1

        for case_name in self.all_cases.keys():
                if case_name not in self.train_cases.keys():
                        self.test_cases[case_name] = self.all_cases[case_name]
        print('Длинна тестовой выборки:', len(self.test_cases.keys()))
        
        self.testing_list.Clear()
        self.testing_list.InsertItems(sorted([case for case in list(self.test_cases.keys())]),0)

        self.testing_ml_list.Clear()
        self.testing_ml_list.InsertItems(sorted([case for case in list(self.test_cases.keys())]),0)

    def alphabet_plot_symbols(self):

        self.alphabet = {'Штатный режим': [], 'Высокая подгонка или подклинка': [], 'Низкая подгонка плунжера': [], 'АСПО,Эмульсия': []}

        for index, train in enumerate(self.trains):
            if self.alphabet_normed_flaq == 'ORD':
                symbol = self.create_symbol(train)
            elif self.alphabet_normed_flaq == 'NORM_MIN':
                symbol = self.create_symbol_with_minimum(train)
            elif self.alphabet_normed_flaq in ['NORM', 'NORM_FIT']:
                symbol = self.create_normed_symbol(train)
            elif self.alphabet_normed_flaq == 'HYBRID':
                if index in [0, 3]:
                    symbol = self.create_symbol(train)
                else:
                    symbol = self.create_normed_symbol(train)

            if index == 0:
                self.alphabet['Штатный режим'] = symbol
            elif index == 1:
                self.alphabet['Высокая подгонка или подклинка'] = symbol
            elif index == 2:
                self.alphabet['Низкая подгонка плунжера'] = symbol
            elif index == 3:
                self.alphabet['АСПО,Эмульсия'] = symbol
        
        self.canvas_shtatplot.Draw(self.plot_alphabet('Штатный режим'))
        self.canvas_ASPOplot.Draw(self.plot_alphabet('АСПО,Эмульсия'))
        self.canvas_hightplot.Draw(self.plot_alphabet('Высокая подгонка или подклинка'))
        self.canvas_lowplot.Draw(self.plot_alphabet('Низкая подгонка плунжера'))

    def plot_alphabet(self, key):
        lines = []
        if key == 'Штатный режим':
            lines.append(PolyLine(list(zip([ind for ind in range(len(self.alphabet[key]))], self.alphabet[key])), legend='Штатный режим', colour='green', width=5))
        elif key == 'Низкая подгонка плунжера':
            lines.append(PolyLine(list(zip([ind for ind in range(len(self.alphabet[key]))], self.alphabet[key])), legend='Низкая подгонка плунжера', colour='blue', width=5))
        elif key == 'АСПО,Эмульсия':
            lines.append(PolyLine(list(zip([ind for ind in range(len(self.alphabet[key]))], self.alphabet[key])), legend='АСПО,Эмульсия', colour='red', width=5))
        elif key == 'Высокая подгонка или подклинка':
            lines.append(PolyLine(list(zip([ind for ind in range(len(self.alphabet[key]))], self.alphabet[key])), legend='Высокая подгонка или подклинка', colour='black', width=5))

        return PlotGraphics(lines, "", "time", "P")

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
        self.data_from_base()
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
        counter = self.case_counter + 1
        #print(counter)

        for index, row in df.iterrows():
            if any(list(row)):
                try:
                    #print(list(row))
                    if type(row[1]) in [float, int]:
                        case.s_list.append(list(row)[1])
                    else:
                        case.s_list.append(float(list(row)[1].replace(',', '.')))

                    if type(row[2]) in [float, int]:
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

    def onDel_cases(self, event):
        """Удаление событий"""
        if self.cursor:
            DeleteCases(self, 'Удаление событий').Show()
        else:
            print('База данных неопределена')

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
        self.field = Field()
        self.cursor.execute(READ_BASE, (self.field_id,))
        data = self.cursor.fetchall()
        self.field.read_data(data)
        self.listbox_wells.Clear()
        counter = 0
        for well in self.field.wells.keys():
            for case in self.field.wells[well].cases.keys():
                if self.field.wells[well].cases[case].case_id > counter:
                    counter = self.field.wells[well].cases[case].case_id
        self.case_counter = counter
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

    @staticmethod
    def write_results_logs(str):
        with open(os.getcwd() + r'\result_logs.txt', 'a') as logs_file:
            print(str, file=logs_file)

    @staticmethod
    def write_typos_logs(str):
        with open(os.getcwd() + r'\typos_logs.txt', 'a') as logs_file:
            print(str, file=logs_file)

    @staticmethod
    def create_symbol(test):
        p = [0] * len(test[0].p_list) 
        for case in test:
            for ind in range(len(case.p_list)):
                p[ind] += case.p_list[ind]
        
        return [i / len(test) for i in p]

    @staticmethod
    def create_symbol_with_minimum(test):
        p = [0] * len(test[0].p_list) 
        for case in test:
            min_p = min(case.p_list)
            for ind in range(len(case.p_list)):
                p[ind] += case.p_list[ind] - min_p
                
        return [i / len(test) for i in p]

    @staticmethod
    def create_normed_symbol(test):
        p = [0] * len(test[0].p_list) 
        for case in test:
            for ind in range(len(case.p_list)):
                p[ind] += case.p_list[ind]
        min_p = min(p)
        max_p = max(p)
        
        return [(i - min_p) / (max_p - min_p) for i in p]

    @staticmethod
    def percent_calculator(complication):
        if complication:
            return  str(int(sum(complication)/len(complication)*100))
        else:
            return 'Нет'

    

app = wx.App()
frame = MyFrame(None, 'РС к ШГН')
frame.Show()
app.MainLoop()
frame.db.close()