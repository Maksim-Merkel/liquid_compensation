import matplotlib.pyplot as plt

class Case():
    '''Класс описывающий динамограммы'''
    def __init__(self):
        self.case_id = None
        self.s_list = []
        self.p_list = []
        self.time_list = []
        self.case_status = None
    
    def plot_dynamogram(self):
        plt.plot(self.s_list, self.p_list)
        plt.show()