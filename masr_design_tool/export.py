try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk
import tkFileDialog
import shelve
import csv
from winplace import get_win_place
from collections import OrderedDict
import dblocation

db_location = dblocation.db_location


class Exportdb(Toplevel):
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.master = master
        self.resizable(width=FALSE, height=FALSE)
        self.lift()

        # Place window
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))

        self.mainframe = ttk.Frame(self, padding=5)
        self.mainframe.pack()

        # Create header label and export button
        self.header_label = ttk.Label(self.mainframe, text='Select database(s) to export to CSV.', wraplength=300)
        self.messagevar = StringVar()
        self.info_label = ttk.Label(self.mainframe, textvar=self.messagevar, wraplength=300)
        self.expt_button = ttk.Button(self.mainframe, text='Export', command=self.export)
        self.close_button = ttk.Button(self.mainframe, text='Close', command=self.destroy)

        # Create checkboxes with labels for each database
        self.checkbox_frame = ttk.Frame(self.mainframe)
        self.db_dict = OrderedDict(zip(self.master.components, self.master.db_names))
        self.checkvar_list = []
        for comp_name in self.db_dict:
            checkvar = IntVar()
            check = ttk.Checkbutton(self.checkbox_frame, text=comp_name, variable=checkvar)
            check.pack(pady=5, anchor=W)
            self.checkvar_list.append(checkvar)

        # Pack widgets
        self.header_label.pack(expand=YES, padx=15, pady=5)
        self.checkbox_frame.pack(padx=15, pady=5)
        self.info_label.pack(padx=15, pady='3 5')
        self.close_button.pack(side=RIGHT)
        self.expt_button.pack(side=RIGHT)

        self.protocol('WM_DELETE_WINDOW', self.destroy)

    def export(self):
        # Obtain user-specified directory in which to save the csv files
        dir_opt = {'initialdir': 'C:\\', 'mustexist': False, 'parent': self.master, 'title': 'Choose save directory.'}
        dirname = tkFileDialog.askdirectory(**dir_opt)
        self.lift()

        # Retrieve selected database names
        selected_names = []
        for i, db_name in enumerate(self.db_dict.values()):
            if self.checkvar_list[i].get() == 1:
                selected_names.append(db_name)

        # Loop through selected databases and save to a .csv file located at dirname/db_name.csv
        for db_name in selected_names:
            this_db = shelve.open(db_location + db_name)
            class_name = db_name[:-2].capitalize()
            attr_names = getattr(__import__(class_name.lower()), class_name).real_attr_names
            pretty_attr_dict = getattr(__import__(class_name.lower()), class_name).pretty_attr_dict
            try:
                with open(dirname+'/'+db_name+'.csv', 'wb') as csvfile:
                    writer = csv.writer(csvfile, dialect='excel')
                    # Create header row
                    header = []
                    for key in pretty_attr_dict.keys():
                        try:
                            attr_str = key+' (%s)' % pretty_attr_dict[key][0]
                        except IndexError:
                            attr_str = key
                        header.append(attr_str)
                    writer.writerow(header)
                    # Create object rows
                    for obj in this_db.values():
                        obj_row = []
                        for attr in attr_names:
                            try:
                                attr_val = getattr(obj, attr)['value']
                            except TypeError:
                                attr_val = getattr(obj, attr)
                            obj_row.append(attr_val)
                        writer.writerow(obj_row)
            except IOError as e:
                self.messagevar.set(str(e))
            this_db.close()
        self.messagevar.set("Database export successful.")