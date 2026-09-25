"""Explicit model-domain failures, distinct from race termination."""


class ModelValidationError(ValueError):
    """Invalid model input, configured physical limit, or propagation domain."""


class FrenetGeometryError(ValueError):
    """Invalid Frenet coordinate geometry; the denominator must not be clipped."""


class VehicleModelValidityError(ModelValidationError):
    """Vehicle/tire/load model evaluated outside its explicitly supported domain."""


class LowSpeedValidityError(VehicleModelValidityError):
    """Dynamic slip-angle model is invalid below its configured minimum speed."""
