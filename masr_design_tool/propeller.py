from displayable import Displayable
from collections import OrderedDict
from tools import convert_unit


class Propeller(Displayable):
    pretty_attr_dict = OrderedDict([('Name', []), ('Weight', ['N', 'lbf', 'kg']), ('Diameter', ['m', 'cm', 'in']),
                                    ('Pitch', ['m', 'cm', 'in']), ('N-blades', []), ('Cost (USD)', [])])
    real_attr_names = ['name', 'weight', 'diameter', 'pitch', 'n_blades', 'cost']
    pretty_str = 'propeller'

    def __init__(self, attr_list):
        Displayable.__init__(self)
        name, weight, diameter, pitch, n_blades, cost = self.process_input(attr_list)

        self.name = name
        self.weight = weight
        self.diameter = diameter
        self.pitch = pitch
        self.n_blades = n_blades
        self.cost = cost

    @staticmethod
    def process_input(attr_list):
        if attr_list[0][0] is None:
            raise ValueError("Propeller must have a name.")
        else:
            name = str(attr_list[0][0])
        if attr_list[1][0] is None:
            raise ValueError("Propeller must have a weight.")
        else:
            weight = {'value': convert_unit(float(attr_list[1][0]), str(attr_list[1][1]), 'std_metric'),
                      'unit': 'N'}
        if attr_list[2][0] is None:
            raise ValueError("Propeller must have a diameter.")
        else:
            diameter = {'value': convert_unit(float(attr_list[2][0]), str(attr_list[2][1]), 'std_metric'),
                        'unit': 'm'}
        if attr_list[3][0] is None:
            raise ValueError("Propeller must have a pitch.")
        else:
            pitch = {'value': convert_unit(float(attr_list[3][0]), str(attr_list[3][1]), 'std_metric'),
                     'unit': 'm'}
        if attr_list[4][0] is None:
            raise ValueError("Propeller must have a number of blades.")
        else:
            n_blades = int(attr_list[4][0])
        try:
            cost = float(attr_list[5][0])
        except TypeError:
            cost = None
        return [name, weight, diameter, pitch, n_blades, cost]
