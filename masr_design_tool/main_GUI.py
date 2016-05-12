#! /usr/bin/env python

import logging
import traceback
import tkMessageBox
try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk
import tkFont
import tkFileDialog
import csv
import shelve
from collections import OrderedDict
import dbmanagement
import export
import alternatives_new
import tradespace
from winplace import get_win_place
from unitconversion import convert_unit
import dblocation
import sys
import os

db_location = dblocation.db_location


class QuadGUI(ttk.Frame):
    """
    The QuadGUI class is the main frame that fills the entire root window. It holds subframes including the vehicle
    requirements frame, the manufacturing requirements frame, the data management frame, and the alternatives frame.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, padding=3)
        # master.report_callback_exception = self.report_callback_exception
        self.master = master

        # Create subframes within mainframe (i.e., self)
        self.vehicle_req_frame = VehicleReqFrame(self)
        self.sensor_frame = SensorFrame(self)
        self.manuf_req_frame = ManufReqFrame(self)
        self.data_mgt_frame = DataMgtFrame(self)
        self.alternatives_frame = AlternativesFrame(self)

        # Grid subframes
        self.vehicle_req_frame.grid(column=0, row=0, columnspan=1, sticky=(N, S, E, W))
        self.sensor_frame.grid(column=1, row=0, columnspan=1, sticky=(N, S, E, W))
        self.manuf_req_frame.grid(column=2, row=0, columnspan=1, sticky=(N, S, E, W))
        self.data_mgt_frame.grid(column=3, row=0, columnspan=1, sticky=(N, S, E, W))
        self.alternatives_frame.grid(column=0, row=1, columnspan=4, sticky=(N, S, E, W))

        # Manage mainframe resizing
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.rowconfigure(1, weight=1)

    # def report_callback_exception(self, *args):
    #     err = traceback.format_exception(*args)
    #     log_filename = '../logfiles/logfile.log'
    #     logging.basicConfig(filename=log_filename, level=logging.DEBUG)
    #     logging.debug(str(err))
    #     tkMessageBox.showerror('Exception', err)


class VehicleReqFrame(ttk.Frame):
    """
    The vehicle requirements frame is the frame that holds all of the widgets that enables the user to enter the
    vehicle requirements such as: required endurance, required payload, maximum weight, maximum dimension, etc.. It also
    contains a button that when pressed will open a new toplevel window where the user can define importance weightings
    for all of the vehicle requirements.

    Note that if additional vehicle requirements are implemented beyond what is included here (endurance, payload,
    weight, and size), the additional requirements need to be hard-coded into the class, including the variable
    'self.weights'. In addition, the 'requirements' list of names that is passed to the weightings toplevel located in
    the set_weightings() method will need to be updated.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, borderwidth=2, relief='sunken')
        self.master = master
        # Initialization gives all categories an equal weight (50/100).
        self.weights = OrderedDict([('max_endurance', [50, 'high']), ('max_payload', [50, 'high']),
                                    ('weight', [50, 'low']), ('max_dimension', [50, 'low']),
                                    ('build_time', [50, 'low'])])

        # Create subframes
        self.constraints_frame = ttk.Frame(self)
        self.wgt_frame = ttk.Frame(self)

        # Create constraints frame widgets
        self.vehicle_req_title = ttk.Label(self.constraints_frame, text='Vehicle Requirements',
                                           font='Helvetica 10 bold')
        f = tkFont.Font(self.vehicle_req_title, self.vehicle_req_title.cget("font"))
        f.configure(underline=False)
        self.vehicle_req_title.configure(font=f)

        self.endurance_label = ttk.Label(self.constraints_frame, text='Endurance (min)')
        self.endurance_var = DoubleVar()
        self.endurance_entry = ttk.Entry(self.constraints_frame, textvariable=self.endurance_var, width=7)

        self.payload_label = ttk.Label(self.constraints_frame, text='Payload')
        self.payload_var = DoubleVar()
        self.payload_entry = ttk.Entry(self.constraints_frame, textvariable=self.payload_var, width=7)
        self.payload_unit_cb = ttk.Combobox(self.constraints_frame, state='readonly',
                                            values=('N', 'lbf', 'kg'), width=3)
        self.payload_unit_cb.current(0)

        self.max_weight_label = ttk.Label(self.constraints_frame, text='Maximum Weight')
        self.max_weight_var = DoubleVar()
        self.max_weight_entry = ttk.Entry(self.constraints_frame, textvariable=self.max_weight_var, width=7)
        self.max_weight_unit_cb = ttk.Combobox(self.constraints_frame, state='readonly',
                                               values=('N', 'lbf', 'kg'), width=3)
        self.max_weight_unit_cb.current(0)

        self.max_size_label = ttk.Label(self.constraints_frame, text='Maximum Size')
        self.max_size_var = DoubleVar()
        self.max_size_entry = ttk.Entry(self.constraints_frame, textvariable=self.max_size_var, width=7)
        self.max_size_unit_cb = ttk.Combobox(self.constraints_frame, state='readonly',
                                             values=('m', 'cm', 'in'), width=3)
        self.max_size_unit_cb.current(0)

        self.maneuverability_label = ttk.Label(self.constraints_frame, text='Maneuverability')
        self.maneuver_var = StringVar()
        self.maneuverability_combobox = ttk.Combobox(self.constraints_frame, textvariable=self.maneuver_var,
                                                     state='readonly', values=('Normal', 'High', 'Acrobatic'), width=7)
        self.maneuverability_combobox.current(0)

        self.cover_checkvar = IntVar()
        self.cover_check = ttk.Checkbutton(self.constraints_frame, text="Top plate cover", variable=self.cover_checkvar)

        # Grid constraints frame widgets
        self.vehicle_req_title.grid(column=1, row=0, columnspan=4, padx=12, pady=12)

        self.endurance_label.grid(column=1, row=1, sticky=W, padx=5, pady='0 2')
        self.endurance_entry.grid(column=2, row=1, sticky=W, pady='0 2')

        self.payload_label.grid(column=1, row=2, sticky=W, padx=5, pady='2 2')
        self.payload_entry.grid(column=2, row=2, sticky=W)
        self.payload_unit_cb.grid(column=3, row=2, sticky=W, padx='0 5', pady='2 2')

        self.max_weight_label.grid(column=1, row=3, sticky=W, padx=5, pady='2 2')
        self.max_weight_entry.grid(column=2, row=3, sticky=W)
        self.max_weight_unit_cb.grid(column=3, row=3, sticky=W, padx='0 5', pady='2 2')

        self.max_size_label.grid(column=1, row=4, sticky=W, padx=5, pady='2 2')
        self.max_size_entry.grid(column=2, row=4, sticky=W)
        self.max_size_unit_cb.grid(column=3, row=4, sticky=W, padx='0 5', pady='2 2')

        self.maneuverability_label.grid(column=1, row=5, sticky=W, padx=5, pady='2 2')
        self.maneuverability_combobox.grid(column=2, row=5, columnspan=2, sticky=W, pady='2 2')

        self.cover_check.grid(column=1, row=6, sticky=W, padx=5, pady='2 5')

        # Manage constraints frame resizing
        self.columnconfigure(0, weight=1)
        self.columnconfigure(4, weight=1)

        # Create weightings button
        self.weightings_button = ttk.Button(self.wgt_frame, text='Set Importance Ratings',
                                            command=self.set_weightings)
        self.weightings_button.pack()

        # Pack subframes
        self.constraints_frame.pack(fill=BOTH, expand=YES)
        self.wgt_frame.pack(fill=BOTH, expand=YES)

    def set_weightings(self):
        """
        Note that the requirements list here will need to be changed if a future user wants to change the number of
        weighting categories. The string that goes in the 'requirements' list below is a pretty name associated
        with the quadrotor attribute names ['max_endurance', 'max_payload', 'weight', 'max_dimension', 'build_time'].
        Note also that when the user closes the WeightingsWindow instance the weighting values in the variable
        'self.weights' will be updated accordingly.
        """
        requirements = ['Maximize endurance', 'Maximize payload', 'Minimize weight', 'Minimize size',
                        'Minimize build time']
        weight_window = WeightingsWindow(self, requirements)
        self.wait_window(weight_window)


