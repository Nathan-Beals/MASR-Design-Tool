from displayable import Displayable
from collections import OrderedDict
from unitconversion import convert_unit


class Cuttingmaterial(Displayable):
    pretty_attr_dict = OrderedDict([('Name', []), ('Density', [r'kg*m^-3', r'slug*ft^-3', r'lbf*ft^-3']),
                                    ('Thickness', ['m', 'cm', 'in'])])
    real_attr_names = ['name', 'density', 'thickness']
    pretty_str = 'cutting material'

    def __init__(self, attr_list):
        Displayable.__init__(self)
        name, density, thickness = self.process_input(attr_list)

        self.name = name
        self.density = density
        self.thickness = thickness

    @staticmethod
    def process_input(attr_list):
        if attr_list[0][0] is None:
            raise ValueError("Cutting material must have a name.")
        else:
            name = str(attr_list[0][0])
        if attr_list[1][0] is None:
            raise ValueError("Cutting material must have a density.")
        else:
            density = {'value': convert_unit(float(attr_list[1][0]), str(attr_list[1][1]), 'std_metric'),
                       'unit': r'kg*m^-3'}
        if attr_list[2][0] is None:
            raise ValueError("Cutting material must have thickness.")
        else:
            thickness = {'value': convert_unit(float(attr_list[2][0]), str(attr_list[2][1]),
                                               'std_metric'), 'unit': 'm'}
        return [name, density, thickness]