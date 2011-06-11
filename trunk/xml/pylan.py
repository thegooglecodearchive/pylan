from pylab import *
import pygtk, gtk

pygtk.require('2.0')
rcParams['font.size'] = 8

# Fix local module import
import sys, os, inspect
sys.path.append(os.path.dirname(inspect.currentframe().f_code.co_filename))

from jmlog import jmlog

class PyLogAnalyser:
    def destroy(self, widget):
        gtk.main_quit()
        
    def __init__(self):
        self.window = gtk.Dialog()
        self.window.connect("destroy", self.destroy)
        self.window.set_title("PyLan")
        self.window.set_border_width(5)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.show()

        self.toolbar = gtk.Toolbar()
        self.toolbar.show()
        self.toolbar.append_item("Open Log", "Open Jmeter Log",None, None, self.open_log)
        self.toolbar.append_space()        
        self.window.vbox.pack_start(self.toolbar, True, True, 0)

        self.init = 1
        self.preview(gtk.Button())
        gtk.main()

    def open_log(self, widget):
        dialog = gtk.FileChooserDialog("Open JMeter Log File",
                               None,
                               gtk.FILE_CHOOSER_ACTION_OPEN,
                               (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)

        filter = gtk.FileFilter()
        filter.set_name("JMeter Logs")
        filter.add_pattern("*.jtl")
        filter.add_pattern("*.csv")
        filter.add_pattern("*.log")
        dialog.add_filter(filter)

        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)

        response = dialog.run()
        if response == gtk.RESPONSE_OK:      
            self.log = jmlog(dialog.get_filename())
            self.window.set_title("PyLan - "+dialog.get_filename())
            dialog.destroy()
            self.window.vbox.remove(self.table)
            if self.init:
                self.toolbar.append_item("Save Log", "Save recalculated SCV log",None, None, self.save_log)
                self.toolbar.append_space()
                self.toolbar.append_item("Refresh Graph", "Refresh current graph view",None, None, self.refresh)
                self.toolbar.append_space()
                self.toolbar.append_item("Save Image", "Save image as PNG file",None, None, self.save)
                self.toolbar.append_space()
                self.init = 0
            self.preview(gtk.Button())
        dialog.destroy()

    def preview(self,widget):
        self.table = gtk.Table(29, 13, True)
        self.table.show()
        self.table.set_col_spacings(10)
        self.table.set_row_spacings(0)
        self.window.vbox.pack_start(self.table, True, True, 0)

        shift = 22
        self.radio_buttons()
        shift += 2
        
        label = gtk.Label("Granularity (Seconds):")
        label.show()
        self.table.attach(label, 0, 2, 0+shift, 1+shift)
        label = gtk.Label("Granularity (Minutes):")
        label.show()
        self.table.attach(label, 0, 2, 1+shift, 2+shift)

        self.sec = self.time_scale(60)
        self.table.attach(self.sec, 2, 10, 0+shift, 1+shift)
        self.min = self.time_scale(21)
        self.min.set_value(1)
        self.table.attach(self.min, 2, 10, 1+shift, 2+shift)
        
        label = gtk.Label()
        label.set_markup("<b>Start Time:</b>");
        label.show()
        self.table.attach(label, 0, 1, 2+shift, 3+shift)
        label = gtk.Label("Hours:")
        label.show()
        self.table.attach(label, 1, 2, 2+shift, 3+shift)
        label = gtk.Label("Minutes:")
        label.show()
        self.table.attach(label, 3, 4, 3+shift-1, 4+shift-1)

        self.spinner_sh = gtk.SpinButton(gtk.Adjustment(0.0, 0.0, 23.0, 1.0, 4.0, 0.0), 0, 0)
        self.spinner_sh.show()
        self.table.attach(self.spinner_sh, 2, 3, 2+shift, 3+shift)

        self.spinner_sm = gtk.SpinButton(gtk.Adjustment(0.0, 0.0, 59.0, 1.0, 10.0, 0.0), 0, 0)
        self.spinner_sm.show()
        self.table.attach(self.spinner_sm, 4, 5, 2+shift, 3+shift)

        label = gtk.Label()
        label.set_markup("<b>End Time:</b>");
        label.show()
        self.table.attach(label, 5, 6, 2+shift, 3+shift)
        label = gtk.Label("Hours:")
        label.show()
        self.table.attach(label, 6, 7, 2+shift, 3+shift)
        label = gtk.Label("Minutes:")
        label.show()
        self.table.attach(label, 8, 9, 2+shift, 3+shift)

        if not self.init:
            self.spinner_eh = gtk.SpinButton(gtk.Adjustment(int(self.log.end_time/3600), 0.0, 23.0, 1.0, 4.0, 0.0), 0, 0)
        else:
            self.spinner_eh = gtk.SpinButton(gtk.Adjustment(0.0, 0.0, 23.0, 1.0, 4.0, 0.0), 0, 0)
        self.spinner_eh.show()
        self.table.attach(self.spinner_eh, 7, 8, 2+shift, 3+shift)

        if not self.init:
            self.spinner_em = gtk.SpinButton(gtk.Adjustment(int((self.log.end_time-int(self.log.end_time/3600)*3600)/60), 0.0, 59.0, 1.0, 5.0, 0.0), 0, 0)
        else:                                             
            self.spinner_em = gtk.SpinButton(gtk.Adjustment(0, 0.0, 59.0, 1.0, 5.0, 0.0), 0, 0)                                    
        self.spinner_em.show()
        self.table.attach(self.spinner_em, 9, 10, 2+shift, 3+shift)

        separator = gtk.HSeparator()
        separator.show()
        self.table.attach(separator, 0, 10, 3+shift, 4+shift)

        button = gtk.CheckButton("Show Legend")
        button.connect("clicked", self.legend_opt)
        button.show()
        self.table.attach(button, 2, 4, 4+shift, 5+shift)

        button = gtk.CheckButton("Show Points")
        button.connect("clicked", self.points_opt)
        button.show()
        self.table.attach(button, 4, 6, 4+shift, 5+shift)

        button = gtk.CheckButton("Show Trend")
        button.connect("clicked", self.trend_opt)
        button.show()
        self.table.attach(button, 6, 8, 4+shift, 5+shift)

        self.scrolled_window = self.label_win()
        self.table.attach(self.scrolled_window, 10, 13, 0, 29)

        if not self.init:
            self.refresh(gtk.Button())

    def refresh(self,widget):
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
                self.table.remove(self.image)
            except:
                None
            
            self.image = gtk.Image()
            self.image.set_from_file("preview.png")
            self.image.show()
            self.table.attach(self.image, 0, 10, 0, 22)
            os.remove("preview.png")

    def save(self,widget):
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

    def save_log(self,widget):
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
            self.log.save(filename)
        dialog.destroy()

    def radio_buttons(self):
        self.title='Throughput (B/s)'
        self.active = 'bpt'
        shift = 22
        
        button = gtk.RadioButton(None, 'Throughput')
        button.connect("toggled", self.preview_bpt)
        button.show()
        self.table.attach(button, 1, 3, shift, shift+1)

        button = gtk.RadioButton(button,'Response Time')
        button.connect("toggled", self.preview_art)
        button.show()
        self.table.attach(button, 3, 5, shift, shift+1)

        button = gtk.RadioButton(button,'Latency')
        button.connect("toggled", self.preview_lat)
        button.show()
        self.table.attach(button, 5, 7, shift, shift+1)
        
        button = gtk.RadioButton(button,'Hits per second')
        button.connect("toggled", self.preview_rpt)
        button.show()
        self.table.attach(button, 7, 9, shift, shift+1)

        button = gtk.RadioButton(button,'Error Rate')
        button.connect("toggled", self.preview_err)
        button.show()
        self.table.attach(button, 2, 4, shift+1, shift+2)

        button = gtk.RadioButton(button,'Error Count')
        button.connect("toggled", self.preview_errc)
        button.show()
        self.table.attach(button, 4, 6, shift+1, shift+2)

        button = gtk.RadioButton(button,'Active Threads')
        button.connect("toggled", self.preview_vu)
        button.show()
        self.table.attach(button, 6, 8, shift+1, shift+2)

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

    def legend_opt(self,widget):
        self.legend_status = not self.legend_status

    def trend_opt(self,widget):
        self.trend_status = not self.trend_status

    def points_opt(self,widget):
        self.points_status = not self.points_status

    def preview_bpt(self, widget):
        self.title='Throughput (B/s)'
        self.active = 'bpt'

    def preview_art(self, widget):
        self.title='Average Response Time (ms)'
        self.active = 'art'
        
    def preview_lat(self, widget):
        self.title='Average Latency (ms)'
        self.active = 'lat'

    def preview_rpt(self, widget):
        self.title='Hits per second'
        self.active = 'rpt'

    def preview_err(self, widget):
        self.title='Error Rate'
        self.active = 'err'

    def preview_errc(self, widget):
        self.title='Error Count'
        self.active = 'errc'

    def preview_vu(self, widget):
        self.title='Active Threads'
        self.active = 'vusers'

def main():
    PyLogAnalyser()

main()