class WeightingsWindow(Toplevel):
    """
        The input 'requirements'  is a list of strings containing vehicle requirement names. (See set_weightings()
        method of the vehicle requirements frame class.)

        This toplevel window allows the user to select their requirements ratings corresponding to the vehicle
        requirements defined in the vehicle requirements frame. This class is written to handle an arbitrary
        requirements list and update the variable 'self.master.weights' in the general case. Therefore it should not
        need to be updated if new vehicle requirements are added to the vehicle requirements frame.
    """
    def __init__(self, master, requirements):

        Toplevel.__init__(self, master)
        self.master = master
        self.requirements = requirements
        self.title("Set Requirement Importance")
        self.resizable(width=FALSE, height=FALSE)

        # Place window
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))

        # Create subframes
        self.mainframe = ttk.Frame(self, padding='12 0 5 15')
        self.button_frame = ttk.Frame(self)

        # Create widgets in mainframe
        self.main_label = ttk.Label(self.mainframe,
                                    text='Please set the relative importance of each vehicle requirement.')
        self.main_label.grid(column=0, row=0, columnspan=4, padx=10, pady='15 10')

        self.weightings_vars = []
        self.weightings_widgets = {}
        row = 1
        for i, req in enumerate(requirements):
            req_label = ttk.Label(self.mainframe, text=req)
            req_weight = IntVar()
            req_scale = ttk.Scale(self.mainframe, orient=HORIZONTAL, length=200, from_=1, to=100, variable=req_weight,
                                  command=lambda event, this_req=req: self.accept_whole_number_only(event, this_req))
            req_entry = ttk.Entry(self.mainframe, textvariable=req_weight, width=3)
            req_weight.set(self.master.weights.values()[i][0])

            req_label.grid(column=0, row=row, sticky=W, padx=5, pady='10 0')
            req_scale.grid(column=1, row=row, columnspan=2, sticky=W, pady='10 0')
            req_entry.grid(column=3, row=row, sticky=W, padx='2 5', pady='10 0')

            self.weightings_widgets[req] = (req_scale, req_entry, req_weight)
            self.weightings_vars.append(req_weight)
            row += 1

        self.arrow_low_label = ttk.Label(self.mainframe, text='less')
        self.arrow_high_label = ttk.Label(self.mainframe, text='more')
        self.arrow_low_label.grid(column=1, row=row, sticky=W)
        self.arrow_high_label.grid(column=2, row=row, sticky=E)

        # Create widgets in button frame
        self.save_button = ttk.Button(self.button_frame, text='Save', command=self.save_weights)
        self.cancel_button = ttk.Button(self.button_frame, text='Cancel', command=self.destroy)
        self.cancel_button.pack(side=RIGHT)
        self.save_button.pack(side=RIGHT)

        # Pack frames
        self.mainframe.pack(fill=BOTH, expand=YES)
        self.button_frame.pack(fill=X)

        self.protocol('WM_DELETE_WINDOW', self.destroy)

    def accept_whole_number_only(self, event, req):
        scale = self.weightings_widgets[req][0]
        scale_val = scale.get()
        if int(scale_val) != scale_val:
            scale.set(round(scale_val))

    def save_weights(self):
        """
        Saves the user selected values to the self.master.weights dictionary variable and closes the window.
        """
        weight_vals = [var.get() for var in self.weightings_vars]
        for i, val_list in enumerate(self.master.weights.values()):
            val_list[0] = weight_vals[i]
        self.destroy()


