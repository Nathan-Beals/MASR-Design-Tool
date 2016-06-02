from collections import OrderedDict
from tools import convert_unit
from displayable import Displayable


class Sensor(Displayable):
    pretty_attr_dict = OrderedDict([('Name', []), ('Weight', ['N', 'lbf', 'kg']), ('XDim', ['m', 'cm', 'in']),
                                    ('YDim', ['m', 'cm', 'in']), ('ZDim', ['m', 'cm', 'in']), ('Required Layer', []),
                                    ('Required Orientation', [])])
    real_attr_names = ['name', 'weight', 'xdim', 'ydim', 'zdim', 'req_layer', 'req_orient']
    pretty_str = 'sensor'

    def __init__(self, attr_list):
        Displayable.__init__(self)
        name, weight, xdim, ydim, zdim, req_layer, req_orient = self.process_input(attr_list)
        self.name = name
        self.weight = weight
        self.xdim = xdim
        self.ydim = ydim
        self.zdim = zdim
        self.req_layer = req_layer
        self.req_orient = req_orient

    @staticmethod
    def process_input(attr_list):
        if attr_list[0][0] is None:
            raise ValueError("Sensor must have a name.")
        else:
            name = attr_list[0][0]
        if attr_list[1][0] is None:
            raise ValueError("Sensor must have a weight.")
        else:
            weight = {'value': convert_unit(float(attr_list[1][0]), str(attr_list[1][1]), 'std_metric'), 'unit': 'N'}
        if attr_list[2][0] is None:
            raise ValueError("Sensor must have an X-dimension.")
        else:
            xdim = {'value': convert_unit(float(attr_list[2][0]), str(attr_list[2][1]), 'std_metric'), 'unit': 'm'}
        if attr_list[3][0] is None:
            raise ValueError("Sensor must have a Y-dimension.")
        else:
            ydim = {'value': convert_unit(float(attr_list[3][0]), str(attr_list[3][1]), 'std_metric'), 'unit': 'm'}
        if attr_list[4][0] is None:
            raise ValueError("Sensor must have a Z-dimension.")
        else:
            zdim = {'value': convert_unit(float(attr_list[4][0]), str(attr_list[4][1]), 'std_metric'), 'unit': 'm'}
        try:
            if attr_list[5][0] is None:
                req_layer = attr_list[5][0]
            elif attr_list[5][0].lower() in ['top', 'bottom']:
                req_layer = attr_list[5][0].lower()
            else:
                raise ValueError("Required layer must be 'top', 'bottom', or leave blank.")
        except AttributeError:
            raise ValueError("Required layer must be 'top', 'bottom', or leave blank.")
        try:
            if attr_list[6][0] is None:
                req_orient = attr_list[6][0]
            elif attr_list[6][0].lower() in ['forward', 'sideways']:
                req_orient = attr_list[6][0].lower()
            else:
                raise ValueError("Required orientation must be 'forward', 'sideways', or leave blank.")
        except AttributeError:
            raise ValueError("Required orientation must be 'forward', 'sideways', or leave blank.")
        return [name, weight, xdim, ydim, zdim, req_layer, req_orient]