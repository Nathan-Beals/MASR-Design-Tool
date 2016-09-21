import shelve
from operator import add

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
    platforms = ['Quadmultipiece']

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
                for platform in platforms:
                    this_vehicle = getattr(__import__(platform.lower()), platform)(pmcombo, battery, pmaterial)
                    feasibility, performance, geometry = this_vehicle.is_feasible(constraints)
                    if feasibility != 'true':
                        #   If not feasible return reason for fail and % off from requirement
                        this_vehicle.feasible = (feasibility, performance)
                    else:
                        this_vehicle.set_performance(performance)
                        this_vehicle.set_geometry(geometry)
                    alternatives.append(this_vehicle)

    pmcombo_db.close()
    battery_db.close()
    print_material_db.close()

    return alternatives


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