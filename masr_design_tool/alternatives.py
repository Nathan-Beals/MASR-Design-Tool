import shelve
import math
from operator import add
from unitconversion import convert_unit
from quadrotor import Quadrotor
import hublayout
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
    cut_material_db = shelve.open(db_location+'cuttingmaterialdb')
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
    for pmcombo in pmcombo_db.values():
        # pre-filter out all batteries that will not be compatible with the prop/motor combo data
        good_bats = [bat for bat in battery_db.values()
                     if abs(float(bat.voltage['value'])-float(pmcombo.test_bat_volt_rating['value'])) < 0.1]
        for battery in good_bats:
            for pmaterial in print_material_db.values():
                for cmaterial in cut_material_db.values():
                    this_quad = Quadrotor(pmcombo, battery, pmaterial, cmaterial)
                    quad_attrs = unit_wrapper(this_quad)
                    feasibility, performance, geometry = is_feasible(quad_attrs, constraints)
                    if feasibility != 'true':
                        # If not feasible return reason for fail and % off from requirement
                        this_quad.feasible = (feasibility, performance)
                    else:
                        this_quad.set_performance(performance)
                        this_quad.set_geometry(geometry)
                    alternatives.append(this_quad)

    pmcombo_db.close()
    battery_db.close()
    cut_material_db.close()
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
    cmat_density = convert_unit(this_quad.cmaterial.density['value'], this_quad.cmaterial.density['unit'], 'lbf*ft^-3')
    cmat_thickness = convert_unit(this_quad.cmaterial.thickness['value'], this_quad.cmaterial.thickness['unit'], 'in')
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

    quad_attrs = [bat_xdim, bat_ydim, bat_zdim, prop_dia, motor_body_dia, cmat_density, cmat_thickness, pmat_density,
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

    bat_xdim, bat_ydim, bat_zdim, prop_dia, motor_body_dia, cmat_density, cmat_thickness, \
        pmat_density, bat_weight, motor_weight, prop_weight, pmc_max_thrust, bat_voltage, bat_capacity, pmc_thrust_vec, \
        pmc_current_vec = quad_attrs

    endurance_req, payload_req, max_weight, max_size, maneuverability, \
        p_len, p_width, p_height, c_len, c_width, max_build_time, sensors = constraints

    # First estimate the vehicle size based on battery, prop, and motor. There are several constraints tested here.
    # 1) The maximum vehicle dimension must be less than the max_size constraint
    # 2) The dimension of the hub must be less than min(cutter_len, cutter_width)
    # 3) The length of the arm must be less than max(printer_len, printer_width). This assumes the other dimension of
    # the printer is sufficiently large, which is a fair assumption since the arm is long and narrow. This also assumes
    # the printer height is sufficient.

    # Call hublayout.hub_layout to size the hub for the chosen battery, sensors, and electronic component set (defined
    # within hublayout.hub_layout). See hublayout module for more information on the hub sizing function and what
    # hub_grid is. hub_layout returns the hub size in inches, the hub layer separation in inches, and the hub grid. Also
    # see hublayout.hublayout_simple
    try:
        hub_size, hub_separation, hub_grid = hublayout.hub_layout([bat_xdim, bat_ydim, bat_zdim], sensors)
    except hublayout.PlacementError as e:
        print str(e)
        return "Could not place sensors in/on hub.", 'N/A', None

    safe_factor = 1.15
    n_arms = 4
    prop_disc_separation_limited_len = safe_factor * (prop_dia/2/math.sin(math.pi/n_arms) + 0.75*motor_body_dia -
                                                      0.5*hub_size)
    prop_to_hub_limited_len = safe_factor * \
        (prop_dia/2 + 1.5*motor_body_dia/2)
    arm_len = max(prop_disc_separation_limited_len, prop_to_hub_limited_len)
    size = hub_size + 2*arm_len + prop_dia
    if size > max_size:
        return "Max dimension too large.", size, None
    if hub_size > min(c_len, c_width):
        return "Hub too large for cutter", hub_size, None
    if arm_len > max(p_len, p_width):
        return "Arms too long for printer.", arm_len, None

    n_layers = len(hub_grid)
    hub_area = hub_size**2 * n_layers
    hub_weight = cmat_density / 12**3 * cmat_thickness * hub_area
    hub_corner_len = hub_separation

    # I (Nate Beals) have no idea where this equation comes from. I pulled it straight from the VBA code.
    arm_vol_incube = (-0.59039*hub_separation**3) - (0.39684*arm_len*hub_corner_len**2) \
        + (0.10027*hub_corner_len*arm_len**2) + (2.35465*hub_separation**2) \
        + (2.06676*hub_corner_len**2) - (0.22142*arm_len*hub_corner_len) \
        - (9.04469e-2*arm_len**2) - (2.1687*hub_separation) - (0.9074*hub_corner_len) \
        + (0.92599*arm_len) - 0.99887
    arm_vol_ftcube = arm_vol_incube / (12**3)
    arm_weight = arm_vol_ftcube * pmat_density

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

    # Calculate estimated build time using equation from original MASR tool (point of origin unknown), and
    # compare to user requirement. Again, original equation in non-standard English units. Output of the build time
    # equation is hours.
    build_time = (-1.68036*arm_len*hub_separation**2 + 10.49405*hub_separation**2 +
                  4.85943*arm_len*hub_separation + 0.48171*arm_len*hub_corner_len -
                  29.25380*hub_separation - 2.59574*hub_corner_len - 3.27393*arm_len + 22.59885) * n_arms
    if build_time > max_build_time:
        return "Takes too long to build.", build_time, None

    # Since the alternative isn't infeasible by this point, it must be feasible. First convert some stuff back to metric
    size = convert_unit(size, 'in', 'm')
    vehicle_weight = convert_unit(vehicle_weight, 'lbf', 'N')
    payload_capacity = convert_unit(payload_capacity, 'lbf', 'N')
    hub_size = convert_unit(hub_size, 'in', 'm')
    hub_separation = convert_unit(hub_separation, 'in', 'm')
    arm_len = convert_unit(arm_len, 'in', 'm')
    vehicle_performance = [vehicle_weight, payload_capacity, vehicle_endurance, size, build_time]
    vehicle_geometry = [hub_size, hub_separation, hub_grid, arm_len, hub_corner_len]
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
    if not min(x) <= xint <= max(x):
        raise ValueError("Insufficient P/M Combo Data")

    if xint in x:
        yint = y[x.index[xint]]
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


# def score_alternatives_old(alternatives, weightings):
#     """
#     This function takes in a list of feasible alternatives, scores the alternatives based on user-specified importance
#     weightings, sets the Quadrotor.score attribute accordingly. The list of feasible alternatives is then returned.
#
#     The weightings input is a dictionary of the form:
#         weightings = {'perf_attr1': [perf_attr1_weight, 'high'], 'perf_attr2': [perf_attr2_weight, 'low'], ... }
#     where the 'high' and 'low' tell whether or not a high value of the attr is desirable or vice versa.
#
#     This function is called from oo_quad_GUI.AlternativesFrame.find_alternatives
#     """
#     # First we need to normalize the weighting values
#     wgt_vals = [float(val[0]) for val in weightings.values()]
#     wgt_sum = sum(wgt_vals)
#     norm_wgt_vals = [wgt/wgt_sum for wgt in wgt_vals]
#
#     # This weighting method takes the weightings selected by the user and uses them to calculate an alternative's
#     # "distance" from a positive and negative ideal score for a particular performance category which are equal to the
#     # best and worst score among alternatives. The 'high'/'low' option in the weightings dictionary tells whether a
#     # numerically high score corresponds to the positive ideal (== 'high') or a numerically low score is more desirable
#     # (== 'low'). After these "distances" are calculated for all performance categories they are used to calculate the
#     # total alternative score, given by the "relative closeness" to the positive ideal.
#     total_d_pos = [0] * len(alternatives)
#     total_d_neg = [0] * len(alternatives)
#     i = 0
#     for perf_attr in weightings:
#         weight = norm_wgt_vals[i]
#         # Find maximum attribute value among all alternatives
#         try:
#             max_val = max(getattr(quad, perf_attr)['value'] for quad in alternatives)
#         except TypeError:
#             max_val = max(getattr(quad, perf_attr) for quad in alternatives)
#         attr_scores = []
#         # Normalize all alternative attribute values using maximum value
#         for quad in alternatives:
#             try:
#                 quad_attr_norm = getattr(quad, perf_attr)['value'] / max_val
#             except TypeError:
#                 quad_attr_norm = getattr(quad, perf_attr) / max_val
#             attr_scores.append(quad_attr_norm)
#         # Define the positive and negative ideal scores among alternatives
#         if weightings[perf_attr][1] == 'high':
#             pos_ideal = max(attr_scores)
#             neg_ideal = min(attr_scores)
#         else:
#             pos_ideal = min(attr_scores)
#             neg_ideal = max(attr_scores)
#         d_pos = [weight*abs(pos_ideal-val) for val in attr_scores]
#         d_neg = [weight*abs(neg_ideal-val) for val in attr_scores]
#         total_d_pos = map(add, total_d_pos, d_pos)
#         total_d_neg = map(add, total_d_neg, d_neg)
#         i += 1
#
#     rel_closeness = map(lambda x, y: float(y)/(x+y), total_d_pos, total_d_neg)
#
#     i = 0
#     for quad in alternatives:
#         quad.score = rel_closeness[i]
#         i += 1
#
#     return alternatives