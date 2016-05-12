import shelve
import math
from scipy.interpolate import interp1d
from operator import add
from unitconversion import convert_unit
from quadrotor import Quadrotor
import dblocation

db_location = dblocation.db_location


def generate_alternatives(constraints):
    """
    This function is called from oo_quad_GUI.quadGUI.alternatives_frame.find_alternatives(). The constraints input is
    a list of constraints defined by the user within the main GUI and is of the form:

        constraints = [endurance_req, payload_req, max_weight, max_size, maneuverability,
                       p_len, p_width, p_height, c_len, c_width, max_build_time, sensors]

    Obviously if more constraints are added to the algorithm these will need to be passed in as well.
    The purpose of this function is to find all of the possible vehicle alternatives given the input constraints,
    although the function output is actually a full list of both infeasible and feasible alternatives (see block
    comment below).
    """
    pmcombo_db = shelve.open(db_location+'propmotorcombodb')
    battery_db = shelve.open(db_location+'batterydb')
    print_material_db = shelve.open(db_location+'printingmaterialdb')

    # This is a "full factorial" search for possible alternatives. If the number of components available becomes large
    # this method of searching may need to be revised. My logic here saves all alternatives in the 'alternatives' list.
    # If the alternative is feasible, the Quadrotor.feasible attribute will be equal to the boolean value True (the
    # default value of the attribute). If it is not feasible the Quadrotor.feasible attribute will be a string telling
    # the first reason the algorithm found for rejecting the alternative. By saving all alternatives in one list they
    # will be easy to pass back to the main gui for display or for statistical purposes. If the list of alternatives
    # becomes very large a list may take up too much memory. In this case other data structures should be used to hold
    # feasible or non-feasible alternatives.
    alternatives = []
    selected_pmaterials = constraints[-2]
    # If the user has not selected any print materials, no alternatives are possible
    if not selected_pmaterials:
        return alternatives
    for pmcombo in pmcombo_db.values():
        # pre-filter out all batteries that will not be compatible with the prop/motor combo data
        good_bats = [bat for bat in battery_db.values()
                     if abs(float(bat.voltage['value'])-float(pmcombo.test_bat_volt_rating['value'])) < 0.1]
        for battery in good_bats:
            for pmaterial in selected_pmaterials:
                    this_quad = Quadrotor(pmcombo, battery, pmaterial)
                    quad_attrs = unit_wrapper(this_quad)
                    feasibility, performance, geometry = is_feasible(quad_attrs, constraints)
                    if feasibility != 'true':
                        #   If not feasible return reason for fail and % off from requirement
                        this_quad.feasible = (feasibility, performance)
                    else:
                        this_quad.set_performance(performance)
                        this_quad.set_geometry(geometry)
                    alternatives.append(this_quad)

    pmcombo_db.close()
    battery_db.close()
    print_material_db.close()

    return alternatives


def unit_wrapper(quad):
    """
    This function takes a quadrotor object as input (from the generate_alternatives() function) and converts the
    attribute quantities that will be needed in the is_feasible() function to English units. This is done because the
    performance and sizing equations given in the original GT tool are in English units. Without re-deriving all of them
    without any documentation it is necessary to do the calculations in English units and convert the results back to
    metric. Not very elegant, but for now it will have to do.
    """
    this_quad = quad
    bat_xdim = convert_unit(this_quad.battery.xdim['value'], this_quad.battery.xdim['unit'], 'in')
    bat_ydim = convert_unit(this_quad.battery.ydim['value'], this_quad.battery.ydim['unit'], 'in')
    bat_zdim = convert_unit(this_quad.battery.zdim['value'], this_quad.battery.zdim['unit'], 'in')
    prop_dia = convert_unit(this_quad.prop.diameter['value'], this_quad.prop.diameter['unit'], 'in')
    motor_body_dia = convert_unit(this_quad.motor.body_diameter['value'], this_quad.motor.body_diameter['unit'], 'in')
    pmat_density = convert_unit(this_quad.pmaterial.density['value'], this_quad.pmaterial.density['unit'], 'lbf*ft^-3')
    bat_weight = convert_unit(this_quad.battery.weight['value'], this_quad.battery.weight['unit'], 'lbf')
    motor_weight = convert_unit(this_quad.motor.weight['value'], this_quad.motor.weight['unit'], 'lbf')
    prop_weight = convert_unit(this_quad.prop.weight['value'], this_quad.prop.weight['unit'], 'lbf')
    pmc_max_thrust = convert_unit(this_quad.pmcombo.max_thrust['value'], this_quad.pmcombo.max_thrust['unit'], 'lbf')
    bat_voltage = this_quad.battery.voltage['value']
    bat_capacity = convert_unit(this_quad.battery.capacity['value'], this_quad.battery.capacity['unit'], 'mAh',
                                this_quad.battery.voltage['value'])
    pmc_thrust_vec = [convert_unit(val, 'N', 'lbf') for val in this_quad.pmcombo.thrust_vec['value']]
    pmc_current_vec = this_quad.pmcombo.current_vec['value']

    quad_attrs = [bat_xdim, bat_ydim, bat_zdim, prop_dia, motor_body_dia, pmat_density,
                  bat_weight, motor_weight, prop_weight, pmc_max_thrust, bat_voltage, bat_capacity, pmc_thrust_vec,
                  pmc_current_vec]
    return quad_attrs