class SensorFrame(ttk.Frame):
    """
    This is the frame that contains all widgets necessary for the user to select the desired sensors to be included on
    the vehicle. It creates a checkbox for each sensor in the sensor database during initialization. Also contains a
    get_selected method which returns a list of currently selected sensor objects.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, borderwidth=2, relief='sunken')
        self.master = master
        self.sensor_title = ttk.Label(self, text='Sensor Options', font='Helvetica 10 bold')
        f = tkFont.Font(self.sensor_title, self.sensor_title.cget("font"))
        f.configure(underline=False)
        self.sensor_title.configure(font=f)
        self.sensor_sub_title = ttk.Label(self, text='(may select multiple sensors)')
        self.checkvar_list = []

        # Create subframe to put checkboxes in
        self.check_frame = ttk.Frame(self)

        # Create list of sensors
        self.refresh()

    def refresh(self):
        for widget in self.check_frame.children.values():
            widget.destroy()
        self.checkvar_list = []
        sensor_db = shelve.open(db_location + 'sensordb')
        for sensor in sensor_db.values():
            checkvar = IntVar()
            check = ttk.Checkbutton(self.check_frame, text=sensor.name, variable=checkvar)
            check.pack(pady=5, anchor=W)
            self.checkvar_list.append(checkvar)
        sensor_db.close()

        self.sensor_title.pack_forget()
        self.sensor_sub_title.pack_forget()
        self.check_frame.pack_forget()
        self.sensor_title.pack(pady='12 7', padx=12)
        self.sensor_sub_title.pack(pady='0 10', padx=12)
        self.check_frame.pack(side=LEFT, pady=10, padx=12)

    def get_selected(self):
        selected_list = []
        sensor_db = shelve.open(db_location + 'sensordb')
        # Loop through sensors
        for i, sensor in enumerate(sensor_db.values()):
            this_sensor = sensor
            # If sensor is selected add it to the selected list
            if self.checkvar_list[i].get() == 1:
                selected_list.append(this_sensor)
        sensor_db.close()
        return selected_list


class ManufReqFrame(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, borderwidth=2, relief='sunken')
        self.master = master

        self.build_time_frame = ttk.Frame(self)

        # Create widgets within the build time frame
        self.manuf_req_title = ttk.Label(self.build_time_frame, text='Manufacturing Requirements',
                                         font='Helvetica 10 bold')
        f = tkFont.Font(self.manuf_req_title, self.manuf_req_title.cget("font"))
        f.configure(underline=False)
        self.manuf_req_title.configure(font=f)

        self.build_time_label = ttk.Label(self.build_time_frame, text='Allowable Build Time (hrs)')
        self.build_time_var = DoubleVar()
        self.build_time_entry = ttk.Entry(self.build_time_frame, textvariable=self.build_time_var, width=7)

        self.manuf_req_title.pack(padx=12, pady=12)
        self.build_time_label.pack(side=LEFT, padx='5 2', pady='0 5')
        self.build_time_entry.pack(side=LEFT, padx='2 5', pady='0 5')

        # Create build dim frame
        self.max_build_dim_frame = MaxBuildDimFrame(self)

        # Pack subframes
        self.build_time_frame.pack(fill=X)
        self.max_build_dim_frame.pack()

        # Manage manufacturing requirements frame resizing
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)


class MaxBuildDimFrame(ttk.Frame):
    """
    Subframe in the main GUI window which contains all widgets related to constraints due to manufacturing, such as
    printer and cutter dimensions as well as maximum allowable build time.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, borderwidth=1, relief='ridge')
        self.master = master

        printer_db = shelve.open(db_location + 'printerdb')
        cutter_db = shelve.open(db_location + 'cutterdb')
        if printer_db:
            self.printername_list = printer_db.keys()
        else:
            self.printername_list = ['No printers']
        if cutter_db:
            self.cuttername_list = cutter_db.keys()
        else:
            self.cuttername_list = ['No cutters']
        printer_db.close()
        cutter_db.close()

        # Create widgets within maximum build dimensions frame (which is within manufacturing requirements frame)
        self.max_build_dim_label = ttk.Label(self, text='3D Printer Options')

        self.printer_label = ttk.Label(self, text='Printer')
        self.printer_combobox = ttk.Combobox(self, state='readonly', values=self.printername_list)
        self.printer_combobox.bind("<<ComboboxSelected>>", self.set_values)
        self.printer_combobox.current(0)

        self.printer_len_label = ttk.Label(self, text='length')
        self.printer_len_entry = ttk.Entry(self, state='readonly', width=7)
        self.printer_len_unit_cb = ttk.Combobox(self, state='readonly', values=('m', 'cm', 'in'), width=3)
        self.printer_len_unit_cb.bind("<<ComboboxSelected>>",
                                      lambda event, entry_name='printer_len':
                                      self.new_unit_selection(event, entry_name))

        self.printer_width_label = ttk.Label(self, text='width')
        self.printer_width_entry = ttk.Entry(self, state='readonly', width=7)
        self.printer_width_unit_cb = ttk.Combobox(self, state='readonly', values=('m', 'cm', 'in'), width=3)
        self.printer_width_unit_cb.bind("<<ComboboxSelected>>",
                                        lambda event, entry_name='printer_width':
                                        self.new_unit_selection(event, entry_name))

        self.printer_height_label = ttk.Label(self, text='height')
        self.printer_height_entry = ttk.Entry(self, state='readonly', width=7)
        self.printer_height_unit_cb = ttk.Combobox(self, state='readonly', values=('m', 'cm', 'in'), width=3)
        self.printer_height_unit_cb.bind("<<ComboboxSelected>>",
                                         lambda event, entry_name='printer_height':
                                         self.new_unit_selection(event, entry_name))

        # Create selectable list of print materials
        self.pmat_label = ttk.Label(self, text='Print Materials')
        self.pmatlist_frame = PrintingMaterialFrame(self)

        # self.cutter_label = ttk.Label(self, text='Laser Cutter')
        # self.cutter_combobox = ttk.Combobox(self, state='readonly', values=self.cuttername_list)
        # self.cutter_combobox.bind("<<ComboboxSelected>>", self.set_values)
        # self.cutter_combobox.current(0)
        #
        # self.cutter_len_label = ttk.Label(self, text='length')
        # self.cutter_len_entry = ttk.Entry(self, state='readonly', width=7)
        # self.cutter_len_unit_cb = ttk.Combobox(self, state='readonly', values=('m', 'cm', 'in'), width=3)
        # self.cutter_len_unit_cb.bind("<<ComboboxSelected>>",
        #                              lambda event, entry_name='cutter_len':
        #                              self.new_unit_selection(event, entry_name))
        #
        # self.cutter_width_label = ttk.Label(self, text='width')
        # self.cutter_width_entry = ttk.Entry(self, state='readonly', width=7)
        # self.cutter_width_unit_cb = ttk.Combobox(self, state='readonly', values=('m', 'cm', 'in'), width=3)
        # self.cutter_width_unit_cb.bind("<<ComboboxSelected>>",
        #                                lambda event, entry_name='cutter_width':
        #                                self.new_unit_selection(event, entry_name))

        # Initialize entry and combobox values based on first printer and cutter
        self.set_values()

        # Grid max build dimensions frame (which is within manufacturing requirements frame) widgets

        self.max_build_dim_label.grid(column=0, row=0, columnspan=6, pady=8)

        self.printer_label.grid(column=0, row=1, columnspan=3, sticky=W, padx=5)
        self.printer_combobox.grid(column=0, row=2, columnspan=3, sticky=W, padx=5, pady='0 2')
        self.printer_len_label.grid(column=0, row=3, sticky=W, padx=5, pady='2 2')
        self.printer_len_entry.grid(column=1, row=3, sticky=W, pady='2 2')
        self.printer_len_unit_cb.grid(column=2, row=3, sticky=W, pady='2 2')
        self.printer_width_label.grid(column=0, row=4, sticky=W, padx=5, pady='2 2')
        self.printer_width_entry.grid(column=1, row=4, sticky=W, pady='2 2')
        self.printer_width_unit_cb.grid(column=2, row=4, sticky=W, pady='2 2')
        self.printer_height_label.grid(column=0, row=5, sticky=W, padx=5, pady='2 5')
        self.printer_height_entry.grid(column=1, row=5, sticky=W, pady='2 5')
        self.printer_height_unit_cb.grid(column=2, row=5, sticky=W, pady='2 5')

        self.pmat_label.grid(column=3, row=1, sticky=W, padx='10 0')
        self.pmatlist_frame.grid(column=3, row=2, rowspan=6, sticky=E)

        # self.cutter_label.grid(column=3, row=1, columnspan=3, sticky=W, padx=5)
        # self.cutter_combobox.grid(column=3, row=2, columnspan=3, sticky=W, padx=5, pady='0 2')
        # self.cutter_len_label.grid(column=3, row=3, sticky=W, padx=5, pady='2 2')
        # self.cutter_len_entry.grid(column=4, row=3, sticky=W, pady='2 2')
        # self.cutter_len_unit_cb.grid(column=5, row=3, sticky=W, padx='0 5', pady='2 5')
        # self.cutter_width_label.grid(column=3, row=4, sticky=W, padx=5, pady='2 5')
        # self.cutter_width_entry.grid(column=4, row=4, sticky=W, pady='2 5')
        # self.cutter_width_unit_cb.grid(column=5, row=4, sticky=W, padx='0 5', pady='2 5')

        # Manage frame resizing
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)
        self.columnconfigure(5, weight=1)

    def set_values(self, event=None):
        """
        This method sets the values of the printer and cutter comboboxes based on the objects contained in the
        respective databases.
        """
        printer_db = shelve.open(db_location + 'printerdb')
        cutter_db = shelve.open(db_location + 'cutterdb')
        self.printer_combobox['width'] = len(self.printer_combobox.get()) + 2
        # self.cutter_combobox['width'] = len(self.cutter_combobox.get()) + 2
        if not printer_db:
            self.printer_combobox.current(0)
            self.printer_len_unit_cb.current(0)
            self.printer_width_unit_cb.current(0)
            self.printer_height_unit_cb.current(0)
        else:
            current_printer = printer_db[self.printer_combobox.get()]
            self.printer_len_entry['state'] = NORMAL
            self.printer_len_entry.delete(0, END)
            self.printer_len_entry.insert(0, '%0.3f' % current_printer.length['value'])
            self.printer_len_entry['state'] = 'readonly'
            self.printer_len_unit_cb.current(self.printer_len_unit_cb['values']
                                             .index(str(current_printer.length['unit'])))

            self.printer_width_entry['state'] = NORMAL
            self.printer_width_entry.delete(0, END)
            self.printer_width_entry.insert(0, '%0.3f' % current_printer.width['value'])
            self.printer_width_entry['state'] = 'readonly'
            self.printer_width_unit_cb.current(self.printer_width_unit_cb['values']
                                               .index(str(current_printer.width['unit'])))

            self.printer_height_entry['state'] = NORMAL
            self.printer_height_entry.delete(0, END)
            self.printer_height_entry.insert(0, '%0.3f' % current_printer.height['value'])
            self.printer_height_entry['state'] = 'readonly'
            self.printer_height_unit_cb.current(self.printer_height_unit_cb['values']
                                                .index(str(current_printer.height['unit'])))

        # if not cutter_db:
        #     self.cutter_combobox.current(0)
        #     self.cutter_len_unit_cb.current(0)
        #     self.cutter_width_unit_cb.current(0)
        # else:
        #     current_cutter = cutter_db[self.cutter_combobox.get()]
        #     self.cutter_len_entry['state'] = NORMAL
        #     self.cutter_len_entry.delete(0, END)
        #     self.cutter_len_entry.insert(0, '%0.3f' % current_cutter.length['value'])
        #     self.cutter_len_entry['state'] = 'readonly'
        #     self.cutter_len_unit_cb.current(self.cutter_len_unit_cb['values']
        #                                     .index(str(current_cutter.length['unit'])))
        #     self.cutter_width_entry['state'] = NORMAL
        #     self.cutter_width_entry.delete(0, END)
        #     self.cutter_width_entry.insert(0, '%0.3f' % current_cutter.width['value'])
        #     self.cutter_width_entry['state'] = 'readonly'
        #     self.cutter_width_unit_cb.current(self.cutter_width_unit_cb['values']
        #                                       .index(str(current_cutter.width['unit'])))
        printer_db.close()
        cutter_db.close()

    def new_unit_selection(self, event, entry_name):
        """
        Defines the behavior that occurs when a new unit is selected from a unit combobox. The entry corresponding to
        that unit combobox is converted from the previous units to the unit selected. This
        does not impact the value of the object in the database, which is always stored in base metric units.
        """
        p_db = shelve.open(db_location + 'printerdb')
        c_db = shelve.open(db_location + 'cutterdb')
        selected_printer = p_db[self.printer_combobox.get()]
        # selected_cutter = c_db[self.cutter_combobox.get()]
        if entry_name == 'printer_len':
            self.printer_len_entry['state'] = NORMAL
            self.printer_len_entry.delete(0, END)
            new_val = convert_unit(selected_printer.length['value'], 'm', self.printer_len_unit_cb.get())
            self.printer_len_entry.insert(0, '%0.3f' % new_val)
            self.printer_len_entry['state'] = 'readonly'
        elif entry_name == 'printer_width':
            self.printer_width_entry['state'] = NORMAL
            self.printer_width_entry.delete(0, END)
            new_val = convert_unit(selected_printer.width['value'], 'm', self.printer_width_unit_cb.get())
            self.printer_width_entry.insert(0, '%0.3f' % new_val)
            self.printer_width_entry['state'] = 'readonly'
        elif entry_name == 'printer_height':
            self.printer_height_entry['state'] = NORMAL
            self.printer_height_entry.delete(0, END)
            new_val = convert_unit(selected_printer.height['value'], 'm', self.printer_height_unit_cb.get())
            self.printer_height_entry.insert(0, '%0.3f' % new_val)
            self.printer_height_entry['state'] = 'readonly'
        # elif entry_name == 'cutter_len':
        #     self.cutter_len_entry['state'] = NORMAL
        #     self.cutter_len_entry.delete(0, END)
        #     new_val = convert_unit(selected_cutter.length['value'], 'm', self.cutter_len_unit_cb.get())
        #     self.cutter_len_entry.insert(0, '%0.3f' % new_val)
        #     self.cutter_len_entry['state'] = 'readonly'
        # elif entry_name == 'cutter_width':
        #     self.cutter_width_entry['state'] = NORMAL
        #     self.cutter_width_entry.delete(0, END)
        #     new_val = convert_unit(selected_cutter.width['value'], 'm', self.cutter_width_unit_cb.get())
        #     self.cutter_width_entry.insert(0, '%0.3f' % new_val)
        #     self.cutter_width_entry['state'] = 'readonly'
        p_db.close()
        c_db.close()

    def refresh_printer_cutter_lists(self):
        """
        This method refreshes the combobox lists. This is useful for when there are modifications made to either the
        printer or cutter databases during runtime. For example, if a user adds a printer to the database this method
        will refresh the combobox list allowing the user to select their newly added printer immediately.
        """
        p_db = shelve.open(db_location + 'printerdb')
        c_db = shelve.open(db_location + 'cutterdb')
        if p_db:
            self.printer_combobox['values'] = p_db.keys()
            self.printer_combobox.current(0)
        else:
            self.printer_combobox['values'] = ['No printers']
            self.printer_combobox.current(0)
        # if c_db:
        #     self.cutter_combobox['values'] = c_db.keys()
        #     self.cutter_combobox.current(0)
        # else:
        #     self.cutter_combobox['values'] = ['No cutters']
        #     self.cutter_combobox.current(0)
        p_db.close()
        c_db.close()


