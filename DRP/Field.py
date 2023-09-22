from Well import Well
from Case import Case

class Field():
    '''Общий класс для различных действий на уровне всех событий'''
    def __init__(self):
        self.base_name = None
        self.wells = {}
    
    def read_data(self, data):
        '''Чтение данных из базы в оперативную память, для быстрой работы'''
        counter = 0
        for row in data:
            if row['well_name'] + ' ' + row['name_of_the_field'] not in self.wells.keys():
                self.wells[row['well_name'] + ' ' + row['name_of_the_field']] = Well()
                self.wells[row['well_name'] + ' ' + row['name_of_the_field']].well_name = row['well_name']
                self.wells[row['well_name'] + ' ' + row['name_of_the_field']].name_of_the_fields = row['name_of_the_field']

            if str(row['case_ID']) not in [case for case in self.wells[row['well_name'] + ' ' + row['name_of_the_field']].cases.keys()]:
                self.wells[row['well_name'] + ' ' + row['name_of_the_field']].cases[str(row['case_ID'])] = Case()
                self.wells[row['well_name'] + ' ' + row['name_of_the_field']].cases[str(row['case_ID'])].case_id = row['case_ID']
                self.wells[row['well_name'] + ' ' + row['name_of_the_field']].cases[str(row['case_ID'])].case_status = row['case_status']
                
            self.wells[row['well_name'] + ' ' + row['name_of_the_field']].cases[str(row['case_ID'])].p_list.append(row['P'])    
            self.wells[row['well_name'] + ' ' + row['name_of_the_field']].cases[str(row['case_ID'])].s_list.append(row['S'])
            self.wells[row['well_name'] + ' ' + row['name_of_the_field']].cases[str(row['case_ID'])].time_list.append(row['date'])
            counter += 1

        
            
            
