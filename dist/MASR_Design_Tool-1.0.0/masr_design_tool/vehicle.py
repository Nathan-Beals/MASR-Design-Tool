from displayable import Displayable
from collections import OrderedDict


class Vehicle(Displayable):
    """
    This class inherits from displayable.Displayable and defines the general performance characteristics of a vehicle.
    Currently the only class inheriting from Vehicle is quadrotor.Quadrotor, however, in the future additional vehicle
    types could be added (e.g., fixed wing, flapping wing, etc.). In this way all Vehicle types will share "performance"
    parameters by which they can be compared.
    """
    perf_attr_dict = OrderedDict([('Weight', ('N', 'lbf', 'kg')), ('Max Payload',  ('N', 'lbf', 'kg')),
                                  ('Endurance', ('min', 'hr')), ('Max Dimension', ('m', 'in', 'cm')),
                                  ('Build Time', ('hr', 'min'))])
    perf_attr_names = ['weight', 'max_payload', 'max_endurance', 'max_dimension', 'build_time']

    perf_attrs_export = zip(perf_attr_dict.keys(), perf_attr_names, perf_attr_dict.values())

    def __init__(self, performance=None):
        Displayable.__init__(self)

        if performance is None:
            performance = [0] * len(self.perf_attr_names)

        weight, max_payload, max_endurance, max_dimension, build_time = performance

        self.weight = weight
        self.max_payload = max_payload
        self.max_endurance = max_endurance
        self.max_dimension = max_dimension
        self.build_time = build_time

    def set_performance(self, performance):
        """
        Set performance method for when the performance needs to be changed after initialization of the object,
        specifically when the vehicle object has been determined to be feasible and performance metrics have been
        calculated.
        """
        weight, max_payload, max_endurance, max_dimension, build_time = performance
        self.weight = {'value': weight, 'unit': 'N'}
        self.max_payload = {'value': max_payload, 'unit': 'N'}
        self.max_endurance = {'value': max_endurance, 'unit': 'min'}  # Endurance in minutes
        self.max_dimension = {'value': max_dimension, 'unit': 'm'}
        self.build_time = {'value': build_time, 'unit': 'hr'}    # Build time in hours
