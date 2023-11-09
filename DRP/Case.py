import matplotlib.pyplot as plt
from math import inf

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

    def max_pooling(self, count):
        p = []
        s = []
        steps = round(len(self.p_list) / count)
        #for step in range(steps):
        #    max_p = -inf
        #    if step < steps - 1:
        #        for index, p_now in enumerate(self.p_list[0 + step * count: count + (step + 1) * count]):
        #            if p_now > max_p:
        #                max_p = p_now
        #                max_s = self.s_list[index + step * count]
        #    else:
        #        for index, p_now in enumerate(self.p_list[0 + step * count:]):  
        #            if p_now > max_p:
        #                max_p = p_now
        #                max_s = self.s_list[index + step * count]
        min_p = min(self.p_list)
        max_p = max(self.p_list)

        p.append(sum([(point - min_p)/10_000 for point in self.p_list[50:125]])/len(self.p_list[50:125]))
        p.append(sum([(point - min_p)/10_000 for point in self.p_list[200:275]])/len(self.p_list[200:275]))

        high_p = [(point - min_p)/(max_p-min_p) for point in self.p_list]

        if 1 in high_p[125:175] and sum(high_p[100:125])/25 < 0.9:
            hight_flaq = 1
        else:
            hight_flaq = 0
        p.append(hight_flaq)
        p += [min_p / 10_000, max_p / 10_000, (max_p - min_p)  / 10_000, p[0] - p[1]]
        p.append(self.p_list.index(max(self.p_list))/300)
        s.append(0)
        return s, p 

    def min_pooling(self, count):
        p = []
        s = []
        steps = round(len(self.p_list) / count)
        for step in range(steps):
            min_p = inf
            if step < steps - 1:
                for index, p_now in enumerate(self.p_list[0 + step * count: count + (step + 1) * count]):
                    if p_now < min_p:
                        min_p = p_now
                        min_s = self.s_list[index + step * count]
            else:
                for index, p_now in enumerate(self.p_list[0 + step * count:]):  
                    if p_now < min_p:
                        min_p = p_now
                        min_s = self.s_list[index + step * count]

            p.append(min_p)
            s.append(min_s)
        return s, p 

    def avg_pooling(self, count):
        p = []
        s = []

        dop_p = []
        steps = round(len(self.p_list) / count)
        for step in range(steps):
            sum_p = 0
            sum_s = 0
            p_min = min(self.p_list)
            
            if step < steps - 1:
                for index, p_now in enumerate(self.p_list[step * count : (step + 1) * count]):
                    sum_p += p_now - p_min
                    sum_s += self.s_list[index + step * count]
                    
                p.append((sum_p / count) / 10000)
                s.append(sum_s / count)
                dop_p.append(sum_p / len(self.p_list[step * count:]))   
            else:
                for index, p_now in enumerate(self.p_list[step * count:]):  
                    sum_p += p_now - p_min
                    sum_s += self.s_list[index + step * count]
                
                p.append((sum_p / len(self.p_list[step * count:])) / 10000)
                s.append(sum_s / len(self.p_list[step * count:])) 
                dop_p.append(sum_p / len(self.p_list[step * count:]))     
        min_p = min(dop_p)
        max_p = max(dop_p)
        dop_p = [(point - min_p)/(max_p-min_p) for point in dop_p]

        min_p = min(self.p_list)
        max_p = max(self.p_list)
        high_p = [(point - min_p)/(max_p-min_p) for point in self.p_list]

        if 1 in high_p[125:175] and sum(high_p[100:125])/25 < 0.9:
            hight_flaq = 1
            print(1)
        else:
            hight_flaq = 0

        return s, [min_p/10_000, max_p/10_000, (max_p - min_p)/10_000, hight_flaq] + p + dop_p
    
    def d_max_pooling(self, count):
        p = []
        s = []
        steps = round(len(self.p_list) / count)
        for step in range(steps):
            max_p = -inf
            if step < steps - 1:
                for index, p_now in enumerate(self.p_list[0 + step * count: count + (step + 1) * count]):
                    if p_now > max_p:
                        max_p = p_now
                        max_s = self.s_list[index + step * count]
            else:
                for index, p_now in enumerate(self.p_list[0 + step * count:]):  
                    if p_now > max_p:
                        max_p = p_now
                        max_s = self.s_list[index + step * count]
                    
            p.append(max_p)
            s.append(max_s)
        
        p_change = []
        for index, p_now in enumerate(p):
            if index < len(p) - 1:
                try:
                    p_change.append((p[index + 1] - p[index])/p[index + 1])
                except ZeroDivisionError:
                    p_change.append((0.0001 - p[index])/0.0001)
        return s, p_change

    def d_min_pooling(self, count):
        p = []
        s = []
        steps = round(len(self.p_list) / count)
        for step in range(steps):
            min_p = inf
            if step < steps - 1:
                for index, p_now in enumerate(self.p_list[0 + step * count: count + (step + 1) * count]):
                    if p_now < min_p:
                        min_p = p_now
                        min_s = self.s_list[index + step * count]
            else:
                for index, p_now in enumerate(self.p_list[0 + step * count:]):  
                    if p_now < min_p:
                        min_p = p_now
                        min_s = self.s_list[index + step * count]
                    
            p.append(min_p)
            s.append(min_s)
        
        p_change = []
        for index, p_now in enumerate(p):
            if index < len(p) - 1:
                try:
                    p_change.append((p[index + 1] - p[index])/p[index + 1])
                except ZeroDivisionError:
                    p_change.append((0.0001 - p[index])/0.0001)
        return s, p_change

    def d_avg_pooling(self, count):
        p = []
        s = []
        steps = round(len(self.p_list) / count)
        for step in range(steps):
            sum_p = 0
            sum_s = 0
            if step < steps - 1:
                for index, p_now in enumerate(self.p_list[0 + step * count:(step + 1) * count]):
                    sum_p += p_now
                    sum_s += self.s_list[index + step * count]
                
                p.append(sum_p / count)
                s.append(sum_s / count)
            else:
                for index, p_now in enumerate(self.p_list[0 + step * count:]):  
                    sum_p += p_now
                    sum_s += self.s_list[index + step * count]
                
                p.append(sum_p / len(self.p_list[0 + step * count:]))
                s.append(sum_s / len(self.p_list[0 + step * count:]))  
        
        p_change = []
        for index, p_now in enumerate(p):
            if index < len(p) - 1:
                try:
                    p_change.append((p[index + 1] - p[index])/p[index + 1])
                except ZeroDivisionError:
                    p_change.append((0.0001 - p[index])/0.0001)
        return s, p_change