from numpy import arange
from matplotlib.dates import MinuteLocator, DateFormatter
from csv import reader, writer
from pylab import *
from datetime import datetime
rcParams['font.size'] = 8

class jmlog:
    def __init__(self,path):
        log_file = open(path,"r")
        self.data=list()
        self.data.extend(reader(log_file))
        log_file.close()
        
        self.data[0].append("secFromStart")
        self.sec_index  =   self.index("secFromStart")
        self.ts_index   =   self.index("timeStamp")
        self.et_index   =   self.index("elapsed")
        self.lt_index   =   self.index("Latency")
        self.b_index    =   self.index("bytes")
        self.lbl_index  =   self.index("label")
        self.err_index  =   self.index("success")
        self.vu_index   =   self.index("allThreads")

        self.labels = list()
        start_time = long(self.data[1][self.ts_index])
        self.start_time = 0
        self.start = 0
        self.end_time = 0
        for row in range(1,len(self.data)):
            current_time = long(self.data[row][self.ts_index])
            self.data[row].append(int((current_time-start_time)/1000))
            self.data[row][self.et_index]=int(self.data[row][self.et_index])
            self.data[row][self.lt_index]=int(self.data[row][self.lt_index])
            self.data[row][self.b_index]=int(self.data[row][self.b_index])
            try:
                self.data[row][self.vu_index]=int(self.data[row][self.vu_index])
            except:
                None
            if self.end_time < self.data[row][-1]:
                self.end_time = self.data[row][-1]
            if not self.data[row][self.lbl_index] in self.labels:
                self.labels.append(self.data[row][self.lbl_index])
        self.end = self.end_time

    def index(self,column):
        for i in range(len(self.data[0])):
            if self.data[0][i] == column:
                return i

    def log_agg(self, time_int, label, mode):
        prev_step = self.start
        next_step = prev_step+time_int
        points = dict()
        points[prev_step]=0
        
        for i in range(1,len(self.data)):
            if self.data[i][self.sec_index] >= prev_step:
                row = i
                break
        count = 0
        while prev_step < self.end and row < len(self.data):
            if self.data[row][self.sec_index] < next_step:
                if self.data[row][self.lbl_index] == label:
                    if mode == 'bpt':
                        points[prev_step] += self.data[row][self.b_index]
                    elif mode == 'art':
                        points[prev_step] += self.data[row][self.et_index]
                        count += 1
                    elif mode == 'lat':
                        points[prev_step] += self.data[row][self.lt_index]
                        count += 1
                    elif mode == 'rpt':
                        points[prev_step] += 1
                    elif mode == 'err' or mode == 'errc':
                        if self.data[row][self.err_index] == 'false':
                            points[prev_step] += 1
                elif mode == 'err_total' or mode == 'errc_total':
                    if self.data[row][self.err_index] == 'false':
                        points[prev_step] += 1
                elif mode == 'bpt_total':
                    points[prev_step] += self.data[row][self.b_index]
                elif mode == 'rpt_total':
                    points[prev_step] += 1
                elif mode == 'vusers':
                    points[prev_step] = self.data[row][self.vu_index]
                row += 1
            else:
                if mode == 'errc' or mode == 'errc_total':
                    points[next_step] = points[prev_step]
                elif mode == 'vusers':
                    None
                elif mode == 'art' or mode == 'lat':
                    if count:
                        points[prev_step] /= count
                        count = 0
                    if next_step < self.end:
                        points[next_step] = 0
                else:                            
                    points[prev_step] /= (time_int*1.0)
                    if next_step < self.end:
                        points[next_step] = 0
                prev_step = next_step
                next_step += time_int
        return points

    def trend(self,array = list()):
        ma = list()
        for i in range(5):
            ma.append(array[i])
        for i in range(5,len(array)-5):
            smoothed = 0
            for j in range(i-5,i+5):
                smoothed+=array[j]/10
            ma.append(smoothed)
        for i in range(len(array)-5,len(array)):
            ma.append(array[i])
        return ma

    def outlier_filter(self,array = list()):
        mm = list()
        for i in range(2):
            mm.append(array[2])
        for i in range(2,len(array)-3):
            block = list()
            for j in range(i-2,i+3):
                block.append(array[j])
            mm.append(sorted(block)[2])
        for i in range(len(array)-3,len(array)):
            mm.append(array[i])
        return mm
   
    def plot(self, graph = 'bpt_total',time_int = 30, label = None, l_opt = False,ttl=None,trend = False, pnts=False):
        if l_opt:
            ax=subplot(2,1,1)
        else:
            ax=subplot(1,1,1)

        title(ttl)
        points = self.log_agg(time_int, label, graph)

        if graph == 'bpt_total'     : label = 'Total Throughput'
        elif graph == 'rpt_total'   : label = 'Total Hits'
        elif graph == 'err_total'   : label = 'Total Error Rate'
        elif graph == 'errc_total'  : label = 'Total Error Count'

        x=list()
        y=list()
        for key in sorted(points.keys()):
            days = key/86400
            hours = (key-86400*days)/3600
            minutes = (key - 86400*days-3600*hours)/60
            seconds = key - 86400*days-3600*hours-60*minutes
            days+=1
            x.append(datetime(1970, 1, days, hours, minutes, seconds))
            y.append(points[key])
        if pnts:
            plot(x,y,linestyle='solid',marker='.',markersize=5,label = label, linewidth=0.5)
        else:
            plot(x,y,label = label, linewidth=0.5)
        if trend:
            plot(x,self.trend(y),label = label+' (Trend)', linewidth=1)

        grid(True)
        max_min = self.end/60
        min_min = self.start/60
        
        time_int = (int((max_min-min_min)/10.0))/10*10
        if not time_int:
            if max_min>75:
                time_int=10
            else:
                time_int=5
        if time_int > 30:
            time_int = 60

        if time_int<=60:
            xlabel('Elapsed time (hh:mm)')
            ax.xaxis.set_major_locator( MinuteLocator(arange(0,max_min,time_int)))
            ax.xaxis.set_minor_locator( MinuteLocator(arange(0,max_min,time_int/5)))
            ax.xaxis.set_major_formatter( DateFormatter('%H:%M') )
        else:
            xlabel('Elapsed time (dd;hh:mm)')
            labels = ax.get_xticklabels()
            ax.xaxis.set_major_formatter( DateFormatter('%d;%H:%M') )
            setp(labels, rotation=0, fontsize=8)
        if l_opt:
            legend(bbox_to_anchor=(0, -0.2),loc=2,ncol=1)
