from displayable import Displayable
from collections import OrderedDict
from tools import convert_unit, CapacityConvError
try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk


class Battery(Displayable):
    pretty_attr_dict = OrderedDict([('Name', []), ('Type', []), ('Weight', ['N', 'lbf', 'kg']),
                                    ('Capacity', ['Wh', 'mAh']), ('Voltage', ['V']), ('Cells', []),
                                    ('Cost (USD)', []), ('XDim', ['m', 'cm', 'in']), ('YDim', ['m', 'cm', 'in']),
                                    ('ZDim', ['m', 'cm', 'in'])])
    real_attr_names = ['name', 'battery_type', 'weight', 'capacity', 'voltage', 'cells', 'cost', 'xdim', 'ydim', 'zdim']
    pretty_str = 'battery'

    def __init__(self, attr_list):
        """
        The relationship between mass and capacity is given in Gur and Rosen in units of kg and Wh:
        Capacity[W*h] = 4.04 * (mass[kg])**2 + 139 * mass[kg] + 0.0155

        Note: The inputs to the class are lists of either length 1 if the input has no units or length 2 if the input
        has units; e.g., weight = [weight_val, weight_unit]
        """
        Displayable.__init__(self)
        name, battery_type, weight, mass, capacity, voltage, \
            cells, cost, xdim, ydim, zdim = self.process_input(attr_list)

        self.name = name
        self.battery_type = battery_type
        self.weight = weight
        self.mass = mass
        self.capacity = capacity
        self.voltage = voltage
        self.cells = cells
        self.cost = cost
        self.xdim = xdim
        self.ydim = ydim
        self.zdim = zdim

    @staticmethod
    def process_input(attr_list):
        # Object must have a name
        if attr_list[0][0] is None:
            raise ValueError("Battery must have a name.")
        else:
            name = str(attr_list[0][0])
        battery_type = attr_list[1][0]
        try:
            cost = float(attr_list[6][0])
        except ValueError:
            cost = None
        except TypeError:
            cost = None
        if attr_list[7][0] is None:
            raise ValueError("Battery must have an X-dimension.")
        else:
            xdim = {'value': convert_unit(float(attr_list[7][0]), str(attr_list[7][1]), 'std_metric'),
                    'unit': 'm'}
        if attr_list[8][0] is None:
            raise ValueError("Battery must have a Y-dimension.")
        else:
            ydim = {'value': convert_unit(float(attr_list[8][0]), str(attr_list[8][1]), 'std_metric'),
                    'unit': 'm'}
        if attr_list[9][0] is None:
            raise ValueError("Battery must have a Z-dimension.")
        else:
            zdim = {'value': convert_unit(float(attr_list[9][0]), str(attr_list[9][1]), 'std_metric'),
                    'unit': 'm'}

        # Apply known relationships for LiPo batteries
        if battery_type is None or battery_type.lower() == 'lipo':
            # Take care of voltage and cell inputs
            if attr_list[4][0] is None and attr_list[5][0] is None:
                raise ValueError("Battery must have a rated voltage or number of cells.")
            elif attr_list[4][0] is None and attr_list[5][0] is not None:
                cells = int(attr_list[5][0])
                voltage = {'value': cells * 3.7, 'unit': str(attr_list[4][1])}
            elif attr_list[4][0] is not None and attr_list[5][0] is None:
                voltage = {'value': float(attr_list[4][0]), 'unit': str(attr_list[4][1])}
                cells = int(round(voltage['value']/3.7))
            else:
                voltage = {'value': float(attr_list[4][0]), 'unit': str(attr_list[4][1])}
                cells = int(attr_list[5][0])

            a = 4.04
            b = 139
            c = 0.0155
            # Object must be initialized with a capacity and/or a weight
            if attr_list[2][0] is None and attr_list[3][0] is None:
                raise ValueError("Battery must have a capacity and/or weight.")
            # If weight is not given but capacity is, solve Gur and Rosen quadratic for mass and convert to weight
            elif attr_list[2][0] is None:
                capacity = {'value': convert_unit(float(attr_list[3][0]), str(attr_list[3][1]),
                                                  'std_metric', voltage['value']), 'unit': 'Wh'}
                quad_sqrt = (b**2 - 4*a*(c-capacity['value']))**0.5
                if quad_sqrt > abs(b):
                    mass = {'value': (-b + quad_sqrt) / (2*a), 'unit': 'kg'}
                    weight = {'value': mass['value'] * 9.81, 'unit': 'N'}
                else:
                    raise ValueError("Battery capacity out of range")
            # If weight is given but capacity is not, solve Gur and Rosen quadratic for capacity
            elif attr_list[3][0] is None:
                weight = {'value': convert_unit(float(attr_list[2][0]), str(attr_list[2][1]),
                                                'std_metric'), 'unit': 'N'}
                mass = {'value': weight['value']/9.81, 'unit': 'kg'}
                capacity = {'value': a*mass['value']**2 + b*mass['value'] + c, 'unit': 'Wh'}
            else:
                weight = {'value': convert_unit(float(attr_list[2][0]), str(attr_list[2][1]),
                                                'std_metric'), 'unit': 'N'}
                mass = {'value': weight['value']/9.81, 'unit': 'kg'}
                capacity = {'value': convert_unit(float(attr_list[3][0]), str(attr_list[3][1]),
                                                  'std_metric', voltage['value']), 'unit': 'Wh'}
        else:   # For other battery types assume all information is given
            try:
                weight = {'value': convert_unit(float(attr_list[2][0]), attr_list[2][1], 'std_metric'),
                          'unit': 'N'}
                mass = {'value': weight['value']/9.81, 'unit': 'kg'}
                voltage = {'value': float(attr_list[4][0]), 'unit': 'V'}
                capacity = {'value': convert_unit(float(attr_list[3][0]), attr_list[3][1], 'std_metric',
                                                  voltage['value']), 'unit': 'Wh'}
                cells = int(attr_list[5][0])
            except TypeError:
                raise ValueError("If entering non-LiPo battery, must give all info.")
        return [name, battery_type, weight, mass, capacity, voltage, cells, cost, xdim, ydim, zdim]

    def display_frame(self, master, header=False, return_widgets=False, mode='regular'):
        """
        See displayable.Displayable.display_frame() for a description of this method.
        """
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
                    temp_val_entry['width'] = 20
                else:
                    temp_val_entry['width'] = 10
                temp_val_entry['state'] = 'readonly'
                current_obj_vars[attr] = [temp_val_entry]
                mainframe.columnconfigure(grid_col, weight=1)
                grid_col += 1
            grid_col += 1

        def new_unit_selection(event, obj_attr):
            """
            See displayable.Displayable.display_frame.new_unit_selection() for a description of this method.
            """
            this_cb = event.widget
            this_textvariable = current_obj_vars[obj_attr][1]
            new_unit = this_cb.get()
            this_attr_val = getattr(self, obj_attr)
            try:
                this_textvariable.set("%0.3f" % convert_unit(this_attr_val['value'], this_attr_val['unit'], new_unit))
            except CapacityConvError:
                voltage = self.voltage['value']
                this_textvariable.set("%0.3f" % convert_unit(this_attr_val['value'], this_attr_val['unit'], new_unit,
                                                             voltage))

        if return_widgets:
            return mainframe, current_obj_vars
        else:
            return mainframe