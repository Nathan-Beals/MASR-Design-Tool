from displayable import Displayable
from collections import OrderedDict
from tools import convert_unit


class Printer(Displayable):
    pretty_attr_dict = OrderedDict([('Name', []), ('Length', ['m', 'cm', 'in']), ('Width', ['m', 'cm', 'in']),
                                    ('Height', ['m', 'cm', 'in'])])
    real_attr_names = ['name', 'length', 'width', 'height']
    pretty_str = '3D printer'

    def __init__(self, attr_list):
        """
        attr_list = [['name'], ['length_val', 'length_unit'], ['width_val, 'width_unit'], ['height_val', 'height_unit']]
        """
        Displayable.__init__(self)
        name, length, width, height = self.process_input(attr_list)

        self.name = name
        self.length = length
        self.width = width
        self.height = height

    @staticmethod
    def process_input(attr_list):
        if attr_list[0][0] is None:
            raise ValueError("Printer must have a name.")
        else:
            name = str(attr_list[0][0])
        if attr_list[1][0] is None:
            raise ValueError("Printer must have a length.")
        else:
            length = {'value': convert_unit(float(attr_list[1][0]), str(attr_list[1][1]), 'std_metric'),
                      'unit': 'm'}
        if attr_list[2][0] is None:
            raise ValueError("Printer must have a width.")
        else:
            width = {'value': convert_unit(float(attr_list[2][0]), str(attr_list[2][1]), 'std_metric'),
                     'unit': 'm'}
        if attr_list[3][0] is None:
            raise ValueError("Printer must have a height.")
        else:
            height = {'value': convert_unit(float(attr_list[3][0]), str(attr_list[3][1]), 'std_metric'),
                      'unit': 'm'}
        return [name, length, width, height]