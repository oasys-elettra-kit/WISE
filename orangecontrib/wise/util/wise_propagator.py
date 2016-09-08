###################################################################
# DO NOT TOUCH THIS CODE -- BEGIN
###################################################################
import threading

def synchronized_method(method):

    outer_lock = threading.Lock()
    lock_name = "__"+method.__name__+"_lock"+"__"

    def sync_method(self, *args, **kws):
        with outer_lock:
            if not hasattr(self, lock_name): setattr(self, lock_name, threading.Lock())
            lock = getattr(self, lock_name)
            with lock:
                return method(self, *args, **kws)

    return sync_method

class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Other than that, there are
    no restrictions that apply to the decorated class.

    To get the singleton instance, use the `Instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    Limitations: The decorated class cannot be inherited from.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    @synchronized_method
    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)

###################################################################
# DO NOT TOUCH THIS CODE -- END
###################################################################

@Singleton
class WisePropagatorsChain(object):
    def __init__(self):
       self.initialize_chain()

    def initialize_chain(self):
        self.propagators_chain = []
        self.propagators_chain.append(HuygensIntegralPropagator())

    def do_propagation(self, propagation_parameters, algorithm):
        for propagator in self.propagators_chain:
            if propagator.is_handler(algorithm):
                return propagator.handle_request(parameters=propagation_parameters)

        return None

class WisePropagationAlgorithms:
    HuygensIntegral = "HuygensIntegral"

class WisePropagationParameters(object):
    def __init__(self,
                 source = None,
                 optical_element = None,
                 detector_size = 0.0,
                 defocus_sweep = 0.0,
                 n_pools = 0):
        self.optical_element = optical_element
        self.source = source
        self.detector_size = detector_size
        self.defocus_sweep = defocus_sweep
        self.n_pools = n_pools

class AbstractWisePropagator(object):

    def __init__(self):
        super().__init__()

    def get_algorithm(self):
        raise NotImplementedError("This method is abstract")

    def is_handler(self, algorithm):
        return algorithm == self.get_algorithm()

    def handle_request(self, parameters=WisePropagationParameters()):
        raise NotImplementedError("This method is abstract")

###################################################################
###################################################################
###################################################################

import numpy
import wiselib.Rayman5 as Rayman

class HuygensIntegralPropagationOutput(object):
    def __init__(self, mir_s, mir_E, det_s, electric_fields, HEW):
        self.mir_s = mir_s
        self.mir_E = mir_E
        self.det_s = det_s
        self.electric_fields = electric_fields
        self.HEW = HEW

class HuygensIntegralPropagator(AbstractWisePropagator):

    def get_algorithm(self):
        return WisePropagationAlgorithms.HuygensIntegral

    def handle_request(self, parameters=WisePropagationParameters()):
        elliptic_mirror = parameters.optical_element
        source = parameters.source

        theta_0 = elliptic_mirror.pTan_Angle
        theta_1 = numpy.arctan(-1/elliptic_mirror.p2[0])
        det_size = parameters.detector_size

        n_auto = Rayman.SamplingCalculator(source.Lambda,
                                           elliptic_mirror.f2,
                                           elliptic_mirror.L,
                                           det_size,
                                           theta_0,
                                           theta_1)

        # Piano specchio (Sorgente=>Specchio)
        mir_x, mir_y = elliptic_mirror.GetXY_MeasuredMirror(n_auto, 0)
        mir_s = Rayman.xy_to_s(mir_x, mir_y)
        mir_E = source.EvalField_XYLab(mir_x, mir_y)
        # wave front at F2
        det_x, det_y = elliptic_mirror.GetXY_TransversePlaneAtF2(det_size, n_auto, parameters.defocus_sweep)
        det_s = Rayman.xy_to_s(det_x, det_y)

        electric_fields = Rayman.HuygensIntegral_1d_MultiPool(source.Lambda,
                                                              mir_E,
                                                              mir_x,
                                                              mir_y,
                                                              det_x,
                                                              det_y,
                                                              parameters.n_pools)

        hew = Rayman.HalfEnergyWidth_1d(abs(electric_fields)**2, Step = numpy.sqrt((det_x[0] - det_x[-1])**2 + (det_y[0] - det_y[-1])**2))



        return HuygensIntegralPropagationOutput(mir_s,
                                                mir_E,
                                                det_s,
                                                electric_fields,
                                                hew)

if __name__ == "__main__":

    chain1 = WisePropagatorsChain.Instance()
    chain2 = WisePropagatorsChain.Instance()

    print(chain1.do_propagation(None, None))

    print(chain1 is chain2)