class PrintingMaterialFrame(ttk.Frame):
    """
    This is the ttk.Frame class which defines the pmat_frame within the manufacturing requirements frame. It is very
    similar to the SensorFrame class.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.master = master
        self.checkvar_list = []

        # Create subframe to put checkboxes in
        self.check_frame = ttk.Frame(self)

        # Create list of sensors
        self.refresh()

    def refresh(self):
        for widget in self.check_frame.children.values():
            widget.destroy()
        self.checkvar_list = []
        pmat_db = shelve.open(db_location + 'printingmaterialdb')
        for pmat in pmat_db.values():
            checkvar = IntVar()
            check = ttk.Checkbutton(self.check_frame, text=pmat.name, variable=checkvar)
            check.pack(pady=5, anchor=W)
            self.checkvar_list.append(checkvar)
        pmat_db.close()

        self.check_frame.pack_forget()
        self.check_frame.pack(side=LEFT, pady=3, padx=12)

    def get_selected(self):
        selected_list = []
        pmat_db = shelve.open(db_location + 'printingmaterialdb')
        # Loop through sensors
        for i, sensor in enumerate(pmat_db.values()):
            this_sensor = sensor
            # If sensor is selected add it to the selected list
            if self.checkvar_list[i].get() == 1:
                selected_list.append(this_sensor)
        pmat_db.close()
        return selected_list


class DataMgtFrame(ttk.Frame):
    """
    This is the database management frame within the main GUI window that holds the list of component databases, as well
    as the "View Database" and "Export Database(s)" buttons. IF DEVELOPERS IN THE FUTURE WANT TO ADD COMPONENT TYPES TO
    THE APPLICATION, THE VARIABLES "self.components" and "self.db_names" WILL NEED TO BE UPDATED APPROPRIATELY.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, borderwidth=2, relief='sunken')
        self.master = master

        # Create data management frame title, listbox, and view database button.
        self.data_mgt_title = ttk.Label(self, text='Database Management', font='Helvetica 10 bold')
        f = tkFont.Font(self.data_mgt_title, self.data_mgt_title.cget("font"))
        f.configure(underline=False)
        self.data_mgt_title.configure(font=f)

        self.components = ['Batteries', 'Propellers', 'Motors',
                           'Prop/Motor Combos', '3D Printers', 'Laser Cutters',
                           'Printing Materials', 'Cutting Materials', 'Sensors']
        self.db_names = ['batterydb', 'propellerdb', 'motordb',
                         'propmotorcombodb', 'printerdb', 'cutterdb',
                         'printingmaterialdb', 'cuttingmaterialdb', 'sensordb']
        self.component_lbox = Listbox(self, height=len(self.components), selectmode='browse')
        for comp in self.components:
            self.component_lbox.insert(END, comp)
        for i in xrange(0, len(self.components), 2):
            self.component_lbox.itemconfigure(i, background='#f0f0ff')
        self.component_lbox.select_set(0)
        self.view_db_button = ttk.Button(self, text='View Database', command=self.open_database_window)
        self.export_db_button = ttk.Button(self, text='Export Database(s)', command=self.open_export_window)

        # Pack widgets
        self.data_mgt_title.pack(padx=12, pady=12)
        self.component_lbox.pack()
        self.view_db_button.pack(pady=10)
        self.export_db_button.pack(pady='5 10')

        # Manage database management frame resizing
        self.columnconfigure(0, weight=1)

    def open_database_window(self):
        db_name = self.db_names[int(self.component_lbox.curselection()[0])]
        dbmanagement.DatabaseMgtWindow(self, db_name)

    def open_export_window(self):
        export.Exportdb(self)


