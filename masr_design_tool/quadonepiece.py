from vehicle import Vehicle
from collections import OrderedDict
from tools import convert_unit, interp
import math
try:
    from Tkinter import *
except ImportError:
    from tkinter import *
import ttk


class Quadonepiece(Vehicle):
    # Note that the default pretty_attr_dict and real_attr_names variables have not been overridden. Instead these
    # shortened versions are used in the overridden display_frame method below.
    short_pretty_attr = OrderedDict([('Propeller', ()), ('Motor', ()), ('Battery', ()), ('Endurance', ('min', 'hr')),
                                     ('Payload', ('N', 'lbf', 'kg')), ('Score', ()), ('Type', ())])
    short_attr_names = ['prop', 'motor', 'battery', 'max_endurance', 'max_payload', 'score', 'pretty_type']
    geometry_attrs = [('Hub Size', 'hub_size', ('m', 'in', 'cm')),
                      ('Hub Separation', 'hub_separation', ('m', 'in', 'cm')),
                      ('Arm Length', 'arm_len', ('m', 'in', 'cm'))]
    part_attrs = [('P/M Combo', 'pmcombo'), ('Battery', 'battery'), ('Print Material', 'pmaterial')]
    pretty_type = 'One Piece'

    # If you want to export data to the csv file when the alternative is exported append the info to the export_info
    # list using a tuple of the format ('Pretty name', 'attribute real name', unit list (if applicable))
    export_info = part_attrs + Vehicle.perf_attrs_export + geometry_attrs

    def __init__(self, pmcombo, battery, pmaterial, geometry=None, feasible=True, score=0, pareto=False):
        """

        The input "feasible" will be true by default. If the quad is found to be infeasible the value will be changed
        to a tuple. The first entry will be a string explaining the first reason why the alternative was rejected
        (but not necessarily the only reason it would have been rejected). The second entry is the % (e.g., 0.15) off
        the vehicle spec was from the requirement.
        """

        # Call vehicle constructor to initialize performance parameters
        Vehicle.__init__(self, "std quad")

        if geometry is None:
            geometry = [0] * 3

        self.hub_xdim, self.hub_ydim, self.arm_len = geometry

        self.pmcombo = pmcombo
        self.prop = self.pmcombo.prop
        self.motor = self.pmcombo.motor
        self.battery = battery
        self.pmaterial = pmaterial
        self.feasible = feasible
        self.score = score
        self.pareto = pareto
        self.name = "(%s, %s)" % (self.pmcombo.name, self.battery.name)

    def __str__(self):
        return self.name

    def is_feasible(self, constraints):
        """
        Checks if a quadrotor alternative (described by its attributes passed in using the quad_attrs variable) is
        feasible considering the constraints given by the user by calculating some vehicle sizing and performance
        metrics.

        Returns ('true', vehicle_performance), where vehicle  performance is a list of metrics, if alternative is
        feasible. Returns (rejection reason, rejected value), where rejection reason is a string, if alternative is not
        feasible.
        """
        bat_xdim = self.battery.xdim['value']
        bat_ydim = self.battery.ydim['value']
        bat_zdim = self.battery.zdim['value']
        prop_dia = self.prop.diameter['value']
        motor_body_dia = self.motor.body_diameter['value']
        pmat_density = self.pmaterial.density['value']
        bat_weight = self.battery.weight['value']
        motor_weight = self.motor.weight['value']
        prop_weight = self.prop.weight['value']
        pmc_max_thrust = self.pmcombo.max_thrust['value']
        bat_voltage = self.battery.voltage['value']
        bat_capacity = convert_unit(self.battery.capacity['value'], 'Wh', 'mAh', bat_voltage)
        pmc_thrust_vec = self.pmcombo.thrust_vec['value']
        pmc_current_vec = self.pmcombo.current_vec['value']

        endurance_req, payload_req, max_weight, max_size, maneuverability, \
            p_len, p_width, p_height, max_build_time, sensors, selected_pmaterials, cover_flag = constraints

        # First estimate the vehicle size based on battery, prop, and motor. There are several constraints tested here.
        # 1) The maximum vehicle dimension must be less than the max_size constraint
        # 2) The dimension of the hub must be less than min(cutter_len, cutter_width)
        # 3) The length of the arm must be less than max(printer_len, printer_width). This assumes the other dimension
        # of the printer is sufficiently large, which is a fair assumption since the arm is long and narrow. This also
        # assumes the printer height is sufficient.

        # The following hub dimensions are from David Locascio's documentation on the new quad design
        hub_xdim = convert_unit(4.25, 'in', 'm')
        hub_ydim = convert_unit(5.75, 'in', 'm')
        hub_separation = convert_unit(1.64, 'in', 'm')
        big_hub_dim = max(hub_xdim, hub_ydim)

        safe_factor = 1.15
        n_arms = 4
        half_arm_width = motor_body_dia/float(2) + 0.05
        prop_disc_separation_limited_len = safe_factor * (prop_dia/2/math.sin(math.pi/n_arms) + 0.75*motor_body_dia -
                                                          0.5*big_hub_dim)
        prop_to_hub_limited_len = safe_factor * \
            (prop_dia/2 + 1.5*motor_body_dia/2)
        arm_len = max(prop_disc_separation_limited_len, prop_to_hub_limited_len)
        size = math.sqrt(hub_xdim**2 + hub_ydim**2) + 2*arm_len + prop_dia  # This is an approximation
        if size > max_size:
            return "Max dimension too large.", size, None
        if size > math.sqrt(p_len**2 + p_width**2):
            return "Body too large for printer.", size, None

        # Calculate the volume of the body and calculate the vehicle weight using known regression
        unit_vol_incube = -6.6375 + 2.0725 * arm_len + 4.29 * half_arm_width + -1.36 * (size/2) + 1.005 * hub_separation
        unit_vol_mcube = unit_vol_incube * 1.63871e-5
        unit_weight = unit_vol_mcube * pmat_density

        sensors_weight = sum(s.weight['value'] for s in sensors)
        wire_weight = convert_unit(0.000612394*arm_len*n_arms, 'lbf', 'N')
        esc_weight = convert_unit(0.2524, 'lbf', 'N')
        apm_weight = convert_unit(0.0705479, 'lbf', 'N')
        compass_weight = convert_unit(0.06062712, 'lbf', 'N')
        receiver_weight = convert_unit(0.033069, 'lbf', 'N')
        propnut_weight = convert_unit(0.0251327, 'lbf', 'N')
        weights = [compass_weight, receiver_weight, apm_weight, wire_weight, esc_weight, propnut_weight]
        weights += [unit_weight, bat_weight, motor_weight*n_arms, prop_weight*n_arms, sensors_weight]
        vehicle_weight = sum(weights)
        if vehicle_weight > max_weight:
            return "Too heavy.", vehicle_weight, None

        # Now estimate the thrust required for the vehicle based on the maneuverability requested by the user and the
        # weight that was just calculated. The original MASR Excel tool uses a table lookup to find the thrust margin
        # coefficient, but since there are only 3 options to choose from (Normal, High, Acrobatic), it makes more sense
        # to simply assign these three values without bothering looking them up in a table. If additional
        # maneuverability fidelity is desired it may be good to use the table lookup.
        thrust_margin_coef = [1.29, 1.66, 2.09][['Normal', 'High', 'Acrobatic'].index(maneuverability)]
        thrust_available = n_arms * pmc_max_thrust
        payload_capacity = (thrust_available / thrust_margin_coef) - vehicle_weight
        if payload_capacity < payload_req:
            return "Not enough payload capacity.", payload_capacity, None

        # Next, determine the estimated vehicle endurance and compare to the endurance required by the user. For this
        # step the average current draw needs to be interpolated from the propeller/motor combo current vs. thrust data
        # using the average thrust as the interpolation point of interest. The equation for average thrust given below
        # assumes that the mission consists only of hovering. This could be replaced with a real mission model result.
        avg_thrust = 1.125 * (vehicle_weight + payload_req) / n_arms
        try:
            avg_current = interp(pmc_thrust_vec, pmc_current_vec, avg_thrust)
        except ValueError as e:
            return str(e)
        vehicle_endurance = bat_capacity / (n_arms * avg_current * 1000) * 60
        if vehicle_endurance < endurance_req:
            return "Not enough endurance.", vehicle_endurance, None

        # Now calculate the estimated build time.
        build_time = -25.9989583333333 + 4.41875 * arm_len + 12.025 * half_arm_width + -0.725 * (size/2) + \
            8.79583333333333 * hub_separation
        if build_time > max_build_time:
            return "Takes too long to build.", build_time, None

        # Since the alternative isn't infeasible by this point, it must be feasible.
        vehicle_performance = [vehicle_weight, payload_capacity, vehicle_endurance, size, build_time]
        vehicle_geometry = [hub_xdim, hub_ydim, arm_len]
        return 'true', vehicle_performance, vehicle_geometry

    def set_geometry(self, geometry):
        """
        Set geometry method for when the geometry needs to be changed after initialization of the object,
        specifically when the vehicle object has been determined to be feasible and geometry values have been
        calculated.
        """
        hub_xdim, hub_ydim, arm_len = geometry
        self.hub_xdim = {'value': hub_xdim, 'unit': 'm'}
        self.hub_ydim = {'value': hub_ydim, 'unit': 'm'}
        self.arm_len = {'value': arm_len, 'unit': 'm'}

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