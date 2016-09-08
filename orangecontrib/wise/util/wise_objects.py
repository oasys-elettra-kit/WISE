import numpy
from collections import OrderedDict

class Wavefront(object):
    electric_fields = None
    positions = None

    def __init__(self, electric_fields=numpy.zeros(100), positions=numpy.zeros(100)):
        self.electric_fields = electric_fields
        self.positions = positions

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

class WiseOutput(object):
    _source = None
    _optical_element = None
    _wavefront = None

    def __init__(self, source=None, optical_element=None, wavefront=None):
        self._source = source
        self._optical_element = optical_element
        self._wavefront = wavefront

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