class ConversionError(Exception):
    pass


class CapacityConvError(ConversionError):
    pass


def convert_unit(val, unit_start, unit_end, voltage=None):
    weight_per_newton = {'N': 1, 'lbf': 0.2248, 'kg': 1/9.81}
    length_per_meter = {'m': 1, 'cm': 100, 'in': 39.37, 'ft': 3.281}
    if voltage is not None:
        capacity_per_Wh = {'Wh': 1, 'mAh': float(voltage)/1000}
    else:
        capacity_per_Wh = {'mAh': 1, 'Wh': 1}
    density_per_metric = {'kg*m^-3': 1, 'slug*ft^-3': 0.00194, 'lbf*ft^-3': 0.00194/32.2}
    cs_area_per_sqmeter = {'m^2': 1, 'cm^2': 10000, 'in^2': 1550, 'ft^2': 10.764}
    time_per_sec = {'s': 1, 'min': float(1)/60, 'hr': float(1)/3600}
    unit_list_of_dict = [weight_per_newton, length_per_meter, capacity_per_Wh, density_per_metric, cs_area_per_sqmeter,
                         time_per_sec]

    # Handle None inputs
    if val is None:
        return None

    # Handle case during object initialization when everything will be converted to standard metric units
    if unit_end == 'std_metric':
        if unit_start in weight_per_newton:
            val_end = float(val)/weight_per_newton[unit_start]
            return val_end
        elif unit_start in length_per_meter:
            val_end = float(val)/length_per_meter[unit_start]
            return val_end
        elif unit_start in capacity_per_Wh:
            if unit_start == 'mAh' and voltage is None:
                raise CapacityConvError("If inputting capacity as mAh must give voltage or num cells")
            else:
                val_end = float(val)/capacity_per_Wh[unit_start]
                return val_end
        elif unit_start in density_per_metric:
            val_end = float(val)/density_per_metric[unit_start]
            return val_end
        elif unit_start in cs_area_per_sqmeter:
            val_end = float(val)/cs_area_per_sqmeter[unit_start]
            return val_end
        elif unit_start in time_per_sec:
            val_end = float(val)/time_per_sec[unit_start]
            return val_end
        else:
            print unit_start
            raise ConversionError("Problem converting unit during __init__")

    # Handle cases when the user wants to change the units for visualization purposes
    if unit_start == unit_end:
        return float(val)
    elif unit_start in capacity_per_Wh.keys() and voltage is None:
        raise CapacityConvError("If converting mAh <--> Wh, must give voltage.")
    else:
        try:
            for d in unit_list_of_dict:
                if unit_start in d.keys():
                    unit_start_conv = d[unit_start]
                    unit_end_conv = d[unit_end]
                    val_end = float(val) * unit_end_conv / unit_start_conv
                    return val_end
            raise ValueError("Start unit, %s, not found." % unit_start)
        except ValueError as error:
            print error
        except KeyError:
            print "End unit not found: stu=%s eu=%s" % (unit_start, unit_end)
            raise


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

    if not min(x) <= xint <= max(x) and not any(float_is_close(xint, xval) for xval in [min(x), max(x)]):
        print x
        print xint
        raise ValueError("Insufficient Data")

    for i, xval in enumerate(x):
        if float_is_close(xval, xint):
            yint = y[i]
            return yint

    for i, xp in enumerate(x):
        if xint < xp:
            p2 = (xp, y[i])
            p1 = (x[i-1], y[i-1])
            slope = (p2[1]-p1[1])/(p2[0]-p1[0])
            yint = slope*(xint-p1[0]) + p1[1]
            return yint


def float_is_close(f1, f2, rel_tol=1e-09, abs_tol=0.000001):
        """
        Floating point "equals" function
        """
        return abs(f1-f2) <= max(rel_tol*max(abs(f1), abs(f2)), abs_tol)