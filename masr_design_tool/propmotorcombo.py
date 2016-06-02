from displayable import Displayable
from collections import OrderedDict
from tools import convert_unit
try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk


class Propmotorcombo(Displayable):
    pretty_attr_dict = OrderedDict([('Motor/Propeller', []), ('Test Battery Voltage', ['V']),
                                    ('Max Thrust', ['N', 'lbf', 'kg'])])
    add_obj_header_dict = OrderedDict([('Current (A)', []), ('Voltage (V)', []), ('Power (W)', []), ('RPM', []),
                                       ('Throttle', []), ('Thrust', ['N', 'lbf', 'kg'])])
    real_attr_names = ['name', 'test_bat_volt_rating', 'max_thrust']
    pretty_str = 'motor/propeller combo'

    def __init__(self, attr_list):
        Displayable.__init__(self)
        motor, prop, test_bat_volt_rating, current_vec, voltage_vec, pwr_vec,\
            rpm_vec, throttle_vec, thrust_vec = self.process_input(attr_list)

        self.motor = motor
        self.prop = prop
        self.test_bat_volt_rating = test_bat_volt_rating
        self.current_vec = current_vec
        self.voltage_vec = voltage_vec
        self.pwr_vec = pwr_vec
        self.rpm_vec = rpm_vec
        self.throttle_vec = throttle_vec
        self.thrust_vec = thrust_vec
        self.max_thrust = {'value': max(self.thrust_vec['value']), 'unit': self.thrust_vec['unit']}
        self.name = "%s/%s" % (self.motor.name, self.prop.name)

    @staticmethod
    def process_input(attr_list):
        motor = attr_list[0][0]
        prop = attr_list[1][0]
        test_bat_volt_rating = {'value': float(attr_list[2][0]), 'unit': 'V'}
        current_vec = {'value': [float(val) for val in attr_list[3]], 'unit': 'A'}
        voltage_vec = {'value': [float(val) for val in attr_list[4]], 'unit': 'V'}
        pwr_vec = {'value': [float(val) for val in attr_list[5]], 'unit': 'W'}
        rpm_vec = attr_list[6]
        throttle_vec = attr_list[7]
        thrust_val_list = [convert_unit(float(val), str(attr_list[8][1]), 'std_metric') for val in attr_list[8][0]]
        thrust_vec = {'value': thrust_val_list, 'unit': 'N'}
        return [motor, prop, test_bat_volt_rating, current_vec, voltage_vec, pwr_vec, rpm_vec, throttle_vec, thrust_vec]

    def display_frame(self, master, header=False, return_widgets=False, mode='regular'):
        mainframe = ttk.Frame(master)

        if header:
            label_col = 1
            for attr in self.pretty_attr_dict:
                mainframe.columnconfigure(label_col, weight=1)
                temp_label = ttk.Label(mainframe, text=attr)
                temp_label.grid(column=label_col, row=0, columnspan=2, padx=3, pady=5, sticky=S)
                label_col += 2
            heading_separator = ttk.Separator(mainframe, orient=HORIZONTAL)
            heading_separator.grid(column=1, row=1, columnspan=label_col, sticky=(E, W))

        grid_col = 1
        current_obj_vars = OrderedDict()
        for attr_col, attr in enumerate(self.real_attr_names):
            attr_val = getattr(self, attr)
            if isinstance(attr_val, dict):
                attr_entry_value = attr_val['value']
                temp_textvariable = StringVar()
                temp_val_entry = ttk.Entry(mainframe, textvariable=temp_textvariable, width=10)
                temp_val_entry.grid(column=grid_col, row=2, padx='3 0', pady=5)
                temp_val_entry.insert(0, "%0.3f" % attr_entry_value)
                temp_val_entry['state'] = 'readonly'
                mainframe.columnconfigure(grid_col, weight=1)
                grid_col += 1
                temp_unit_cb = ttk.Combobox(mainframe, state='readonly',
                                            values=self.pretty_attr_dict.values()[attr_col],
                                            width=len(max(self.pretty_attr_dict.values()[attr_col]))+2)
                temp_unit_cb.bind("<<ComboboxSelected>>", lambda event, obj_attr=attr:
                                  new_unit_selection(event, obj_attr))
                temp_unit_cb.current(0)
                temp_unit_cb.grid(column=grid_col, row=2, padx='0 3', pady=5)
                current_obj_vars[attr] = [temp_val_entry, temp_textvariable, temp_unit_cb]
            else:
                attr_entry_value = attr_val
                temp_val_entry = ttk.Entry(mainframe)
                temp_val_entry.grid(column=grid_col, row=2, columnspan=2, padx=3, pady=5)
                temp_val_entry.insert(0, str(attr_entry_value))
                if attr == 'name':
                    temp_val_entry['width'] = 30
                else:
                    temp_val_entry['width'] = 10
                temp_val_entry['state'] = 'readonly'
                current_obj_vars[attr] = [temp_val_entry]
                mainframe.columnconfigure(grid_col, weight=1)
                grid_col += 1
            grid_col += 1

        def new_unit_selection(event, obj_attr):
            this_cb = event.widget
            this_textvariable = current_obj_vars[obj_attr][1]
            new_unit = this_cb.get()
            this_attr_val = getattr(self, obj_attr)
            this_textvariable.set("%0.3f" % convert_unit(this_attr_val['value'], this_attr_val['unit'], new_unit))

        if return_widgets:
            return mainframe, current_obj_vars
        else:
            return mainframe
