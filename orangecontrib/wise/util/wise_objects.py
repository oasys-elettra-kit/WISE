import numpy
from collections import OrderedDict

class WiseWavefront(object):
    positions_x = None
    positions_y = None
    positions_s = None
    electric_fields = None
    height_errors = None

    def __init__(self,
                 positions_x=numpy.zeros(100),
                 positions_y=numpy.zeros(100),
                 positions_s=numpy.zeros(100),
                 electric_fields=numpy.zeros(100),
                 height_errors=numpy.zeros(100)):
        self.positions_x = positions_x
        self.positions_y = positions_y
        self.positions_s = positions_s
        self.electric_fields = electric_fields
        self.height_errors = height_errors

class WiseSource(object):
    inner_wise_source = None
    properties = OrderedDict()
    
    def __init__(self, inner_wise_source=None):
        self.inner_wise_source = inner_wise_source
        
    def set_property(self, key, value):
        self.properties[key] = value
    
    def get_property(self, key):
        return self.properties[key]
    
class WiseOpticalElement(object):
    inner_wise_optical_element = None
    properties = OrderedDict()
    
    def __init__(self, inner_wise_optical_element=None):
        self.inner_wise_optical_element = inner_wise_optical_element
        
    def set_property(self, key, value):
        self.properties[key] = value
    
    def get_property(self, key):
        return self.properties[key]

class WiseNumericalIntegrationParameters:
    AUTOMATIC = 0
    USER_DEFINED = 1

    calculation_type = 0
    detector_size = 0.0
    number_of_points = 0
    calculated_number_of_points = 0

    def __init__(self, calculation_type=AUTOMATIC, detector_size=0.0, number_of_points=0, calculated_number_of_points=0):
        self.calculation_type = calculation_type
        self.detector_size = detector_size
        self.number_of_points = number_of_points
        self.calculated_number_of_points = calculated_number_of_points

class WiseOutput(object):
    _source = None
    _optical_element = None
    _wavefront = None
    _numerical_integration_parameters = None

    def __init__(self,
                 source=None,
                 optical_element=None,
                 wavefront=None,
                 numerical_integration_parameters=None):
        self._source = source
        self._optical_element = optical_element
        self._wavefront = wavefront
        self._numerical_integration_parameters = numerical_integration_parameters

    def has_source(self):
        return not self._source is None

    def get_source(self):
        return self._source

    def has_optical_element(self):
        return not self._optical_element is None

    def get_optical_element(self):
        return self._optical_element

    def has_wavefront(self):
        return not self._wavefront is None

    def get_wavefront(self):
        return self._wavefront

    def has_numerical_integration_parameters(self):
        return not self._numerical_integration_parameters is None

    def get_numerical_integration_parameters(self):
        return self._numerical_integration_parameters

class WisePreInputData:

    NONE = "None"

    def __init__(self,
                figure_error_file=NONE,
                figure_error_step=0.0,
                figure_user_units_to_m=1.0,
                roughness_file=NONE,
                roughness_x_scaling=1.0,
                roughness_y_scaling=1.0
                ):
        super().__init__()

        self.figure_error_file = figure_error_file
        self.figure_error_step = figure_error_step
        self.figure_user_units_to_m = figure_user_units_to_m

        self.roughness_file = roughness_file
        self.roughness_x_scaling =roughness_x_scaling
        self.roughness_y_scaling = roughness_y_scaling