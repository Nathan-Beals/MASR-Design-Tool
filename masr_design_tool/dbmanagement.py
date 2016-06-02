try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk
from collections import OrderedDict
import shelve
import tools
from winplace import get_win_place
import dblocation

"""
This module contains all of the classes relating to the database management frame of the main GUI. All functionality
relating to database management are contained herein. Widget structure is:

                                        DatabaseMgtWindow
                                        |       |       |
                                DatabaseFrame   |       |
                                    AddObjectWindow   AddEditPMComboWindow
                                                |       |           |
                                            OverwriteConfirm      AddPMComboVectorFrame
"""
db_location = dblocation.db_location


class DatabaseMgtWindow(Toplevel):
    """
    The main database management window. Consists of the database frame (defined in the following class) and add, edit,
    and close buttons.
    """
    def __init__(self, master, db_name):
        Toplevel.__init__(self, master)
        self.master = master
        self.db_name = db_name
        self.db_location = db_location
        self.class_name = self.db_name[:-2].capitalize()
        pretty_class_str = getattr(__import__(self.class_name.lower()), self.class_name).pretty_str
        self.title(pretty_class_str.capitalize() + " Database")
        self.mode = 'view'
        self.overwrite_decision = 'cancel'

        # Place window
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))

        # Create subframes within database management window
        self.db_frame = DatabaseFrame(self)
        self.button_frame = ttk.Frame(self, padding=5)

        # Create add, edit, close, cancel, and save changes buttons in button frame
        self.add_button = ttk.Button(self.button_frame, text='Add', command=self.launch_add_object_window)
        self.edit_button = ttk.Button(self.button_frame, text='Edit', command=self.edit_objects)
        self.close_button = ttk.Button(self.button_frame, text='Close', command=self.close_window)
        self.cancel_button = ttk.Button(self.button_frame, text='Cancel', command=self.cancel_edit)
        self.save_changes_button = ttk.Button(self.button_frame, text='Save Changes', command=self.save_edits)
        self.delete_button = ttk.Button(self.button_frame, text='Delete Object', command=self.delete_obj)

        # Create edit message label in button frame
        self.edit_message = StringVar()
        self.edit_message_label = ttk.Label(self.button_frame, textvariable=self.edit_message)

        # Pack button frame widgets
        self.close_button.pack(side=RIGHT)
        self.edit_button.pack(side=RIGHT)
        self.add_button.pack(side=RIGHT)
        self.edit_message_label.pack(side=LEFT)

        # Pack subframes
        self.db_frame.pack(fill=BOTH, expand=YES)
        self.button_frame.pack(fill=X)

        # Handle resizing
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def launch_add_object_window(self):
        """
        This method is called when the user presses self.add_button. It's main purpose is to check whether or not
        the user wishes to add a prop/motor combo or something else and calls the appropriate toplevel window to achieve
        this.
        """
        if self.db_name == 'propmotorcombodb':
            # Obtain dictionary of available motors and propellers
            motor_db = shelve.open(self.db_location+'motordb')
            prop_db = shelve.open(self.db_location+'propellerdb')
            if not motor_db:
                motor_db.close()
                prop_db.close()
                self.edit_message.set("There must be at least one motor in the motor database.")
            elif not prop_db:
                motor_db.close()
                prop_db.close()
                self.edit_message.set("There must be at least one propeller in the propeller database.")
            else:
                AddEditPMComboWindow(self, 'add')
        else:
            AddObjectWindow(self)

    def edit_objects(self):
        """
        This method is called when the user presses the self.edit_button.
        """
        if self.db_name != 'propmotorcombodb':
            self.mode = 'edit'
            self.db_frame.refresh_db_frame()
            self.db_frame.writable_entries()
            # Temporarily remove add, edit, and close buttons.
            self.add_button.pack_forget()
            self.edit_button.pack_forget()
            self.close_button.pack_forget()
            # Replace with save changes and cancel buttons, as well as edit message label
            self.save_changes_button.pack(side=RIGHT)
            self.delete_button.pack(side=RIGHT)
            self.cancel_button.pack(side=RIGHT)
            self.edit_message_label.pack(side=LEFT)
        else:
            if not self.db_frame.current_object_selection.get():
                self.edit_message.set("Select an object to edit.")
            else:
                AddEditPMComboWindow(self, 'edit')
                self.db_frame.current_object_selection = StringVar()
                self.db_frame.refresh_db_frame()

    def cancel_edit(self):
        """
        Returns the db management window to view mode, which returns entries to readonly and replaces the edit mode
        buttons with the view mode buttons.
        """
        self.mode = 'view'
        self.db_frame.refresh_db_frame()

        self.edit_message.set("No changes made to database.")
        self.cancel_button.pack_forget()
        self.delete_button.pack_forget()
        self.save_changes_button.pack_forget()
        self.close_button.pack(side=RIGHT)
        self.edit_button.pack(side=RIGHT)
        self.add_button.pack(side=RIGHT)

    def save_edits(self):
        # First delete all items in the existing database. The "edit" is actually a complete updating using the info
        # from the writable entry widgets. This makes it easier to enforce the rules associated with certain object
        # attributes that are enforced during initialization of the object. Create a copy of the old database
        # temporarily in case something goes wrong after the old database is deleated.
        old_db_copy = {}
        try:
            db = shelve.open(self.db_location+self.db_name)
            for obj_name in db:
                old_db_copy[obj_name] = db[obj_name]
                del db[obj_name]
            db.close()
        except IOError:
            self.edit_message.set("Could not delete old entries.")
            raise

        # Now look through the db_frame entries by row, get the entries, group them, and store them in the
        # obj_info ordered dictionary. Pass this to the add_obj_to_database method which adds an object with the
        # attributes given in obj_info to the database with name = self.db_name.
        try:
            # obj is type ordered dictionary here
            for obj in self.db_frame.all_object_entries.values():
                obj_info = OrderedDict()
                # attr are the keys (type str) in obj
                for attr in obj:
                    if len(obj[attr]) == 1:
                        # obj_info[attr] is a list with a single ttk.Entry
                        obj_info[attr] = obj[attr]
                    else:
                        # obj_info[attr] is a list with a ttk.Entry and a ttk.Combobox
                        obj_info[attr] = [obj[attr][0], obj[attr][2]]
                self.add_obj_to_database(obj_info)
            self.mode = 'view'
            self.db_frame.refresh_db_frame()
        except Exception:
            # If something went wrong, restore old database
            db = shelve.open(self.db_location+self.db_name)
            for obj_name in old_db_copy:
                db[obj_name] = old_db_copy[obj_name]
            db.close()
            self.edit_message.set("Could not add new entries.")
            raise
        self.edit_message.set("Edit successful.")

        # Return to default button configuration
        self.cancel_button.pack_forget()
        self.delete_button.pack_forget()
        self.save_changes_button.pack_forget()
        self.close_button.pack(side=RIGHT)
        self.edit_button.pack(side=RIGHT)
        self.add_button.pack(side=RIGHT)

    def delete_obj(self):
        """
        Called when the user presses 'self.delete_button' while in edit mode and an object is selected using the
        radiobuttons. Deletes the appropriate object from the database.
        """
        current_obj_name = self.db_frame.current_object_selection.get()
        oc_message = "Are you sure you want to delete the object %s?" % current_obj_name
        oc = OverwriteConfirm(self, oc_message)
        oc.wait_window()
        if self.overwrite_decision == 'confirmed':
            db = shelve.open(self.db_location+self.db_name)
            del db[current_obj_name]
            self.edit_message.set("Object deleted successfully.")
            if not db:
                self.mode = 'view'
                self.db_frame.refresh_db_frame()
                self.cancel_button.pack_forget()
                self.delete_button.pack_forget()
                self.save_changes_button.pack_forget()
                self.close_button.pack(side=RIGHT)
                self.edit_button.pack(side=RIGHT)
                self.add_button.pack(side=RIGHT)
            db.close()
            self.db_frame.refresh_db_frame()
            self.db_frame.writable_entries()
        else:
            self.edit_message.set("No changes made to database.")

    def add_obj_to_database(self, object_info):
        """
        object_info is an OrderedDict with form
                    {'obj_name': [name_entry], 'other_attr_with_unit': [attr_val_entry, attr_unit_combobox], ...}
        i.e., it is a dictionary of the object's attributes with appropriate unit from which the object can be created.
        """
        obj_attr = []
        # attr_info is a list with either 1 ttk.Entry or 1 Entry and 1 Combobox depending on the attribute
        for attr_info in object_info.values():
            entry_val_list = []
            # entry is either a ttk.Entry widget or a ttk.Combobox widget
            for entry in attr_info:
                entry_value = entry.get()
                if len(str(entry_value)) == 0 or entry_value == 0:
                    entry_value = None
                entry_val_list.append(entry_value)
            obj_attr.append(entry_val_list)

        if all(entry[0] is None for entry in obj_attr):
            obj_attr = None

        obj = getattr(__import__(self.class_name.lower()), self.class_name)(obj_attr)
        db = shelve.open(self.db_location+self.db_name)
        db[obj.name] = obj
        db.close()

    def close_window(self):
        self.master.master.manuf_req_frame.max_build_dim_frame.refresh_printer_cutter_lists()
        self.master.master.manuf_req_frame.max_build_dim_frame.set_values()
        self.master.master.sensor_frame.refresh()
        self.destroy()


