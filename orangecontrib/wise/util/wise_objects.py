import numpy
from collections import OrderedDict

class WiseOutput(object):
    source = None
    optical_element = None
    wavefront = None

    def __init__(self, source = WiseSource(), optical_element = WiseOpticalElement(), wavefront = Wavefront()):
        self.source = source
        self.optical_element = optical_element
        self.wavefront = wavefront

class Wavefront(object):
    electric_fields = None
    positions = None

    def __init__(self, electric_fields = numpy.zeros(100), positions = numpy.zeros(100)):
        self.electric_fields = electric_fields
        self.positions = positions


    def get_intensities(self):
        return numpy.abs(self.electric_fields)**2

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
    