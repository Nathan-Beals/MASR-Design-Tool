from collections import OrderedDict
try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk
from unitconversion import convert_unit


class Displayable(object):
    """
    This class is inherited by all component classes and contains methods that return tkk frames (and sometimes
    data structures holding the children of the frame) for displaying the component objects.
    """
    pretty_attr_dict = OrderedDict()
    real_attr_names = []
    perf_attr_dict = None
    perf_attr_names = None

    @classmethod
    def obj_input_frame(cls, master):
        """
        This is a classmethod which returns a ttk Frame with empty widgets organized according to cls.pretty_attr_dict
        (note that this class attribute is always overridden in the child classes). It also returns an ordered dictionary
        containing the frame's entry and combobox widgets so that the calling function has access to the values for
        subsequent use. This method is currently only called by the dbmanagement.AddObjectWindow.__init__ method.
        """
        mainframe = ttk.Frame(master, padding=3, borderwidth=2, relief=RIDGE)
        col = 0
        object_info = OrderedDict()
        for attr in cls.pretty_attr_dict:
            mainframe.columnconfigure(col, weight=1)
            # If the attributes have units we need to add a combobox for unit selection
            if cls.pretty_attr_dict[attr]:
                temp_attr_label = ttk.Label(mainframe, text=attr)
                temp_attr_label.grid(column=col, row=0, columnspan=2, padx=3, pady=5, sticky=S)

                temp_value_entry = ttk.Entry(mainframe, width=13-len(max(cls.pretty_attr_dict[attr]))+1)
                temp_value_entry.grid(column=col, row=2, padx='3 0', pady=5)

                col += 1
                temp_unit_cb = ttk.Combobox(mainframe, state='readonly', values=cls.pretty_attr_dict[attr],
                                            width=len(max(cls.pretty_attr_dict[attr]))+1)
                temp_unit_cb.current(0)
                temp_unit_cb.grid(column=col, row=2, padx='0 3', pady=5)
                object_info[attr] = [temp_value_entry, temp_unit_cb]
            else:
                temp_attr_label = ttk.Label(mainframe, text=attr)
                temp_attr_label.grid(column=col, row=0, columnspan=2, padx=3, pady=5, sticky=S)

                temp_value_entry = ttk.Entry(mainframe, width=13)
                temp_value_entry.grid(column=col, row=2, columnspan=2, padx=3, pady=5)
                object_info[attr] = [temp_value_entry]
                col += 1
            col += 1

        heading_separator = ttk.Separator(mainframe, orient=HORIZONTAL)
        heading_separator.grid(column=0, row=1, columnspan=col, sticky=(E, W))

        return mainframe, object_info

    def __init__(self):
        """
        Constructor. Generally component classes will not inherit non-method attributes from this class. 'name' is
        necessary because I wanted to define the __str__ method here, since it has to do with class display. The name
        attribute will be overridden.
        """
        self.name = 'no name'

    def __str__(self):
        return self.name

    def display_frame(self, master, header=False, return_widgets=False, mode='regular'):
        """
        This method displays self by creating a ttk Frame and using the information in self.pretty_attr_dict to
        format a GUI containing self's attributes.

        If the input 'header' is True the method will include a header row containing the attribute names in
        self.pretty_attr_dict in the frame returned to the caller. This option is usually used for the first object
        displayed in a list, or when an object's information is displayed by itself.

        The 'return_widgets' flag tells the method whether or not to return a dictionary containing the widgets
        contained in the frame for later use by the caller.

        The 'mode' input can either be 'regular' or 'perf'. Currently this doesn't do anything and regular is set to
        default. A todo is to generalize the method so that it does not need to be overwritten by children. Currently
        the battery, propmotorcombo, and quadrotor classes override this method due to differences in either the
        display frame method itself or the new_unit_selection function.
        """
        mainframe = ttk.Frame(master)

        if mode == 'regular':
            display_dictionary = self.pretty_attr_dict
            display_real_names = self.real_attr_names
        else:
            display_dictionary = self.perf_attr_dict
            display_real_names = self.perf_attr_names

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
                entry_width = max([10, len(display_dictionary.keys()[attr_col])])
                temp_val_entry = ttk.Entry(mainframe, textvariable=temp_textvariable, width=entry_width)
                temp_val_entry.grid(column=grid_col, row=2, padx='3 0', pady=5)
                temp_val_entry.insert(0, "%0.3f" % attr_entry_value)
                temp_val_entry['state'] = 'readonly'
                mainframe.columnconfigure(grid_col, weight=1)
                grid_col += 1
                temp_unit_cb = ttk.Combobox(mainframe, state='readonly',
                                            values=display_dictionary.values()[attr_col],
                                            width=len(max(display_dictionary.values()[attr_col]))+2)
                temp_unit_cb.bind("<<ComboboxSelected>>", lambda event, obj_attr=attr:
                                  new_unit_selection(event, obj_attr))
                temp_unit_cb.current(0)
                temp_unit_cb.grid(column=grid_col, row=2, padx='0 3', pady=5)
                # The current_obj_vars list contains the information for each object's widgets in the form:
                # [value entry widget, value textvariable, unit combobox, "old" unit]
                # "old" unit is initialized and then updates whenever the user selects a new unit. This is included so
                # that both the old unit and new unit are available within new_unit_selection.
                current_obj_vars[attr] = [temp_val_entry, temp_textvariable, temp_unit_cb, temp_unit_cb.get()]
            else:
                attr_entry_value = attr_val
                temp_val_entry = ttk.Entry(mainframe)
                temp_val_entry.grid(column=grid_col, row=2, columnspan=2, padx=3, pady=5)
                temp_val_entry.insert(0, str(attr_entry_value))
                if attr == 'name':
                    temp_val_entry['width'] = 20
                else:
                    entry_width = max([10, len(display_dictionary.keys()[attr_col])])
                    temp_val_entry['width'] = entry_width
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
            old_unit = current_obj_vars[obj_attr][3]
            current_obj_vars[obj_attr][3] = new_unit
            this_attr_val = getattr(self, obj_attr)
            if master.master.mode == 'edit':
                this_textvariable.set("%0.3f" %
                                      convert_unit(float(this_textvariable.get()), old_unit, new_unit))
            else:
                this_textvariable.set("%0.3f" % convert_unit(this_attr_val['value'], this_attr_val['unit'], new_unit))

        if return_widgets:
            return mainframe, current_obj_vars
        else:
            return mainframe