class AlternativesFrame(ttk.Frame):
    """
    This is the main alternatives frame which takes up the bottom half of the main GUI window.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, borderwidth=2, relief='sunken')
        self.master = master
        self.alternatives = []
        self.f_alternatives = []
        self.last_constraints = []
        self.overwrite_decision = 'cancel'

        # Create subframes
        self.header_frame = ttk.Frame(self, padding='10 5 10 5')
        self.button_frame = ttk.Frame(self, padding=5)

        # Create widgets in header frame and grid
        self.find_alt_button = ttk.Button(self.header_frame, text='Find Alternatives', command=self.find_alternatives)
        self.trade_button = ttk.Button(self.header_frame, text='Explore Tradespace', command=self.tradespace)
        self.alt_infovar = StringVar()
        self.alt_info_label = ttk.Label(self.header_frame, textvariable=self.alt_infovar)
        self.sortby_label = ttk.Label(self.header_frame, text='Sort by:')
        # self.sortby_vals is an ordered dictionary object which contains (pretty name, attribute name) pairs for each
        # attribute which is to be included in the sort-by combobox.
        self.sortby_vals = OrderedDict([('total score', 'score'), ('endurance', 'max_endurance'),
                                        ('payload', 'max_payload'), ('build time', 'build_time'),
                                        ('weight', 'weight'), ('max dimension', 'max_dimension')])
        self.sortby_cb = ttk.Combobox(self.header_frame, values=self.sortby_vals.keys(), state='readonly',
                                      width=len(max(self.sortby_vals, key=len))+2)
        self.sortby_cb.current(0)
        self.sortby_cb.bind("<<ComboboxSelected>>", self.resort)

        self.find_alt_button.grid(column=0, row=0, rowspan=2, sticky='nsw')
        self.trade_button.grid(column=1, row=0, rowspan=2, sticky='nsw', padx='5 0')
        self.alt_info_label.grid(column=1, row=0, rowspan=2, sticky='e', padx='0 10')
        self.sortby_label.grid(column=2, row=0, sticky='sw')
        self.sortby_cb.grid(column=2, row=1, sticky='se')
        self.header_frame.columnconfigure(1, weight=1)
        self.header_frame.rowconfigure(0, weight=1)
        self.header_frame.rowconfigure(1, weight=1)

        # Create widgets in button_frame and pack
        self.exp_alts_button = ttk.Button(self.button_frame, text='Export feasible alts',
                                          command=self.export_alternatives)
        self.view_fail_stats_button = ttk.Button(self.button_frame, text='Failure Stats', command=self.view_fail_stats)
        self.build_model_button = ttk.Button(self.button_frame, text='Build Model', command=self.build_model)
        self.view_details_button = ttk.Button(self.button_frame, text='View Details', command=self.view_details)
        self.total_quit_button = ttk.Button(self.button_frame, text='Close Tool', command=self.close_tool)
        self.total_quit_button.pack(side=RIGHT)
        self.build_model_button.pack(side=RIGHT, padx='0 3')
        self.view_details_button.pack(side=RIGHT, padx=3)
        self.view_fail_stats_button.pack(side=RIGHT, padx='3 0')
        self.exp_alts_button.pack(side=RIGHT)

        # Create alternatives view frame
        self.alt_view_frame = VertScrolledFrame(self)

        # Pack subframes
        self.header_frame.pack(fill=X)
        self.alt_view_frame.pack(fill=BOTH, expand=YES)
        self.button_frame.pack(fill=X)

    def tradespace(self):
        """
        Open a new explore tradespace Toplevel. Called when the "Explore Tradespace" button is pressed and there exists
        at least one feasible alternative.
        """
        try:
            import matplotlib
        except ImportError:
            self.alt_infovar.set("matplotlib must be installed to explore tradespace.")
            return

        if self.f_alternatives:
            tradespace.Tradespace(self)
        else:
            self.alt_infovar.set("There are no feasible alternatives in the solution space.")

    def find_alternatives(self):
        self.last_constraints = self.get_constraints()
        constraints = self.last_constraints
        self.alternatives = alternatives_new.generate_alternatives(constraints)

        # Note that "if alt.feasible is True" in the logic below is actually what I mean. "if alt.feasible" fails
        # because the logical value of a python string (see quadrotor.Quadrotor.feasible) is True.
        self.f_alternatives = [alt for alt in self.alternatives if alt.feasible is True]

        infeasible_reasons = {}
        for alt in self.alternatives:
            if alt.feasible is not True:
                if alt.feasible[0] in infeasible_reasons:
                    infeasible_reasons[alt.feasible[0]] += 1
                else:
                    infeasible_reasons[alt.feasible[0]] = 1

        if not infeasible_reasons:
            info_str = "%d/%d feasible alternatives. Zero failures." % (len(self.f_alternatives),
                                                                        len(self.alternatives))
        else:
            sorted_reasons = sorted(infeasible_reasons, key=infeasible_reasons.get, reverse=True)
            info_str = "%d/%d feasible alternatives. Most popular fail: %s (%d)" % (len(self.f_alternatives),
                                                                                    len(self.alternatives),
                                                                                    sorted_reasons[0],
                                                                                    max(infeasible_reasons.values()))

        self.alt_infovar.set(info_str)

        # Now we want to score the feasible alternatives based on user-defined vehicle requirements weightings
        if self.f_alternatives:
            self.f_alternatives = alternatives_new.score_alternatives(self.f_alternatives,
                                                                  self.master.vehicle_req_frame.weights)
        self.alt_view_frame.interior.refresh_alt_sheet()
        self.alt_view_frame.interior.config(width=505)

    def get_constraints(self):
        """
        This method gets the vehicle requirements and other constraints from the GUI widgets and puts them into the
        'constraints' list for use in the vehicle sizing algorithm.

        Note that the quantities are being converted to English units. This is because the sizing algorithm located in
        the 'alternatives.is_feasible()' method uses many equations taken from a Georgia Tech tool originally written in
        English units. There is no documentation for these equations and therefore there is no way for me to convert the
        coefficients to metric without completely re-deriving the equations, which may be a project for another day.
        """
        p_db = shelve.open(db_location + 'printerdb')
        c_db = shelve.open(db_location + 'cutterdb')
        selected_printer = p_db[self.master.manuf_req_frame.max_build_dim_frame.printer_combobox.get()]
        #selected_cutter = c_db[self.master.manuf_req_frame.max_build_dim_frame.cutter_combobox.get()]

        endurance_req = float(self.master.vehicle_req_frame.endurance_var.get())   # Endurance in minutes
        payload_req = float(self.master.vehicle_req_frame.payload_var.get())
        payload_req = convert_unit(payload_req, self.master.vehicle_req_frame.payload_unit_cb.get(), 'lbf')
        max_weight = float(self.master.vehicle_req_frame.max_weight_var.get())
        max_weight = convert_unit(max_weight, self.master.vehicle_req_frame.max_weight_unit_cb.get(), 'lbf')
        max_size = float(self.master.vehicle_req_frame.max_size_var.get())
        max_size = convert_unit(max_size, self.master.vehicle_req_frame.max_size_unit_cb.get(), 'in')
        maneuverability = str(self.master.vehicle_req_frame.maneuver_var.get())
        cover_flag = self.master.vehicle_req_frame.cover_checkvar.get()
        p_len = convert_unit(selected_printer.length['value'], selected_printer.length['unit'], 'in')
        p_width = convert_unit(selected_printer.width['value'], selected_printer.width['unit'], 'in')
        p_height = convert_unit(selected_printer.height['value'], selected_printer.height['unit'], 'in')
        # c_len = convert_unit(selected_cutter.length['value'], selected_cutter.length['unit'], 'in')
        # c_width = convert_unit(selected_cutter.width['value'], selected_cutter.width['unit'], 'in')
        max_build_time = float(self.master.manuf_req_frame.build_time_var.get())   # Build time in hours
        # Get selected sensors
        sensors = self.master.sensor_frame.get_selected()
        pmaterials = self.master.manuf_req_frame.max_build_dim_frame.pmatlist_frame.get_selected()

        # If more constraints are added make sure to check alternatives.py. Some modifications may need to be made.
        constraints = [endurance_req, payload_req, max_weight, max_size, maneuverability,
                       p_len, p_width, p_height, max_build_time, sensors, pmaterials, cover_flag]

        p_db.close()
        c_db.close()
        return constraints

    def resort(self, event):
        self.alt_view_frame.interior.refresh_alt_sheet()

    def view_details(self):
        if not self.f_alternatives:
            return
        quad_selected_indx = self.alt_view_frame.interior.current_object_selection.get()
        selected_quad = self.f_alternatives[quad_selected_indx]
        ViewQuadDetails(self, selected_quad)

    def build_model(self):
        if not self.f_alternatives:
            return
        quad_selected_indx = self.alt_view_frame.interior.current_object_selection.get()
        selected_quad = self.f_alternatives[quad_selected_indx]
        try:
            import sw14
            sw14.build_model(selected_quad)
        except ImportError:
            self.alt_infovar.set("Required modules not installed for export.")
            return

    def view_fail_stats(self):
        if not self.alternatives:
            return
        ViewFailedStats(self, self.alternatives, self.last_constraints)

    def export_alternatives(self):
        """
        This method exports information about the feasible alternatives to a csv file for processing and analysis
        outside of the application. The performance metrics are common to all alternative architectures and are
        therefore held in the vehicle.perf_attr_dict (pretty names) and vehicle.perf_attr_names (real attr names) class
        attributes. The geometry information would be different for all vehicle architectures (quad, fixed wing, etc).
        Therefore the corresponding geometry information is held in quadrotor.geometry_attr_info
        """
        # Obtain user-specified directory in which to save the csv files
        dir_opt = {'initialdir': 'C:\\', 'mustexist': False, 'parent': self.master, 'title': 'Choose save directory.'}
        dirname = tkFileDialog.askdirectory(**dir_opt)

        # Create list of header labels for the csv file based on vehicle parts, vehicle performance metrics, and vehicle
        # type geometry metrics.
        header = []
        attr_names = []
        alternative_types = []
        for alt in self.f_alternatives:
            # If the type of the alternative (quadrotor.Quadrotor, etc) is new add the geometry and parts metrics to the
            # header.
            if type(alt) not in alternative_types:
                alternative_types.append(type(alt))
                for attr_info in alt.export_info:
                    attr_name = attr_info[1]
                    if attr_name not in attr_names:
                        attr_names.append(attr_name)
                        try:
                            pretty_name = attr_info[0]
                            unit = attr_info[2][0]
                            attr_str = pretty_name + ' (%s)' % unit
                        except KeyError:
                            attr_str = pretty_name
                        except IndexError:
                            attr_str = pretty_name
                        header.append(attr_str)

        # Save to a .csv file located at dirname/f_alternatives.csv
        try:
            with open(dirname+'/'+'f_alternatives'+'.csv', 'wb') as csvfile:
                writer = csv.writer(csvfile, dialect='excel')
                writer.writerow(header)
                # Create object rows
                for alt in self.f_alternatives:
                    alt_row = []
                    for attr in attr_names:
                        try:
                            attr_val = getattr(alt, attr)['value']
                        except TypeError:
                            attr_val = getattr(alt, attr)
                        except AttributeError:
                            attr_val = 'N/A'
                        alt_row.append(attr_val)
                    writer.writerow(alt_row)
                self.alt_infovar.set('Export successful.')
        except IOError as e:
            self.alt_infovar.set(str(e))

    def close_tool(self):
        close_message = "Are you sure you want to close the tool?"
        oc = dbmanagement.OverwriteConfirm(self, close_message)
        self.wait_window(oc)
        if self.overwrite_decision == 'confirmed':
            self.master.master.destroy()


class VertScrolledFrame(ttk.Frame):
    """
    Class for vertical scrolled frame. This blueprint for this code was written by stackOverflow user Gonzo.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = ttk.Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        self.canvas = Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=self.canvas.yview)

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = AlternativesSheet(self.canvas)
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor=NW)

        self.interior.bind('<Configure>', self._configure_interior)
        self.canvas.bind('<Configure>', self._configure_canvas)

    # track changes to the canvas and frame width and sync them,
    # also updating the scrollbar
    def _configure_interior(self, event):
        # update the scrollbars to match the size of the inner frame
        size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
        self.canvas.config(scrollregion="0 0 %s %s" % size)
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # update the canvas's width to fit the inner frame
            self.canvas.config(width=self.interior.winfo_reqwidth())

    def _configure_canvas(self, event):
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # update the inner frame's width to fill the canvas
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())


