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