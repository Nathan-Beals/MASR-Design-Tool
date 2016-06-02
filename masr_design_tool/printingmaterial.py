from displayable import Displayable
from collections import OrderedDict
from tools import convert_unit


class Printingmaterial(Displayable):
    pretty_attr_dict = OrderedDict([('Name', []), ('Density', [r'kg*m^-3', r'slug*ft^-3', r'lbf*ft^-3']),
                                    ('C-S Area', ['m^2', 'cm^2', 'in^2'])])
    real_attr_names = ['name', 'density', 'cs_area']
    pretty_str = 'printing material'

    def __init__(self, attr_list):
        Displayable.__init__(self)
        name, density, cs_area = self.process_input(attr_list)

        self.name = name
        self.density = density
        self.cs_area = cs_area

    @staticmethod
    def process_input(attr_list):
        if attr_list[0][0] is None:
            raise ValueError("Printing material must have a name.")
        else:
            name = str(attr_list[0][0])
        if attr_list[1][0] is None:
            raise ValueError("Printing material must have a density.")
        else:
            density = {'value': convert_unit(float(attr_list[1][0]), str(attr_list[1][1]), 'std_metric'),
                       'unit': r'kg*m^-3'}
        if attr_list[2][0] is None:
            raise ValueError("Printing material must have a cross-sectional area.")
        else:
            cs_area = {'value': convert_unit(float(attr_list[2][0]), str(attr_list[2][1]), 'std_metric'),
                       'unit': r'm^2'}
        return [name, density, cs_area]