def is_feasible(quad_attrs, constraints):
    """
    Checks if a quadrotor alternative (described by its attributes passed in using the quad_attrs variable) is feasible
    considering the constraints given by the user by calculating some vehicle sizing and performance metrics.

    Returns ('true', vehicle_performance), where vehicle  performance is a list of metrics, if alternative is feasible.
    Returns (rejection reason, rejected value), where rejection reason is a string, if alternative is not
    feasible.
    """

    bat_xdim, bat_ydim, bat_zdim, prop_dia, motor_body_dia, pmat_density, bat_weight, motor_weight, prop_weight, \
        pmc_max_thrust, bat_voltage, bat_capacity, pmc_thrust_vec, pmc_current_vec = quad_attrs

    endurance_req, payload_req, max_weight, max_size, maneuverability, \
        p_len, p_width, p_height, max_build_time, sensors, selected_pmaterials, cover_flag = constraints

    # First estimate the vehicle size based on battery, prop, and motor. There are several constraints tested here.
    # 1) The maximum vehicle dimension must be less than the max_size constraint
    # 2) The dimension of the hub must be less than min(cutter_len, cutter_width)
    # 3) The length of the arm must be less than max(printer_len, printer_width). This assumes the other dimension of
    # the printer is sufficiently large, which is a fair assumption since the arm is long and narrow. This also assumes
    # the printer height is sufficient.

    # The following hub dimensions are from David Locascio's documentation on the new quad design
    hub_xdim = 4.25
    hub_ydim = 5.75
    big_hub_dim = max(hub_xdim, hub_ydim)

    safe_factor = 1.15
    n_arms = 4
    prop_disc_separation_limited_len = safe_factor * (prop_dia/2/math.sin(math.pi/n_arms) + 0.75*motor_body_dia -
                                                      0.5*big_hub_dim)
    prop_to_hub_limited_len = safe_factor * \
        (prop_dia/2 + 1.5*motor_body_dia/2)
    arm_len = max(prop_disc_separation_limited_len, prop_to_hub_limited_len)
    size = math.sqrt(hub_xdim**2 + hub_ydim**2) + 2*arm_len + prop_dia  # This is an approximation
    if size > max_size:
        return "Max dimension too large.", size, None
    if big_hub_dim > min(p_len, p_width):
        return "Hub too large for printer", big_hub_dim, None
    if arm_len > max(p_len, p_width):
        return "Arms too long for printer.", arm_len, None

    # We want arm weight and hub weight now. These are calculated using weight/volume regressions as a function of
    # propeller size.
    prop_diameters = [5, 6, 7, 8, 9, 10, 11, 12]
    arm_volumes = [0.74, 0.86, 1.02, 1.20, 1.38, 1.57, 1.81, 2.04]
    base_plate_volumes = [2.29]*len(prop_diameters)
    top_plate_volumes = [3.23, 3.13, 3.06, 2.94, 2.84, 2.75, 2.65, 2.56]
    top_plate_cover_volumes = [4.58, 4.49, 4.39, 4.29, 4.20, 4.10, 4.00, 3.89]

    arm_vol = interp(prop_diameters, arm_volumes, prop_dia)
    base_plate_vol = interp(prop_diameters, base_plate_volumes, prop_dia)
    top_plate_vol = interp(prop_diameters, top_plate_volumes, prop_dia)
    top_plate_cover_vol = interp(prop_diameters, top_plate_cover_volumes, prop_dia)

    if cover_flag:
        hub_vol = base_plate_vol + top_plate_cover_vol
    else:
        hub_vol = base_plate_vol + top_plate_vol

    arm_weight = arm_vol * pmat_density
    hub_weight = hub_vol * pmat_density

    # The original authors give misc other weights for parts to go into the aggregate weight. Note: if the user wishes
    # to include sensors this weight should also be added.
    sensors_weight = convert_unit(sum(s.weight['value'] for s in sensors), 'N', 'lbf')
    wire_weight = 0.000612394 * arm_len * n_arms
    esc_weight = 0.2524
    apm_weight = 0.0705479
    compass_weight = 0.06062712
    receiver_weight = 0.033069
    propnut_weight = 0.0251327
    weights = [arm_weight*n_arms, compass_weight, receiver_weight, apm_weight, wire_weight, esc_weight, propnut_weight]
    weights += [hub_weight, bat_weight, motor_weight*n_arms, prop_weight*n_arms, sensors_weight]
    vehicle_weight = sum(weights)
    if vehicle_weight > max_weight:
        return "Too heavy.", vehicle_weight, None

    # Now estimate the thrust required for the vehicle based on the maneuverability requested by the user and the
    # weight that was just calculated. The original MASR Excel tool uses a table lookup to find the thrust margin
    # coefficient, but since there are only 3 options to choose from (Normal, High, Acrobatic), it makes more sense to
    # simply assign these three values without bothering looking them up in a table. If additional maneuverability
    # fidelity is desired it may be good to use the table lookup.
    thrust_margin_coef = [1.29, 1.66, 2.09][['Normal', 'High', 'Acrobatic'].index(maneuverability)]
    thrust_available = n_arms * pmc_max_thrust
    payload_capacity = (thrust_available / thrust_margin_coef) - vehicle_weight
    if payload_capacity < payload_req:
        return "Not enough payload capacity.", payload_capacity, None

    # Next, determine the estimated vehicle endurance and compare to the endurance required by the user. For this step
    # the average current draw needs to be interpolated from the propeller/motor combo current vs. thrust data using
    # the average thrust as the interpolation point of interest. The equation for average thrust given below assumes
    # that the mission consists only of hovering. This could be replaced with a real mission model result.
    avg_thrust = 1.125 * (vehicle_weight + payload_req) / n_arms
    try:
        avg_current = interp(pmc_thrust_vec, pmc_current_vec, avg_thrust)
    except ValueError as e:
        return str(e)
    vehicle_endurance = bat_capacity / (n_arms * avg_current * 1000) * 60
    if vehicle_endurance < endurance_req:
        return "Not enough endurance.", vehicle_endurance, None

    # Now calculate the estimated build time based on a regression of experimentally measured times (as a function of
    # propeller diameter).
    arm_times = [2.50, 2.66, 2.93, 3.22, 3.50, 3.83, 4.17, 4.38]
    base_plate_times = [1.63] * len(prop_diameters)
    top_plate_times = [3.15, 3.03, 2.90, 2.78, 2.67, 2.55, 2.43, 2.30]
    top_plate_cover_times = [4.72, 4.63, 4.53, 4.43, 4.35, 4.25, 4.13, 4.02]

    arm_time = interp(prop_diameters, arm_times, prop_dia)
    base_plate_time = interp(prop_diameters, base_plate_times, prop_dia)
    top_plate_time = interp(prop_diameters, top_plate_times, prop_dia)
    top_plate_cover_time = interp(prop_diameters, top_plate_cover_times, prop_dia)

    if cover_flag:
        build_time = arm_time*4 + base_plate_time + top_plate_cover_time
    else:
        build_time = arm_time*4 + base_plate_time + top_plate_time

    if build_time > max_build_time:
        return "Takes too long to build.", build_time, None

    # Since the alternative isn't infeasible by this point, it must be feasible. First convert some stuff back to metric
    size = convert_unit(size, 'in', 'm')
    vehicle_weight = convert_unit(vehicle_weight, 'lbf', 'N')
    payload_capacity = convert_unit(payload_capacity, 'lbf', 'N')
    hub_xdim = convert_unit(hub_xdim, 'in', 'm')
    hub_ydim = convert_unit(hub_ydim, 'in', 'm')
    arm_len = convert_unit(arm_len, 'in', 'm')
    vehicle_performance = [vehicle_weight, payload_capacity, vehicle_endurance, size, build_time]
    vehicle_geometry = [hub_xdim, hub_ydim, arm_len]
    return 'true', vehicle_performance, vehicle_geometry


