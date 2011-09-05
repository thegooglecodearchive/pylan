'''
Copyright (c) 2011, Pavel Paulau <Pavel.Paulau@gmail.com>

All rights reserved.

Redistribution and use of this software in source and binary forms, with or 
without modification, are permitted provided that the following conditions are 
met:

* Redistributions of source code must retain the above copyright notice, this 
list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

* Neither the name of Jan Odvarko nor the names of its contributors may be used 
to endorse or promote products derived from this software without specific 
prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR 
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON 
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

from pylab import *
import pygtk, gtk, gobject
pygtk.require('2.0')
rcParams['font.size'] = 8

from numpy import arange
from matplotlib.dates import MinuteLocator, DateFormatter

from csv import reader, writer
from lxml import etree

from datetime import datetime
import os

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    JMeter Unified Log Class
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class jmlog:
    def __init__(self,path):
        # Read first log line for further validation        
        log_file = open(path,"r")
        first_line = log_file.readline()
        log_file.close()
        
        # Determine file format and perform basic check
        if first_line == '<?xml version="1.0" encoding="UTF-8"?>\n':
            if self.validate_xml(path): self.read_xml()
            else: return None
        else:
            if self.validate_csv(first_line): self.read_csv(path)
            else: return None
    
    def validate_csv(self,line):
        # Validate CSV file header
        header = ("timeStamp","elapsed","label","success","bytes","allThreads","Latency")
        
        for label in header:
            if not line.count(label):
                self.status = "Invalid CSV header"
                return False
                
        self.status = "Valid"
        return True
    
    def read_csv(self,path):
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
        
        # Sample labels
        self.labels = list()

        # Transaction labels
        self.transactions = list()

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
            self.data[row][self.b_index]=int(self.data[row][self.b_index])/1024
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
        
    def validate_xml(self,path):
        # Parse log file
        try:
            self.tree = etree.parse(path)
        except etree.XMLSyntaxError as e:
            self.status = str(e)
            return False
        
        # Prepare DTD file
        schema = '''<!ELEMENT testResults (sample)*>
            <!ATTLIST testResults version	CDATA	#FIXED "1.2">            
            <!ELEMENT sample (httpSample)*>
            <!ATTLIST sample
                t	CDATA	#REQUIRED
                lt	CDATA	#REQUIRED
                ts	CDATA	#REQUIRED
                s	CDATA	#REQUIRED
                lb	CDATA	#REQUIRED
                by	CDATA	#REQUIRED
                ng	CDATA	#REQUIRED
                na	CDATA	#REQUIRED
            >            
            <!ELEMENT httpSample EMPTY>
            <!ATTLIST httpSample
                t	CDATA	#REQUIRED
                lt	CDATA	#REQUIRED
                ts	CDATA	#REQUIRED
                s	CDATA	#REQUIRED
                lb	CDATA	#REQUIRED
                by	CDATA	#REQUIRED
                ng	CDATA	#REQUIRED
                na	CDATA	#REQUIRED
            >
        '''
        
        dtd_filename = os.getcwd() + '/temp_dtd.xml'
        dtd_file = open(dtd_filename,'w')
        dtd_file.write(schema)
        dtd_file.close()
        
        dtd = etree.DTD(dtd_filename)
        os.remove(dtd_filename)
        
        # DTD Validation
        if dtd.validate(self.tree):
            self.status = "Valid"
            return True
        else:
            self.status = "XML validation failed (DTD)"
            return False

    def read_xml(self):
        # Data container
        self.data=list()
        
        # Data header
        self.data.append((
            "timeStamp","elapsed","Latency","bytes",
            "label","success",
            "allThreads","secFromStart",
            "type"))       
        
        # Temp var
        start_time = 0        
        
        for sample in self.tree.findall("sample"):
            # Transcation level
            row = list()    
            # Append column to transaction row for each attribute
            row.append(long(sample.get("ts")))
            row.append(long(sample.get("t")))
            row.append(long(sample.get("lt")))
            row.append(long(sample.get("by"))/1024)
            row.append(sample.get("lb"))
            row.append(sample.get("s"))
            row.append(int(sample.get("na")))
    
            # Set start time
            if not start_time:
                start_time = row[0]
        
            row.append(int((row[0]-start_time)/1000))
            row.append("sample")
    
            # HTTP sample level
            # Aggregative metrics
            elapsedTime=0
            latency=0
    
            for httpSample in sample.getchildren():                
                subRow = list()
                # Append column to sample row for each attribute
                subRow.append(long(httpSample.get("ts")))
                subRow.append(long(httpSample.get("t")))
                subRow.append(long(httpSample.get("lt")))
                subRow.append(long(httpSample.get("by")))
                subRow.append(httpSample.get("lb"))
                subRow.append(httpSample.get("s"))
                subRow.append(int(httpSample.get("na")))
                subRow.append(int((subRow[0]-start_time)/1000))        
                subRow.append("httpSample")
        
                # Append data to global array
                self.data.append(subRow)
        
                # Add saple time and latentcy to current transaction
                elapsedTime+=subRow[1]
                latency+=subRow[2]
        
            # Update transactiob time and latency
            row[1]=elapsedTime
            row[2]=latency
    
            # Append data to global array
            self.data.append(row)
        
        # Obtain indexes for each column
        self.sec_index  =   self.index("secFromStart")
        self.ts_index   =   self.index("timeStamp")
        self.et_index   =   self.index("elapsed")
        self.lt_index   =   self.index("Latency")
        self.b_index    =   self.index("bytes")
        self.lbl_index  =   self.index("label")
        self.err_index  =   self.index("success")
        self.vu_index   =   self.index("allThreads")
        self.type_index =   self.index("type")

        # Sample labels
        self.labels = list()

        # Transaction labels
        self.transactions = list()
        
        # Time Variables: fixed and view frame values
        self.start_time = 0
        self.start = 0
        self.end_time = 0
        
        for row in range(1,len(self.data)):
            if self.end_time < self.data[row][self.sec_index]:
                self.end_time = self.data[row][self.sec_index]
            if self.data[row][self.type_index] == "httpSample":
                if not self.data[row][self.lbl_index] in self.labels:
                    self.labels.append(self.data[row][self.lbl_index])
            else:
                if not self.data[row][self.lbl_index] in self.transactions:
                    self.transactions.append(self.data[row][self.lbl_index])
               
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

    def export2csv(self,path):
        # Convert XML log to CSV format
        log_file = open(path,"wb")
        output = writer(log_file)
        
        for row in range(len(self.data)):
            current_row=(
                self.data[row][self.ts_index],
                self.data[row][self.et_index],
                self.data[row][self.lbl_index],
                self.data[row][self.err_index],
                self.data[row][self.b_index],
                self.data[row][self.vu_index],
                self.data[row][self.lt_index]
            )
            output.writerow(current_row)
        
        log_file.close()
   
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


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Main Class
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class PyLan:    
    def destroy(self, widget):
        gtk.main_quit()
    
    def __init__(self):
        # Main window
        self.window = gtk.Dialog()
        self.window.connect("destroy", self.destroy)
        self.window.set_title("PyLan")
        self.window.set_border_width(5)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.show()
        
        # Menubar
        self.menubar = self.get_main_menu(self.window)
        self.window.vbox.pack_start(self.menubar, True, True, 0)
        self.menubar.show()
        
        # Init options
        self.init   = 1
        self.title  = 'Average Response Time (ms)'
        self.active = 'art'
        self.preview()
        
    def get_main_menu(self, window):
        # Menu Items
        self.menu_items = (
            ( "/_File",                         None,   None,                   0,  "<Branch>" ),
            ( "/File/_Open",                    None,   self.open_log,          0,  None ),
            ( "/File/_Save Chart",              None,   self.save_chart,        0,  None ),
            ( "/File/Save Log",                 None,   self.save_log,          0,  None ),
            ( "/File/sep1",                     None,   None,                   0,  "<Separator>" ),
            ( "/File/Quit",                     None,   gtk.main_quit,          0,  None ),
            ( "/_Chart",                        None,   None,                   0,  "<Branch>" ),
            ( "/Chart/Reponse Time",            None,   self.chart_selector,    0,  "<RadioItem>" ),
            ( "/Chart/Latency",                 None,   self.chart_selector,    1,  "/Chart/Reponse Time" ),
            ( "/Chart/Responses per Second",    None,   self.chart_selector,    2,  "/Chart/Reponse Time" ),
            ( "/Chart/Throughput",              None,   self.chart_selector,    3,  "/Chart/Reponse Time" ),
            ( "/Chart/Error Rate",              None,   self.chart_selector,    4,  "/Chart/Reponse Time" ),
            ( "/Chart/Error Count",             None,   self.chart_selector,    5,  "/Chart/Reponse Time" ),
            ( "/Chart/Active Threads",          None,   self.chart_selector,    6,  "/Chart/Reponse Time" ),
            ( "/_Options",                      None,   None,                   0,  "<Branch>" ),
            ( "/Options/Show Legend",           None,   self.option_selector,   0,  "<CheckItem>" ),
            ( "/Options/Show Trends",           None,   self.option_selector,   1,  "<CheckItem>" ),
            ( "/Options/Show Points",           None,   self.option_selector,   2,  "<CheckItem>" ),
        )
        
        accel_group = gtk.AccelGroup()

        # This function initializes the item factory.
        item_factory = gtk.ItemFactory(gtk.MenuBar, "<main>", accel_group)

        # This method generates the menu items. Pass to the item factory
        #  the list of menu items
        item_factory.create_items(self.menu_items)

        # Attach the new accelerator group to the window.
        window.add_accel_group(accel_group)

        # need to keep a reference to item_factory to prevent its destruction
        self.item_factory = item_factory
        # Finally, return the actual menu bar created by the item factory.
        return item_factory.get_widget("<main>")
    
    def open_log(self,stub1,stub2):
        dialog = gtk.FileChooserDialog("Open JMeter Log File",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        filter = gtk.FileFilter()
        filter.set_name("JMeter Logs")
        filter.add_pattern("*.jtl")
        filter.add_pattern("*.xml")
        filter.add_pattern("*.csv")
        filter.add_pattern("*.log")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        self.filename = dialog.get_filename()
        dialog.destroy()
                
        if response == gtk.RESPONSE_OK:   
            # Reads log
            self.log = jmlog(self.filename)
            
            # Import validation
            if self.log.status == "Valid":
                self.window.set_title("PyLan - " + self.filename)
                self.window.vbox.remove(self.table)
    
                self.init = 0
                self.preview()
            else:
                ww = WarnWindow(self.log.status)

    def preview(self):
        # Height basis
        shift = 24

        # Main canvas
        self.table = gtk.Table(shift+2, 13, True)
        self.table.show()
        self.table.set_col_spacings(10)
        self.table.set_row_spacings(0)
        self.window.vbox.pack_start(self.table, True, True, 0)
        
        # Granularity (Seconds)
        label = gtk.Label("Granularity (seconds):")
        label.show()
        self.table.attach(label, 0, 2, 0+shift, 1+shift)
        
        self.sec = self.time_scale(60)
        self.table.attach(self.sec, 2, 5, 0+shift, 1+shift)
        
        # Granularity (Minutes)
        label = gtk.Label("Granularity (minutes):")
        label.show()
        self.table.attach(label, 5, 7, 0+shift, 1+shift)
        
        self.min = self.time_scale(21)
        self.table.attach(self.min, 7, 10, 0+shift, 1+shift)
        self.min.set_value(1)
        
        # Start time
        label = gtk.Label()
        label.set_markup("<b>Start Time:</b>");
        label.show()
        self.table.attach(label, 0, 1, 1+shift, 2+shift)
        label = gtk.Label("Hours:")
        label.show()
        self.table.attach(label, 1, 2, 1+shift, 2+shift)
        label = gtk.Label("Minutes:")
        label.show()
        self.table.attach(label, 3, 4, 1+shift, 2+shift)

        self.spinner_sh = gtk.SpinButton(gtk.Adjustment(0.0, 0.0, 23.0, 1.0, 4.0, 0.0), 0, 0)
        self.spinner_sh.show()
        self.table.attach(self.spinner_sh, 2, 3, 1+shift, 2+shift)

        self.spinner_sm = gtk.SpinButton(gtk.Adjustment(0.0, 0.0, 59.0, 1.0, 10.0, 0.0), 0, 0)
        self.spinner_sm.show()
        self.table.attach(self.spinner_sm, 4, 5, 1+shift, 2+shift)

        # End time
        label = gtk.Label()
        label.set_markup("<b>End Time:</b>");
        label.show()
        self.table.attach(label, 5, 6, 1+shift, 2+shift)
        label = gtk.Label("Hours:")
        label.show()
        self.table.attach(label, 6, 7, 1+shift, 2+shift)
        label = gtk.Label("Minutes:")
        label.show()
        self.table.attach(label, 8, 9, 1+shift, 2+shift)

        if not self.init:
            self.spinner_eh = gtk.SpinButton(gtk.Adjustment(int(self.log.end_time/3600), 0.0, 23.0, 1.0, 4.0, 0.0), 0, 0)
        else:
            self.spinner_eh = gtk.SpinButton(gtk.Adjustment(0.0, 0.0, 23.0, 1.0, 4.0, 0.0), 0, 0)
        self.spinner_eh.show()
        self.table.attach(self.spinner_eh, 7, 8, 1+shift, 2+shift)

        if not self.init:
            self.spinner_em = gtk.SpinButton(gtk.Adjustment(int((self.log.end_time-int(self.log.end_time/3600)*3600)/60), 0.0, 59.0, 1.0, 5.0, 0.0), 0, 0)
        else:                                             
            self.spinner_em = gtk.SpinButton(gtk.Adjustment(0, 0.0, 59.0, 1.0, 5.0, 0.0), 0, 0)                                    
        self.spinner_em.show()
        self.table.attach(self.spinner_em, 9, 10, 1+shift, 2+shift)
    
        # List of Labels
        self.scrolled_window = self.label_win()
        self.table.attach(self.scrolled_window, 10, 13, 0, shift+2)

        # Refresh chart
        if not self.init:
            self.refresh(None,None)

    def refresh(self,stub1,stub2):
        # Refresh current chart
        if not self.init:
            try:
                time_int = int(self.sec.get_value()+60*self.min.get_value())
            except:
                time_int = 60
            
            end_point = self.spinner_em.get_value()*60 + self.spinner_eh.get_value()*3600
            start_point = self.spinner_sm.get_value()*60 + self.spinner_sh.get_value()*3600
            if end_point < self.log.end_time:
                self.log.end = max(300,int(end_point))
            else:
                self.log.end = self.log.end_time
            if start_point < self.log.end:
                self.log.start = int(start_point)
            else:
                self.log.start = max(0,int(self.log.end)-300)
            
            if time_int:
                clf()
                if self.active == 'vusers':
                    self.log.plot(self.active, time_int, None, False,self.title,False,False)
                else:
                    for label in self.label_list:
                        self.log.plot(self.active, time_int, label, self.legend_status,self.title,self.trend_status,self.points_status)
                    if self.total_status and self.active != 'art' and self.active != 'lat':
                        self.log.plot(self.active+'_total', time_int, None, self.legend_status, self.title,self.trend_status,self.points_status)
                savefig("preview.png",dpi=96, transparent=False,format="png")
                
                try:
                    self.table.remove(self.button)
                except:
                    None
                
                # Image object
                self.image = gtk.Image()
                self.image.set_from_file("preview.png")
                self.image.show()
                os.remove("preview.png")
                
                # Button container
                self.button = gtk.Button()
                self.button.add(self.image)
                self.button.show()
                self.button.connect("clicked", self.refresh, "1")
                
                self.table.attach(self.button, 0, 10, 0, 24)
                
    def save_chart(self,stub1,stub2):
        # Save chart to PNG file
        if not self.init:
            dialog = gtk.FileChooserDialog("Save...",
                                    None,
                                   gtk.FILE_CHOOSER_ACTION_SAVE,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            dialog.set_default_response(gtk.RESPONSE_OK)
            filter = gtk.FileFilter()
            filter.set_name("PNG Images")
            filter.add_pattern("*.png")
            dialog.add_filter(filter)
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                if dialog.get_filename()[-4:] != '.png':
                    filename = dialog.get_filename()+'.png'
                else:
                    filename = dialog.get_filename()
                savefig(filename,dpi=96, transparent=False,format="png")
            dialog.destroy()

    def save_log(self,stub1,stub2):
        # Save log in CSV format
        if not self.init:
            dialog = gtk.FileChooserDialog("Save...",
                                    None,
                                   gtk.FILE_CHOOSER_ACTION_SAVE,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            dialog.set_default_response(gtk.RESPONSE_OK)
            filter = gtk.FileFilter()
            filter.set_name("JMeter Logs")
            filter.add_pattern("*.jtl")
            filter.add_pattern("*.csv")
            filter.add_pattern("*.log")
            dialog.add_filter(filter)
            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                filename = dialog.get_filename()
                self.log.export2csv(filename)
            dialog.destroy()

    def label_win(self):
        self.label_list = list()
        self.total_status = False
        self.legend_status = False
        self.trend_status = False
        self.points_status = False
        
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_border_width(0)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.show()
      
        table = gtk.Table(30, 3, True)
        table.show()
        scrolled_window.add_with_viewport(table)

        if not self.init:
            row = 1

            label = gtk.Label()
            label.set_markup("<b>Transactions:</b>");
            label.show()
            table.attach(label, 0, 3, 0, 1)

            for label in sorted(self.log.transactions):
                button = gtk.CheckButton(label)
                button.connect("clicked", self.label_options, label)
                button.set_alignment(0,0.5)
                button.show()
                table.attach(button, 0, 3, row, row+1)
                row +=1
        
            label = gtk.Label()
            label.set_markup("<b>Samples:</b>");
            label.show()
            table.attach(label, 0, 3, row, row+1)

            row+=1
            
            for label in sorted(self.log.labels):
                button = gtk.CheckButton(label)
                button.connect("clicked", self.label_options, label)
                button.set_alignment(0,0.5)
                button.show()
                table.attach(button, 0, 3, row, row+1)
                row +=1
            button = gtk.CheckButton('Total')
            button.connect("clicked", self.total)
            button.show()
            table.attach(button, 0, 3, row, row+1)

        return scrolled_window

    def time_scale(self, scale = 60):
            Hscale = gtk.HScale(gtk.Adjustment(0, 0, scale, 1, 1, 1))
            Hscale.set_update_policy(gtk.UPDATE_CONTINUOUS)
            Hscale.set_digits(0)
            Hscale.set_value_pos(gtk.POS_LEFT)
            Hscale.set_draw_value(True)
            Hscale.show()
            return Hscale

    def label_options(self, widget, label = None):
        if widget.get_active():
            self.label_list.append(label)
        else:
            self.label_list.remove(label)
    
    def total(self,widget):
        self.total_status = not self.total_status

    def option_selector(self,option,stub):
        # Update settings
        if option == 0:
            self.legend_status = not self.legend_status
        elif option == 1:
            self.trend_status = not self.trend_status
        elif option == 2:
            self.points_status = not self.points_status
        
        # Refresh chart
        if not self.init:
            self.refresh(None,None)

    def chart_selector(self,chart_type,stub):
        # Set chart title and type
        if chart_type == 0:
            self.title='Average Response Time (ms)'
            self.active = 'art'
        elif chart_type == 1:
            self.title='Average Latency (ms)'
            self.active = 'lat'
        elif chart_type == 2:
            self.title='Responses per Second'
            self.active = 'rpt'
        elif chart_type == 3:
            self.title='Throughput (kB/s)'
            self.active = 'bpt'
        elif chart_type == 4:
            self.title='Error Rate'
            self.active = 'err'
        elif chart_type == 5:
            self.title='Error Count'
            self.active = 'errc'
        elif chart_type == 6:
            self.title='Active Threads'
            self.active = 'vusers'
        
        # Refresh chart
        if not self.init:
            self.refresh(None,None)

class ProgressBar:
    def __init__(self):
        # Create the ProgressBar
        self.progress = gtk.Window(gtk.WINDOW_POPUP)
        self.progress.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.progress.set_border_width(10)
        self.progress.show()

        self.bar = gtk.ProgressBar()
        self.bar.show()        
        self.progress.add(self.bar)        

class WarnWindow:
    def __init__(self, status):
        md = gtk.MessageDialog(None, 
            gtk.DIALOG_DESTROY_WITH_PARENT,gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE,
            status)
        md.run()
        md.destroy()

def main():
    PyLan()
    gtk.main()    

main()