class DatabaseFrame(ttk.Frame):
    """
    This class is a ttk Frame that is a container for the object display frames retrieved using obj.display_frame. The
    frame may also contain radiobuttons if the user is in 'edit' mode or the user is viewing the propmotorcombo
    database.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, padding=3, borderwidth=2, relief='ridge')
        self.master = master
        self.db_name = master.db_name
        self.db_location = master.db_location
        self.all_object_entries = OrderedDict()
        self.current_object_selection = StringVar()
        self.radiobutton_list = []

        # Populate database frame
        self.refresh_db_frame()

    def refresh_db_frame(self):
        """
        This method populates the database frame using the objects stored in the appropriate database. It loops through
        all objects in the database and calls the object's display_frame() method to get a ttk Frame containing that
        object's information.

        This method can be called at pretty much anytime to refresh the frame. For instance after an object has been
        added or deleted from the database, or after an edit to the database has been made.
        """
        self.all_object_entries = OrderedDict()
        self.current_object_selection = StringVar()
        self.radiobutton_list = []
        for widget in self.children.values():
            widget.destroy()

        db = shelve.open(self.db_location+self.db_name)
        row = 0
        for obj in db.values():
            if row != 0:
                obj_frame, obj_widgets = obj.display_frame(self, return_widgets=True)
                obj_frame.grid(column=1, row=row, sticky=(E, W))
            else:
                obj_frame, obj_widgets = obj.display_frame(self, header=True, return_widgets=True)
                obj_frame.grid(column=1, row=row, rowspan=2, sticky=(E, W))
                row += 1
            self.all_object_entries[obj.name] = obj_widgets
            if self.db_name == 'propmotorcombodb' or self.master.mode == 'edit':
                radiobutton = ttk.Radiobutton(self, variable=self.current_object_selection,
                                              value=obj.name)
                radiobutton.grid(column=0, row=row)
                self.radiobutton_list.append(radiobutton)
            row += 1
        db.close()

    def writable_entries(self):
        """
        Makes all the entries in the database frame writable. This method is called when the user clicks the edit button
        in the database management window.
        """
        for obj in self.all_object_entries.values():
            for attr_val in obj.values():
                attr_val[0].config(state=NORMAL)

    def readonly_entries(self):
        """
        Makes all the entries in the database frame read-only.
        """
        for obj in self.all_object_entries.values():
            for attr_val in obj.values():
                print type(attr_val[0])
                attr_val[0]['state'] = 'readonly'

    def get_object_entries(self):
        return self.all_object_entries


class AddObjectWindow(Toplevel):
    """
    This is a toplevel window which is used when the user wishes to add an object to the database. An empty
    "object form" is retrieved using the object class's obj_input_frame() classmethod.
    """
    def __init__(self, master):
        Toplevel.__init__(self, master)
        self.db_name = master.db_name
        self.db_location = master.db_location
        self.class_name = master.class_name
        pretty_class_str = getattr(__import__(self.class_name.lower()), self.class_name).pretty_str
        self.title("Add to %s database" % pretty_class_str)

        # Place window
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))

        # Create subframes
        self.entry_frame, self.object_info = \
            getattr(__import__(self.class_name.lower()), self.class_name).obj_input_frame(self)
        self.button_frame = ttk.Frame(self, padding=5)

        # Create Save and Close buttons and add window information indicator
        self.overwrite_decision = 'cancel'  # Instance variable used as a global between self and OverwriteConfirm()
        self.add_button = ttk.Button(self.button_frame, text='Add', command=self.add_obj_to_database)
        self.close_button = ttk.Button(self.button_frame, text='Close', command=self.close_window)
        self.indicator_var = StringVar()
        self.add_indicator = ttk.Label(self.button_frame, textvariable=self.indicator_var)

        # Pack Save and close buttons and add object indicator
        self.close_button.pack(side=RIGHT)
        self.add_button.pack(side=RIGHT)
        self.add_indicator.pack(side=LEFT)

        # Pack subframes
        self.entry_frame.pack(fill=BOTH, expand=YES)
        self.button_frame.pack(fill=X)

        # Handle resizing
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.protocol('WM_DELETE_WINDOW', self.close_window)

    def close_window(self):
        # First refresh the database frame so that when the window is closed any new objects will be displayed
        self.master.db_frame.refresh_db_frame()
        self.destroy()

    def add_obj_to_database(self):
        """
        Creates an object which is an instance of the appropriate component class with attributes given by the current
        values of the entries in self.object_info. Then saves this object to the appropriate database.
        """

        # Retrieve object attributes
        obj_attr = []
        for entries in self.object_info.values():
            entry_val_list = []
            for entry in entries:
                entry_value = entry.get()
                if len(entry_value) == 0 or entry_value == 0:
                    entry_value = None
                entry_val_list.append(entry_value)
            obj_attr.append(entry_val_list)

        db = shelve.open(self.db_location+self.db_name)
        try:
            # Create object
            obj = getattr(__import__(self.class_name.lower()), self.class_name)(obj_attr)
            # Add object to database
            if obj.name in db.keys():
                overwrite_message = "An object with the name '%s' already exists in the database. " \
                                    "Would you like to overwrite the existing object?" % obj.name
                oc = OverwriteConfirm(self, overwrite_message)
                self.wait_window(oc)
                if self.overwrite_decision == 'confirmed':
                    db[obj.name] = obj
                    self.clear_entries()
                    self.indicator_var.set("Object added successfully.")
                else:
                    self.indicator_var.set("No object added.")
            else:
                db[obj.name] = obj
                self.clear_entries()
                self.indicator_var.set("Object added successfully.")
        except IOError:
            self.indicator_var.set("Could not add object.")
        except tools.ConversionError as e:
            self.indicator_var.set(str(e))
        except ValueError as e:
            self.indicator_var.set(str(e))
        finally:
            db.close()

    def clear_entries(self):
        for e in self.object_info.values():
            e[0].delete(0, END)


class AddEditPMComboWindow(Toplevel):
    def __init__(self, master, mode):
        """
        This class is a Toplevel window which replaces the standard AddObjectWindow for the case of propeller/motor
        combinations. The structure of the class's attributes are significantly different from those of other
        components, therefore a new window is necessary.

        The mode input can either be mode = 'add' or mode = 'edit', depending on what button was pressed in the database
        management window.
        """
        Toplevel.__init__(self, master)
        self.mode = mode
        if self.mode == 'add':
            self.title("Add to Prop/Motor Combo Database")
        else:
            self.title("Edit Prop/Motor Object")
        self.db_name = 'propmotorcombodb'
        self.db_location = master.db_location
        self.class_name = 'Propmotorcombo'
        self.overwrite_decision = 'cancel'

        # Place window
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))

        # Important step. If the mode is edit, retrieve the selected prop/motor combo from the database window
        if self.mode == 'edit':
            self.current_obj_name = self.master.db_frame.current_object_selection.get()
            db = shelve.open(self.db_location+self.db_name)
            self.obj_for_edit = db[self.current_obj_name]
            db.close()

        # Create internal frames
        self.add_vector_frame = AddPMComboVectorFrame(self)
        self.misc_entry_frame = ttk.Frame(self, padding=5)
        self.button_frame = ttk.Frame(self, padding=5)

        # Create add and cancel buttons (for add mode) and save changes button (for edit mode) + indicator message label
        self.indicator_var = StringVar()
        self.indicator_label = ttk.Label(self.button_frame, textvariable=self.indicator_var)
        self.update()
        self.indicator_var.set("Enter motor/propeller combo data in the spreadsheet.")
        self.add_button = ttk.Button(self.button_frame, text='Add', command=self.add_obj_to_database)
        self.save_changes_button = ttk.Button(self.button_frame, text='Save Changes', command=self.add_obj_to_database)
        self.cancel_button = ttk.Button(self.button_frame, text='Cancel', command=self.close_window)
        self.delete_obj_button = ttk.Button(self.button_frame, text='Delete Object',
                                            command=self.delete_obj_from_database)

        # Create motor database and propeller databases
        self.motor_db = shelve.open(self.db_location+'motordb')
        self.prop_db = shelve.open(self.db_location+'propellerdb')

        # Create widgets in misc entry frame
        self.motor_label = ttk.Label(self.misc_entry_frame, text='Select Motor')
        self.motor_selected = StringVar()
        self.motor_cb = ttk.Combobox(self.misc_entry_frame, textvariable=self.motor_selected,
                                     values=self.motor_db.keys(), state='readonly', width=len(max(self.motor_db.keys(),
                                                                                              key=len))+1)
        if self.mode == 'edit':
            self.motor_cb.current(self.motor_db.keys().index(self.obj_for_edit.motor.name))
        else:
            self.motor_cb.current(0)
        self.motor_db.close()

        self.prop_label = ttk.Label(self.misc_entry_frame, text='Select Propeller')
        self.prop_selected = StringVar()
        self.prop_cb = ttk.Combobox(self.misc_entry_frame, textvariable=self.prop_selected, values=self.prop_db.keys(),
                                    state='readonly', width=len(max(self.prop_db.keys(), key=len))+1)
        if self.mode == 'edit':
            self.prop_cb.current(self.prop_db.keys().index(self.obj_for_edit.prop.name))
        else:
            self.prop_cb.current(0)
        self.prop_db.close()

        self.battery_voltage_label = ttk.Label(self.misc_entry_frame, text='Test Battery Voltage (V)')
        self.battery_voltage = StringVar()
        self.battery_voltage_entry = ttk.Entry(self.misc_entry_frame, textvariable=self.battery_voltage, width=8)
        if self.mode == 'edit':
            self.battery_voltage.set(self.obj_for_edit.test_bat_volt_rating['value'])

        # Grid widgets in button frame
        self.indicator_label.pack(side=LEFT)
        self.cancel_button.pack(side=RIGHT)
        if self.mode == 'add':
            self.add_button.pack(side=RIGHT)
        else:
            self.delete_obj_button.pack(side=RIGHT)
            self.save_changes_button.pack(side=RIGHT)

        # Grid widgets in misc entry frame
        self.motor_label.grid(column=0, row=0, pady='15 5', sticky=S)
        self.motor_cb.grid(column=0, row=1, padx=10, pady='0 10', sticky=N)
        self.prop_label.grid(column=0, row=2, pady='5 5', sticky=S)
        self.prop_cb.grid(column=0, row=3, padx=10, pady='0 10', sticky=N)
        self.battery_voltage_label.grid(column=0, row=4, pady='5 5', padx=10, sticky=S)
        self.battery_voltage_entry.grid(column=0, row=5, pady='0 10', padx=10, sticky=N)

        # Grid frames.
        self.button_frame.grid(column=0, row=1, columnspan=2, sticky='nsew')
        self.misc_entry_frame.grid(column=0, row=0, sticky='nsew')
        self.add_vector_frame.grid(column=1, row=0, sticky='nsew')

        # Handle resizing
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.protocol('WM_DELETE_WINDOW', self.close_window)

    def add_obj_to_database(self):
        """
        Performs the same function as the analogous add_obj_to_database method in the AddObjectWindow class with some
        modifications to accommodate the more complicated data structures of the Prop/Motor combo object attributes.
        """
        self.motor_db = shelve.open(self.db_location+'motordb')
        self.prop_db = shelve.open(self.db_location+'propellerdb')
        selected_motor = self.motor_db[self.motor_selected.get()]
        selected_prop = self.prop_db[self.prop_selected.get()]
        self.motor_db.close()
        self.prop_db.close()
        battery_voltage = self.battery_voltage.get()
        attr_list = [[selected_motor], [selected_prop], [battery_voltage]]

        # Get current add_vector_frame entry values
        for attr_vec in self.add_vector_frame.entry_list_of_list:
            attr_entry_vals = []
            for entry in attr_vec:
                if len(str(entry.get())) == 0:
                    continue
                attr_entry_vals.append(float(entry.get()))
            attr_list.append(attr_entry_vals)
        thrust_unit = self.add_vector_frame.thrust_unit_selected.get()
        attr_list[-1] = [attr_list[-1], thrust_unit]

        # Create Propmotorcombo object
        try:
            current_obj = getattr(__import__(self.class_name.lower()), self.class_name)(attr_list)
        except Exception:
            print "Could not create prop motor combo object"
            raise

        # Add object to database
        pmcombo_db = shelve.open(self.db_location+self.db_name)
        try:
            if pmcombo_db and current_obj.name in [pmcombo for pmcombo in pmcombo_db]:
                if (self.mode == 'edit') and (current_obj.name == self.master.db_frame.current_object_selection.get()):
                    overwrite_message = "Are you sure you want to make these changes to the %s database entry?"\
                                        % current_obj.name
                else:
                    overwrite_message = "A propeller/motor combo object with the propeller and motor combination %s already " \
                                        "exists. Would you like to overwrite the existing object?" % current_obj.name
                oc = OverwriteConfirm(self, overwrite_message)
                self.wait_window(oc)
                if self.overwrite_decision == 'confirmed':
                    pmcombo_db[current_obj.name] = current_obj
                    if self.mode == 'edit':
                        self.indicator_var.set("Object edited successfully.")
                    else:
                        self.add_vector_frame.clear_entries()
                        self.indicator_var.set("Object added successfully.")
                else:
                    self.indicator_var.set("No object added.")
            else:
                pmcombo_db[current_obj.name] = current_obj
                self.add_vector_frame.clear_entries()
                self.indicator_var.set("Object added successfully.")
        except IOError:
            self.indicator_var.set("Could not add object.")
        except tools.ConversionError as e:
            self.indicator_var.set(str(e))
        except ValueError as e:
            self.indicator_var.set(str(e))
        except AttributeError:
            print pmcombo_db
            raise
        finally:
            pmcombo_db.close()

    def delete_obj_from_database(self):
        overwrite_message = "Are you sure you want to delete the object %s from the database?" % self.current_obj_name
        oc = OverwriteConfirm(self, overwrite_message)
        oc.wait_window()
        if self.overwrite_decision == 'confirmed':
            db = shelve.open(self.db_location+self.db_name)
            try:
                del db[self.current_obj_name]
                self.master.edit_message.set("Object deleted successfully.")
                db.close()
                self.close_window()
            except IOError:
                self.indicator_var.set("Could not delete object.")
        else:
            self.indicator_var.set("No changes made.")

    def close_window(self):
        self.master.db_frame.refresh_db_frame()
        self.destroy()


class AddPMComboVectorFrame(ttk.Frame):
    """
    This class defines the "spreadsheet-like" frame in the AddEditPMComboWindow. Default number of rows is set at 15
    and may be changed to accommodate larger input data lists by modifying the self.num_entry_rows variable in the
    __init__ method.
    """
    def __init__(self, master):
        ttk.Frame.__init__(self, master, padding=7, borderwidth=2, relief='ridge')
        # Create header rows
        self.current_label = ttk.Label(self, text='Current(A)')
        self.voltage_label = ttk.Label(self, text='Voltage(V)')
        self.power_label = ttk.Label(self, text='Power(W)')
        self.rpm_label = ttk.Label(self, text='RPM')
        self.throttle_label = ttk.Label(self, text='Throttle')
        self.thrust_label = ttk.Label(self, text='Thrust')

        self.thrust_unit_selected = StringVar()
        self.thrust_unit_cb = ttk.Combobox(self, textvariable=self.thrust_unit_selected, values=['N', 'lbf'],
                                           state='readonly', width=2)
        self.thrust_unit_cb.current(0)

        self.heading_separator = ttk.Separator(self, orient=HORIZONTAL)

        # Grid header rows
        self.current_label.grid(column=0, row=0, columnspan=2, padx=3, pady=5, sticky=S)
        self.voltage_label.grid(column=2, row=0, columnspan=2, padx=3, pady=5, sticky=S)
        self.power_label.grid(column=4, row=0, columnspan=2, padx=3, pady=5, sticky=S)
        self.rpm_label.grid(column=6, row=0, columnspan=2, padx=3, pady=5, sticky=S)
        self.throttle_label.grid(column=8, row=0, columnspan=2, padx=3, pady=5, sticky=S)
        self.thrust_label.grid(column=10, row=0, columnspan=1, padx='3 0', pady=5, sticky=S)
        self.thrust_unit_cb.grid(column=11, row=0, columnspan=1, padx='0 1', pady='5 4', sticky=S)
        self.heading_separator.grid(column=0, row=1, columnspan=12, sticky=(W, E))

        # Create "spreadsheet" of entries
        if self.master.mode == 'edit':
            db = shelve.open(self.master.db_location+self.master.db_name)
            for obj_name in db.keys():
                if obj_name == self.master.current_obj_name:
                    self.obj_for_edit = db[obj_name]
            db.close()
        self.real_vector_names = ['current_vec', 'voltage_vec', 'pwr_vec', 'rpm_vec', 'throttle_vec', 'thrust_vec']
        self.num_entry_rows = 15
        self.num_heading_attr = 6
        self.entry_list_of_list = []
        for col in xrange(0, 2*self.num_heading_attr, 2):
            self.columnconfigure(col, weight=1)
            if self.master.mode == 'edit':
                current_attr = getattr(self.obj_for_edit, self.real_vector_names[col/2])
                try:
                    current_vec_vals = current_attr['value']
                except TypeError:
                    current_vec_vals = current_attr
            current_list = []
            for row in xrange(0, self.num_entry_rows):
                temp_entry = ttk.Entry(self, width=8)
                temp_entry.grid(column=col, row=row+2, columnspan=2, sticky=(N, S, E, W))
                if self.master.mode == 'edit':
                    if row <= len(current_vec_vals)-1:
                        temp_entry.insert(0, str(current_vec_vals[row]))
                current_list.append(temp_entry)
                row += 1
            self.entry_list_of_list.append(current_list)
            col += 2

    def clear_entries(self):
        for attr in self.entry_list_of_list:
            for entry in attr:
                try:
                    entry.delete(0, END)
                except TypeError:
                    print "Entry: %r" % entry
                    print "Attr: %r" % attr
                    raise


class OverwriteConfirm(Toplevel):
    """
    This class defines a Toplevel window which may be called to ask the user to confirm his decision before performing
    an irreversible task (such as saving an object to a database or modifying an existing database object). When the
    user selects either "Confirm" or "Cancel", the value of the variable self.master.overwrite_decision variable is
    changed which can then be used to control flow in the master frame.
    """
    def __init__(self, master, message_text):
        Toplevel.__init__(self, master)
        self.master = master
        self.resizable(width=FALSE, height=FALSE)

        # Place window
        xpos, ypos = get_win_place(self)
        self.geometry('+%d+%d' % (xpos, ypos))

        self.mainframe = ttk.Frame(self, padding=5)
        self.mainframe.pack()

        # Create confirmation message, replace confirmation button, and cancel button
        self.message_text = message_text
        self.message = ttk.Label(self.mainframe, text=self.message_text, wraplength=300)
        self.replace_button = ttk.Button(self.mainframe, text='Confirm',
                                         command=lambda: self.overwrite_decision('confirmed'))
        self.cancel_button = ttk.Button(self.mainframe, text='Cancel',
                                        command=lambda: self.overwrite_decision('cancel'))

        # Grid widgets
        self.message.pack(expand=YES, padx=15, pady=5)
        self.replace_button.pack(side=RIGHT)
        self.cancel_button.pack(side=RIGHT)

    def overwrite_decision(self, result):
        if result == 'confirmed':
            self.master.overwrite_decision = 'confirmed'
        else:
            self.master.overwrite_decision = 'cancel'
        self.destroy()