def interp(x, y, xint):
    """
    Uses linear interpolation of the datasets x and y to find the value yint corresponding to a value xint. In this
    case x is the thrust array, y is the current array, and xint is the average thrust required.

    xint must satisfy min(x) <= xint <= max(x)

    x and y arrays must be of equal length. This should be pre-enforced when the pmcombo object was created.

    Linear interpolation should be sufficient for the problem of finding the average current draw given the average
    thrust required if the thrust since this plot is roughly linear for the datasets currently available. Of course the
    approximation gets worse with the second derivative of the true relationship between current and thrust. This
    function is used instead of a potentially more efficient implementation using scipy because 1) the application will
    be more portable without dependencies and 2) the data is basically linear so only this simple method is required.
    """

    # Put this in so that the function accepts integer and float single values
    if not isinstance(y, list):
        y = [y]
    if not isinstance(x, list):
        x = [x]

    if not min(x) <= xint <= max(x):
        raise ValueError("Insufficient Data")

    if xint in x:
        yint = y[x.index(xint)]
        return yint

    for i, xp in enumerate(x):
        if xint < xp:
            p2 = (xp, y[i])
            p1 = (x[i-1], y[i-1])
            slope = (p2[1]-p1[1])/(p2[0]-p1[0])
            yint = slope*(xint-p1[0]) + p1[1]
            return yint


