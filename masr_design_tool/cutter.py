from collections import OrderedDict
from unitconversion import convert_unit
from displayable import Displayable


class Cutter(Displayable):
    pretty_attr_dict = OrderedDict([('Name', []), ('Length', ['m', 'cm', 'in']), ('Width', ['m', 'cm', 'in'])])
    real_attr_names = ['name', 'length', 'width']
    pretty_str = 'laser cutter'

    def __init__(self, attr_list):
        Displayable.__init__(self)
        name, length, width = self.process_input(attr_list)

        self.name = name
        self.length = length
        self.width = width

    @staticmethod
    def process_input(attr_list):
        if attr_list[0][0] is None:
            raise ValueError("Laser cutter must have a name.")
        else:
            name = str(attr_list[0][0])
        if attr_list[1][0] is None:
            raise ValueError("Laser cutter must have a length value.")
        else:
            length = {'value': convert_unit(float(attr_list[1][0]), str(attr_list[1][1]), 'std_metric'),
                      'unit': 'm'}
        if attr_list[2][0] is None:
            raise ValueError("Laser cutter must have a width value.")
        else:
            width = {'value': convert_unit(float(attr_list[2][0]), str(attr_list[2][1]), 'std_metric'),
                     'unit': 'm'}
        return [name, length, width]
