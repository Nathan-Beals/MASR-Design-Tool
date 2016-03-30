from vehicle import Vehicle
from collections import OrderedDict
from unitconversion import convert_unit
try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk


class Quadrotor(Vehicle):
    # Note that the default pretty_attr_dict and real_attr_names variables have not been overridden. Instead these
    # shortened versions are used in the overridden display_frame method below.
    short_pretty_attr = OrderedDict([('Propeller', ()), ('Motor', ()), ('Battery', ()), ('Endurance', ('min', 'hr')),
                                     ('Payload', ('N', 'lbf', 'kg')), ('Score', ())])
    short_attr_names = ['prop', 'motor', 'battery', 'max_endurance', 'max_payload', 'score']
    geometry_attrs = [('Hub Size', 'hub_size', ('m', 'in', 'cm')),
                      ('Hub Separation', 'hub_separation', ('m', 'in', 'cm')),
                      ('Arm Length', 'arm_len', ('m', 'in', 'cm'))]
    part_attrs = [('P/M Combo', 'pmcombo'), ('Battery', 'battery'), ('Print Material', 'pmaterial')]

    # If you want to export data to the csv file when the alternative is exported append the info to the export_info
    # list using a tuple of the format ('Pretty name', 'attribute real name', unit list (if applicable))
    export_info = part_attrs + Vehicle.perf_attrs_export + geometry_attrs

    def __init__(self, pmcombo, battery, pmaterial, cmaterial, geometry=None, feasible=True, score=0, pareto=False):
        """

        The input "feasible" will be true by default. If the quad is found to be infeasible the value will be changed
        to a tuple. The first entry will be a string explaining the first reason why the alternative was rejected
        (but not necessarily the only reason it would have been rejected). The second entry is the % (e.g., 0.15) off
        the vehicle spec was from the requirement.
        """

        # Call vehicle constructor to initialize performance parameters
        Vehicle.__init__(self)

        if geometry is None:
            geometry = [0] * 5

        self.hub_size, self.hub_separation, self.hub_grid, self.arm_len, self.hub_corner_len = geometry

        self.pmcombo = pmcombo
        self.prop = self.pmcombo.prop
        self.motor = self.pmcombo.motor
        self.battery = battery
        self.pmaterial = pmaterial
        self.cmaterial = cmaterial
        self.feasible = feasible
        self.score = score
        self.pareto = pareto
        self.name = "(%s, %s)" % (self.pmcombo.name, self.battery.name)

    def __str__(self):
        return self.name

    def set_geometry(self, geometry):
        """
        Set geometry method for when the geometry needs to be changed after initialization of the object,
        specifically when the vehicle object has been determined to be feasible and geometry values have been
        calculated.
        """
        hub_size, hub_separation, hub_grid, arm_len, hub_corner_len = geometry
        self.hub_size = {'value': hub_size, 'unit': 'm'}
        self.hub_separation = {'value': hub_separation, 'unit': 'm'}
        self.hub_grid = hub_grid
        self.arm_len = {'value': arm_len, 'unit': 'm'}
        self.hub_corner_len = {'value': hub_corner_len, 'unit': 'm'}

    def display_frame(self, master, header=False, mode='regular', return_widgets=False):
        """
        This method takes in a Tkinter or ttk widget as the master widget and constructs a ttk Frame with the object
        information. The information inserted into the frame is determined by either the self.short_pretty_attr
        dictionary (mode='regular'), or the self.perf_attr_dict (mode='perf'). The method then returns the frame,
        called 'mainframe', containing the object information widgets.

        If the 'header' input is True the mainframe that is returned will also contain a header. This is by default
        false.
        """
        if mode == 'regular':
            display_dictionary = self.short_pretty_attr
            display_real_names = self.short_attr_names
        else:
            display_dictionary = self.perf_attr_dict
            display_real_names = self.perf_attr_names

        mainframe = ttk.Frame(master)

        if header:
            label_col = 1
            for attr in display_dictionary:
                mainframe.columnconfigure(label_col, weight=1)
                temp_label = ttk.Label(mainframe, text=attr)
                temp_label.grid(column=label_col, row=0, columnspan=2, padx=3, pady=5, sticky=S)
                label_col += 2
            heading_separator = ttk.Separator(mainframe, orient=HORIZONTAL)
            heading_separator.grid(column=1, row=1, columnspan=label_col, sticky=(E, W))

        grid_col = 1
        current_obj_vars = OrderedDict()
        for attr_col, attr in enumerate(display_real_names):
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
                                            values=display_dictionary.values()[attr_col],
                                            width=len(max(display_dictionary.values()[attr_col]))+1)
                temp_unit_cb.bind("<<ComboboxSelected>>", lambda event, obj_attr=attr:
                                  new_unit_selection(event, obj_attr))
                temp_unit_cb.current(0)
                temp_unit_cb.grid(column=grid_col, row=2, padx='0 3', pady=5)
                current_obj_vars[attr] = [temp_val_entry, temp_textvariable, temp_unit_cb]
            else:
                attr_entry_value = attr_val
                temp_val_entry = ttk.Entry(mainframe)
                temp_val_entry.grid(column=grid_col, row=2, columnspan=2, padx=3, pady=5)
                try:
                    temp_val_entry.insert(0, "%0.2f" % attr_entry_value)
                except TypeError:
                    temp_val_entry.insert(0, str(attr_entry_value))
                # format entry widget widths
                if attr in ['prop', 'motor', 'battery']:
                    temp_val_entry['width'] = 20
                elif attr in ['max_endurance']:
                    temp_val_entry['width'] = len('Endurance (min)') + 1
                else:
                    temp_val_entry['width'] = 8
                temp_val_entry['state'] = 'readonly'
                current_obj_vars[attr] = [temp_val_entry]
                mainframe.columnconfigure(grid_col, weight=1)
                grid_col += 1
            grid_col += 1

        def new_unit_selection(event, obj_attr):
            """
            This is an event handler for when a combobox value changes (i.e., the user wants to do a unit conversion).
            The function simply changes the value of the textvariable linked to the attribute entry according to the
            current value of the unit combobox.
            """
            this_cb = event.widget
            this_textvariable = current_obj_vars[obj_attr][1]
            new_unit = this_cb.get()
            this_attr_val = getattr(self, obj_attr)
            this_textvariable.set("%0.3f" % convert_unit(this_attr_val['value'], this_attr_val['unit'], new_unit))

        if return_widgets:
            return mainframe, current_obj_vars
        else:
            return mainframe