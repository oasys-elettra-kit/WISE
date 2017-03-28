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

    def __init__(self, decorated):
        self._decorated = decorated

    @synchronized_method
    def Instance(self):
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

from  orangecontrib.wise.util.wise_objects import WiseNumericalIntegrationParameters

class WisePropagationParameters(object):
    MIRROR_ONLY = 0
    DETECTOR_ONLY = 1
    MIRROR_AND_DETECTOR = 2

    def __init__(self,
                 propagation_type = MIRROR_ONLY,
                 source = None,
                 optical_element = None,
                 wavefront = None,
                 numerical_integration_parameters = None,
                 defocus_sweep = 0.0,
                 n_pools = 0):
        self.propagation_type = propagation_type
        self.source = source
        self.optical_element = optical_element
        self.wavefront = wavefront
        self.numerical_integration_parameters = numerical_integration_parameters
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
import wiselib.Rayman as Rayman

class HuygensIntegralPropagationOutput(object):
    def __init__(self,
                 mir_x,
                 mir_y,
                 mir_s,
                 mir_E,
                 residuals,
                 number_of_points,
                 det_x,
                 det_y,
                 det_s,
                 electric_fields,
                 HEW):
        self.mir_x = mir_x
        self.mir_y = mir_y
        self.mir_s = mir_s
        self.mir_E = mir_E
        self.residuals = residuals
        self.number_of_points = number_of_points
        self.det_x = det_x
        self.det_y = det_y
        self.det_s = det_s
        self.electric_fields = electric_fields
        self.HEW = HEW

class HuygensIntegralPropagator(AbstractWisePropagator):

    def get_algorithm(self):
        return WisePropagationAlgorithms.HuygensIntegral

    def handle_request(self, parameters=WisePropagationParameters()):
        elliptic_mirror = parameters.optical_element
        source = parameters.source
        numerical_integration_parameters = parameters.numerical_integration_parameters

        #print("\nPropagation Type = " + str(parameters.propagation_type) + "\n[0=Mirror Only, 1=Detector Only (no calculation of mirror E), 2=Mirror+Detector]\n")

        if parameters.propagation_type == WisePropagationParameters.MIRROR_ONLY or \
            parameters.propagation_type == WisePropagationParameters.MIRROR_AND_DETECTOR:

            theta_0 = elliptic_mirror.pTan_Angle
            theta_1 = numpy.arctan(-1/elliptic_mirror.p2[0])

            if numerical_integration_parameters.calculation_type == WiseNumericalIntegrationParameters.AUTOMATIC:
                number_of_points = Rayman.SamplingCalculator(source.Lambda,
                                                             elliptic_mirror.f2,
                                                             elliptic_mirror.L,
                                                             numerical_integration_parameters.detector_size,
                                                             theta_0,
                                                             theta_1)
            else:
                number_of_points = numerical_integration_parameters.number_of_points

            # Wavefront on mirror surface
            mir_x, mir_y = elliptic_mirror.GetXY_MeasuredMirror(number_of_points, 0)
            residuals = elliptic_mirror.LastResidualUsed

            mir_s = Rayman.xy_to_s(mir_x, mir_y)
            mir_E = source.EvalField_XYLab(mir_x, mir_y)

            #print("*** calculated new mir_x, mir_y, mir_s, mir_E")

        elif parameters.propagation_type == WisePropagationParameters.DETECTOR_ONLY:
            mir_x = parameters.wavefront.positions_x
            mir_y = parameters.wavefront.positions_y
            mir_s = parameters.wavefront.positions_s
            mir_E = parameters.wavefront.electric_fields
            residuals = parameters.wavefront.residuals
            number_of_points = numerical_integration_parameters.calculated_number_of_points

            #print("*** used mir_x, mir_y, mir_s, mir_E from mirror")

        if parameters.propagation_type == WisePropagationParameters.DETECTOR_ONLY or \
            parameters.propagation_type == WisePropagationParameters.MIRROR_AND_DETECTOR:
            # wave front at F2
            det_x, det_y = elliptic_mirror.GetXY_TransversePlaneAtF2(numerical_integration_parameters.detector_size,
                                                                     number_of_points,
                                                                     parameters.defocus_sweep)
            det_s = Rayman.xy_to_s(det_x, det_y)


            electric_fields = Rayman.HuygensIntegral_1d_MultiPool(source.Lambda,
                                                                  mir_E,
                                                                  mir_x,
                                                                  mir_y,
                                                                  det_x,
                                                                  det_y,
                                                                  parameters.n_pools)
            try:
                hew = Rayman.HalfEnergyWidth_1d(abs(electric_fields)**2, Step = numpy.mean(numpy.diff(det_s)))
            except ValueError as error:
                if "cannot convert float NaN to integer" in str(error):
                    raise Exception("Inconsistent source parameters.\nMaybe " + "\u0394" + "Theta is too big.")

            #print("*** calculated det_x, det_y, det_s, electric_fields, hew on detector")

            return HuygensIntegralPropagationOutput(mir_x,
                                                    mir_y,
                                                    mir_s,
                                                    mir_E,
                                                    residuals,
                                                    number_of_points,
                                                    det_x,
                                                    det_y,
                                                    det_s,
                                                    electric_fields,
                                                    hew)
        else:
            return HuygensIntegralPropagationOutput(mir_x,
                                                    mir_y,
                                                    mir_s,
                                                    mir_E,
                                                    residuals,
                                                    number_of_points,
                                                    None,
                                                    None,
                                                    None,
                                                    None,
                                                    None)

if __name__ == "__main__":

    chain1 = WisePropagatorsChain.Instance()
    chain2 = WisePropagatorsChain.Instance()

    print(chain1.do_propagation(None, None))

    print(chain1 is chain2)