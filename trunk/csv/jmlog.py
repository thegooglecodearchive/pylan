####################################################################################################
#    JMeter CSV Log Class                                                                          #
####################################################################################################

from numpy import arange
from matplotlib.dates import MinuteLocator, DateFormatter
from csv import reader, writer
from pylab import *
from datetime import datetime
rcParams['font.size'] = 8

class jmlog:
    def __init__(self,path):
        # Open CSV log file from local disk
        log_file = open(path,"r")
        # Initialize container and read data from log
        self.data=list()
        self.data.extend(reader(log_file))
        # Close CSV log file
        log_file.close()

        # Appen additional column to data array - Seconds from start
        self.data[0].append("secFromStart")
        # Obtain indexes for each column
        self.sec_index  =   self.index("secFromStart")
        self.ts_index   =   self.index("timeStamp")
        self.et_index   =   self.index("elapsed")
        self.lt_index   =   self.index("Latency")
        self.b_index    =   self.index("bytes")
        self.lbl_index  =   self.index("label")
        self.err_index  =   self.index("success")
        self.vu_index   =   self.index("allThreads")

        # Transaction labels
        self.labels = list()

        # Time Variables: fixed and view frame values
        start_time = long(self.data[1][self.ts_index])
        self.start_time = 0
        self.start = 0
        self.end_time = 0
        for row in range(1,len(self.data)):
            # Calculate additional column value - Seconds from start
            current_time = long(self.data[row][self.ts_index])
            self.data[row].append(int((current_time-start_time)/1000))
            # Transform string values to integer type
            self.data[row][self.et_index]=int(self.data[row][self.et_index])
            self.data[row][self.lt_index]=int(self.data[row][self.lt_index])
            self.data[row][self.b_index]=int(self.data[row][self.b_index])
            try:
                self.data[row][self.vu_index]=int(self.data[row][self.vu_index])
            except:
                None
            # Update end time
            if self.end_time < self.data[row][-1]:
                self.end_time = self.data[row][-1]
            # Update label list
            if not self.data[row][self.lbl_index] in self.labels:
                self.labels.append(self.data[row][self.lbl_index])
        self.end = self.end_time

    def index(self,column):
        # Return numerical index for string value (key-value hash)
        for i in range(len(self.data[0])):
            if self.data[0][i] == column:
                return i

    def log_agg(self, time_int, label, mode):
        # Calculate and average performance metrics (set by 'mode' parameter)
        # for specified transaction label and time interval 
        prev_step = self.start
        next_step = prev_step+time_int
        points = dict()
        points[prev_step]=0

        # Poor algorithm for start time calculation - to fix!!!
        for i in range(1,len(self.data)):
            if self.data[i][self.sec_index] >= prev_step:
                row = i
                break

        # Data points calculation
        count = 0
        while prev_step < self.end and row < len(self.data):
            # Check whether timestamp in current interval
            if self.data[row][self.sec_index] < next_step:
                # Is transaction metric?
                if self.data[row][self.lbl_index] == label:
                    # Calculate point for each mode (aka metric)
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
                # Or aggregative metric?
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
                # Finalize averaging
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
                # Next time interval
                prev_step = next_step
                next_step += time_int
        return points

    def trend(self,array = list()):
        # Smooth graph using moving average algorithm
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
        # Remove outliers using moving median algorithm
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
        # Check whether 'Legend' is set and customize plot mode
        if l_opt:
            ax=subplot(2,1,1)
        else:
            ax=subplot(1,1,1)
        
        # Set graph title    
        title(ttl)

        # Extract data points for specified time interval, transaction label and graph type
        points = self.log_agg(time_int, label, graph)

        # Set graph label
        if graph == 'bpt_total'     : label = 'Total Throughput'
        elif graph == 'rpt_total'   : label = 'Total Hits'
        elif graph == 'err_total'   : label = 'Total Error Rate'
        elif graph == 'errc_total'  : label = 'Total Error Count'

        # Initialize data points arrays
        x=list()
        y=list()
        for key in sorted(points.keys()):
            # Define time value (X axis)
            days = key/86400
            hours = (key-86400*days)/3600
            minutes = (key - 86400*days-3600*hours)/60
            seconds = key - 86400*days-3600*hours-60*minutes
            days+=1
            x.append(datetime(1970, 1, days, hours, minutes, seconds))
            # Define time value (Y axis)
            y.append(points[key])

        # Check whether 'Points' is set and customize graph
        if pnts:            
            plot(x,y,linestyle='solid',marker='.',markersize=5,label = label, linewidth=0.5)
        else:            
            plot(x,y,label = label, linewidth=0.5)

        # Check whether 'Trend' is set and customize graph
        if trend:
            plot(x,self.trend(y),label = label+' (Trend)', linewidth=1)

        # Activate grid mode
        grid(True)

        # Evaluate time markers
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

        # Check whether 'Legend' is set and customize graph
        if l_opt:
            legend(bbox_to_anchor=(0, -0.2),loc=2,ncol=1)
