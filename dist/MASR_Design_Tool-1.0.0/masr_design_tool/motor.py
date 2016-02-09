from displayable import Displayable
from collections import OrderedDict
from unitconversion import convert_unit


class Motor(Displayable):
    pretty_attr_dict = OrderedDict([('Name', []), ('Weight', ['N', 'lbf', 'kg']), ('Kv', ['RPM/V']),
                                    ('Diameter', ['m', 'cm', 'in']), ('Cost (USD)', [])])
    real_attr_names = ['name', 'weight', 'Kv', 'body_diameter', 'cost']
    pretty_str = 'motor'

    def __init__(self, attr_list):
        Displayable.__init__(self)
        name, weight, Kv, body_diameter, cost = self.process_input(attr_list)

        self.name = name
        self.weight = weight
        self.Kv = Kv
        self.body_diameter = body_diameter
        self.cost = cost

    @staticmethod
    def process_input(attr_list):
        if attr_list[0][0] is None:
            raise ValueError("Motor must have a name.")
        else:
            name = str(attr_list[0][0])
        if attr_list[1][0] is None:
            raise ValueError("Motor must have a weight.")
        else:
            weight = {'value': convert_unit(float(attr_list[1][0]), str(attr_list[1][1]), 'std_metric'),
                      'unit': 'N'}
        if attr_list[2][0] is None:
            raise ValueError("Motor must have a velocity constant.")
        else:
            Kv = {'value': float(attr_list[2][0]), 'unit': str(attr_list[2][1])}
        if attr_list[3][0] is None:
            raise ValueError("Motor must have a body diameter.")
        else:
            body_diameter = {'value': convert_unit(float(attr_list[3][0]), str(attr_list[3][1]),
                                                   'std_metric'), 'unit': 'm'}
        try:
            cost = float(attr_list[4][0])
        except TypeError:
            cost = None
        return [name, weight, Kv, body_diameter, cost]