def score_alternatives(alternatives, weightings):
    """
    This function takes in a list of feasible alternatives, scores the alternatives based on user-specified importance
    weightings, sets the Quadrotor.score attribute accordingly. The list of feasible alternatives is then returned. The
    algorithm used is TOPSIS. Quadrotor attribute values are normalized, and user-specified importance ratings are
    applied. Then each alternative is compared to the positive and negative ideal solutions via an effective distance
    from the negative ideal solution. Alternatives are ranked based on their distance from the negative ideal solution.
    Therefore, a solution with a TOPSIS score of 1 is the positive ideal solution for the given weightings, and an
    alternative with a score of 0 is the negative ideal solution. Note that unless one configuration is the only
    alternative on the Pareto frontier a true TOPSIS score of 1 is impossible unless weighting factors of zero are
    allowed (which they are currently not). However, since the TOPSIS scores are rounded to two decimal places, it is
    possible for a score to be rounded to 1 (and similarly to 0).

    The weightings input is a dictionary of the form:
        weightings = OrderedDict([('perf_attr1', [perf_attr1_weight, 'high']),
                                ('perf_attr2', [perf_attr2_weight, 'low']), ... )])
    where the 'high' and 'low' tell whether or not a high value of the attr is desirable or vice versa.

    This function is called from oo_quad_GUI.AlternativesFrame.find_alternatives
    """
    # First we need to normalize the weighting values
    wgt_vals = [float(val[0]) for val in weightings.values()]
    wgt_sum = sum(wgt_vals)
    norm_wgt_vals = [wgt/wgt_sum for wgt in wgt_vals]
    # Loop through all performance attributes contained in the weightings dictionary.
    total_d_pos = [0] * len(alternatives)
    total_d_neg = [0] * len(alternatives)
    for i, perf_attr in enumerate(weightings):
        weight = norm_wgt_vals[i]
        try:
            attr_vals = [getattr(quad, perf_attr)['value'] for quad in alternatives]
        except TypeError:
            attr_vals = [getattr(quad, perf_attr) for quad in alternatives]
        # Find norm
        norm = sum(val**2 for val in attr_vals)**0.5
        # Normalize the attribute values
        norm_attr_vals = [val/norm for val in attr_vals]
        # Apply weighting to normalized values
        weighted_vals = [weight*val for val in norm_attr_vals]
        if weightings[perf_attr][1] == 'high':
            pos_ideal = max(weighted_vals)
            neg_ideal = min(weighted_vals)
        else:
            pos_ideal = min(weighted_vals)
            neg_ideal = max(weighted_vals)
        d_pos = [(val-pos_ideal)**2 for val in weighted_vals]
        d_neg = [(val-neg_ideal)**2 for val in weighted_vals]
        total_d_pos = map(add, total_d_pos, d_pos)
        total_d_neg = map(add, total_d_neg, d_neg)
    total_d_pos = [x**0.5 for x in total_d_pos]
    total_d_neg = [x**0.5 for x in total_d_neg]
    closeness = map(lambda pos, neg: float(neg)/(pos+neg), total_d_pos, total_d_neg)

    # Find Pareto solutions
    def float_is_close(f1, f2, rel_tol=1e-09, abs_tol=0.0):
        """
        Floating point "equals" function
        """
        return abs(f1-f2) <= max(rel_tol*max(abs(f1), abs(f2)), abs_tol)

    def is_dominated(a1, a2):
        """
        Takes in two feasible alternatives and determines whether alternative 1 is dominated by alternative 2, returning
        True or False appropriately.
        """
        for attr in weightings:
            try:
                a1_attr_val = getattr(a1, attr)['value']
                a2_attr_val = getattr(a2, attr)['value']
            except TypeError:
                a1_attr_val = getattr(a1, attr)
                a2_attr_val = getattr(a2, attr)
            if weightings[attr][1] == 'high':
                if (a1_attr_val > a2_attr_val) or float_is_close(a1_attr_val, a2_attr_val):
                    return False
            else:
                if (a1_attr_val < a2_attr_val) or float_is_close(a1_attr_val, a2_attr_val):
                    return False
        return True

    for alt in alternatives:
        comps = (is_dominated(alt, a_comp) for a_comp in alternatives if a_comp is not alt)
        if not any(comps):
            alt.pareto = True

    # Assign TOPSIS scores to the quad.score attribute.
    for i, quad in enumerate(alternatives):
        quad.score = closeness[i]
    return alternatives