class AlternativesSheet(ttk.Frame):
    """
    This class defines the "spreadsheet" of feasible alternatives that appears on the main GUI after a user has selected
    "Find Alternatives".
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, width=500, height=300, padding='10 0 10 0')
        self.master = master
        self.current_object_selection = IntVar()
        self.radiobutton_list = []

        # Populate alternatives sheet
        self.refresh_alt_sheet()

    def refresh_alt_sheet(self):
        sortby_attr = self.master.master.master.sortby_vals[self.master.master.master.sortby_cb.get()]
        self.master.master.master.f_alternatives = sorted(self.master.master.master.f_alternatives,
                                                          key=lambda alt: getattr(alt, sortby_attr), reverse=True)

        self.radiobutton_list = []
        for widget in self.children.values():
            widget.destroy()

        row = 0
        for quad in self.master.master.master.f_alternatives:
            if row != 0:
                quad_frame = quad.display_frame(self)
                quad_frame.grid(column=1, row=row)
            else:
                quad_frame = quad.display_frame(self, header=True)
                quad_frame.grid(column=1, row=row, rowspan=2)
                row += 1
            radiobutton = ttk.Radiobutton(self, variable=self.current_object_selection,
                                          value=len(self.radiobutton_list))
            radiobutton.grid(column=0, row=row)
            self.radiobutton_list.append(radiobutton)
            row += 1


class ViewQuadDetails(Toplevel):
    """
    This class defines the toplevel window that appears when the user selects the "View Details" button on the main GUI.
    It simply displays all of the information pertaining to the selected feasible alternative.
    """
    def __init__(self, master, quad):
        Toplevel.__init__(self, master)
        self.master = master
        self.quad = quad
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))
        self.mainframe = ttk.Frame(self)
        self.mainframe.pack(fill=BOTH, expand=YES)

        # Create title label
        self.title = ttk.Label(self.mainframe, text='Quadrotor Details', font='-weight bold')
        self.title.pack(pady='15 5')

        # Create subframes and close button
        self.perf_frame = ttk.Frame(self.mainframe, borderwidth=2, relief=RIDGE, padding='5 15 5 10')
        self.perf_frame.pack(pady='15 8', padx=8)
        self.prop_frame = ttk.Frame(self.mainframe, borderwidth=2, relief=RIDGE, padding='5 10 5 10')
        self.prop_frame.pack(pady=8, padx=8)
        self.bat_frame = ttk.Frame(self.mainframe, borderwidth=2, relief=RIDGE, padding='5 10 5 10')
        self.bat_frame.pack(pady=8, padx=8)
        self.motor_frame = ttk.Frame(self.mainframe, borderwidth=2, relief=RIDGE, padding='5 10 5 15')
        self.motor_frame.pack(pady='8 15', padx=8)
        self.close_button = ttk.Button(self.mainframe, text='Close', command=self.destroy)
        self.close_button.pack(side=RIGHT, padx='0 5', pady='0 5')

        # Create frame titles
        perf_title = ttk.Label(self.perf_frame, text='Vehicle Performance', font='-weight bold')
        perf_title.pack()
        prop_title = ttk.Label(self.prop_frame, text='Propeller', font='-weight bold')
        prop_title.pack()
        bat_title = ttk.Label(self.bat_frame, text='Battery', font='-weight bold')
        bat_title.pack()
        motor_title = ttk.Label(self.motor_frame, text='Motor', font='-weight bold')
        motor_title.pack()

        # Create performance frame
        _perf_frame = quad.display_frame(self.perf_frame, header=True, mode='perf')
        _perf_frame.pack(side=LEFT)

        # Create propeller frame
        _prop_frame = quad.prop.display_frame(self.prop_frame, header=True)
        _prop_frame.pack(side=LEFT)

        # Create motor frame
        _motor_frame = quad.motor.display_frame(self.motor_frame, header=True)
        _motor_frame.pack(side=LEFT)

        # Create battery frame
        _bat_frame = quad.battery.display_frame(self.bat_frame, header=True)
        _bat_frame.pack(side=LEFT)


class ViewFailedStats(Toplevel):
    """
    This class defines the toplevel window that appears when the user clicks the Failure Stats button on the main GUI
    after finding alternatives for a set of constraints. It retrieves the alternative.feasible attribute values for the
    failed alternatives and organizes them so the user can see the most common reasons for alternative failure.
    """
    def __init__(self, master, quad_alts, constraints):
        Toplevel.__init__(self, master)
        self.master = master
        self.alternatives = quad_alts
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))

        endurance_req, payload_req, max_weight, max_size, maneuverability, \
            p_len, p_width, p_height, c_len, c_width, max_build_time, sensors = constraints
        sensors_list = ",".join([s.name for s in sensors])
        self.failed_alts = [alt for alt in self.alternatives if alt.feasible is not True]

        self.mainframe = ttk.Frame(self)
        self.mainframe.pack(fill=BOTH, expand=YES)
        constraints_dict = {"Max dimension too large.": max_size, "Hub too large for cutter": min(c_len, c_width),
                            "Arms too long for printer.": max(p_len, p_width), "Too heavy.": max_weight,
                            "Not enough payload capacity.": payload_req, "Not enough endurance.": endurance_req,
                            "Takes too long to build.": max_build_time,
                            "Could not place sensors in/on hub.": sensors_list}

        # Create and grid header and separator
        self.reason_header = ttk.Label(self.mainframe, text='Reason for failure')
        self.num_alts_header = ttk.Label(self.mainframe, text='# of alternatives')
        self.fail_val_header = ttk.Label(self.mainframe, text='Avg failed value')
        self.constraint_header = ttk.Label(self.mainframe, text='Constraint value')
        self.heading_separator = ttk.Separator(self.mainframe, orient=HORIZONTAL)
        self.reason_header.grid(column=0, row=0, sticky=W, pady='10 5', padx='15 10')
        self.num_alts_header.grid(column=1, row=0, sticky=W, pady='10 5', padx=10)
        self.fail_val_header.grid(column=2, row=0, sticky=W, pady='10 5', padx=10)
        self.constraint_header.grid(column=3, row=0, sticky=W, pady='10 5', padx='10 15')
        self.heading_separator.grid(column=0, row=1, columnspan=4, sticky='ew')

        infeasible_reasons = {}
        for alt in self.failed_alts:
            if alt.feasible[0] in infeasible_reasons:
                infeasible_reasons[alt.feasible[0]] += 1
            else:
                infeasible_reasons[alt.feasible[0]] = 1
        sorted_reasons = sorted(infeasible_reasons, key=infeasible_reasons.get, reverse=True)

        for grid_row, reason in enumerate(sorted_reasons, start=2):
            reason_label = ttk.Label(self.mainframe, text=reason)
            num_alts_label = ttk.Label(self.mainframe, text=str(infeasible_reasons[reason]))
            fail_sum = 0
            try:
                for alt in self.failed_alts:
                    if alt.feasible[0] == reason:
                        fail_sum += alt.feasible[1]
                avg_fail = float(fail_sum) / infeasible_reasons[reason]
                avg_fail_label = ttk.Label(self.mainframe, text="%0.2f" % avg_fail)
            except TypeError:
                avg_fail_label = ttk.Label(self.mainframe, text='N/A')
            constraint_label = ttk.Label(self.mainframe, text=str(constraints_dict[reason]))

            reason_label.grid(column=0, row=grid_row, sticky=W, pady=5, padx='15 10')
            num_alts_label.grid(column=1, row=grid_row, pady=5, padx=10)
            avg_fail_label.grid(column=2, row=grid_row, pady=5, padx=10)
            constraint_label.grid(column=3, row=grid_row, pady=5, padx=10)


def main():
    """
    This is the main function that creates the root Tk window. The mainframe variable is an instance of the QuadGUI
    frame class defined above. The QuadGUI instance will be the parent widget for the rest of the application.
    """
    # First add the directory (in this case masr_design_tool) of the component classes (battery, sensor, propeller, etc)
    # to the system path so that Python can find the modules when it needs to import them.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    root = Tk()
    xpos, ypos = get_win_place(root)
    root.geometry('+%d+%d' % (xpos, ypos))
    root.title("Quadrotor Sizing Tool")
    mainframe = QuadGUI(root)
    mainframe.grid(column=0, row=0, sticky=(N, S, E, W))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.protocol('WM_DELETE_WINDOW', mainframe.alternatives_frame.close_tool)
    root.mainloop()

if __name__ == '__main__':
    main()