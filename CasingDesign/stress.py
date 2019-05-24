from config import *
import numpy as np


def biaxial_yield(yield_point, sigma_a, tension=True, collapse=True):
    """
    Yield point adjusted for biaxial stress conditions

    :param yield_point: yield point (psi)
    :type yield_point: float
    :param sigma_a: axial stress (psi)
    :type sigma_a: float
    :param tension: Is the pipe in tension?
    :type tension: bool
    :param collapse: collapse scenario?
    :type collapse: bool
    :return: yield point adjusted, Y_pa (psi)
    :rtype: float
    """

    if tension is True:
        if collapse is True:
            return yield_point * (np.sqrt(1 - 0.75 * (sigma_a / yield_point) ** 2) - 0.5 * (sigma_a / yield_point))
        else:
            return yield_point * (np.sqrt(1 - 0.75 * (sigma_a / yield_point) ** 2) + 0.5 * (sigma_a / yield_point))
    if collapse is True:
        return yield_point * (np.sqrt(1 - 0.75 * (sigma_a / yield_point) ** 2) + 0.5 * (sigma_a / yield_point))
    else:
        return yield_point * (np.sqrt(1 - 0.75 * (sigma_a / yield_point) ** 2) - 0.5 * (sigma_a / yield_point))


def triaxial_yield(yield_point, sigma_a, sigma_r, tension=True, collapse=True):
    """
    Yield point adjusted for triaxial stress conditions

    :param yield_point: yield point (psi)
    :type yield_point: float
    :param sigma_a: axial stress (psi)
    :type sigma_a: float
    :param sigma_r: radial stress (psi)
    :type sigma_r: float
    :param tension: Is the pipe in tension?
    :type tension: bool
    :param collapse: collapse scenario?
    :type collapse: bool
    :return: yield point adjusted, Y_pa (psi)
    :rtype: float
    """

    if tension is True:
        if collapse is True:
            return yield_point * (np.sqrt(1 - 0.75 * (sigma_a - sigma_r) / yield_point) -
                                  0.5 * (sigma_a - sigma_r) / yield_point) + sigma_r
        else:
            return yield_point * (np.sqrt(1 - 0.75 * (sigma_a - sigma_r) / yield_point) +
                                  0.5 * (sigma_a - sigma_r) / yield_point) + sigma_r
    if collapse is True:
        return yield_point * (np.sqrt(1 - 0.75 * (sigma_a - sigma_r) / yield_point) +
                              0.5 * (sigma_a - sigma_r) / yield_point) + sigma_r
    else:
        return yield_point * (np.sqrt(1 - 0.75 * (sigma_a - sigma_r) / yield_point) -
                              0.5 * (sigma_a - sigma_r) / yield_point) + sigma_r


def radial(od, id, Pi, Po):
    """
    Radial stress on a tubular due to pressure

    :param od: outer diameter, OD (in)
    :type od: float
    :param id: inner diameter, ID (in)
    :type id: float
    :param Pi: inside pressure, P_i (psi)
    :type Pi: float
    :param Po: outside pressure, P_o (psi)
    :type Po: float
    :return: radial stress, sigma_r (psi)
    :rtype: float
    """
    ri = id / 2
    ro = od / 2
    k1 = (ri ** 2 * Pi - ro ** 2 * Po) / (ro ** 2 - ri ** 2)
    k2 = (Pi - Po) * ri ** 2 * ro ** 2 / ((ro ** 2 - ri ** 2) * ri ** 2)

    return k1 - k2


def tangential(od, id, Pi, Po):
    """
    Tangential stress on a tubular due to pressure

    :param od: outer diameter, OD (in)
    :type od: float
    :param id: inner diameter, ID (in)
    :type id: float
    :param Pi: inside pressure, P_i (psi)
    :type Pi: float
    :param Po: outside pressure, P_o (psi)
    :type Po: float
    :return: tangential stress, sigma_t (psi)
    :rtype: float
    """
    ri = id / 2
    ro = od / 2
    k1 = (ri ** 2 * Pi - ro ** 2 * Po) / (ro ** 2 - ri ** 2)
    k2 = (Pi - Po) * ri ** 2 * ro ** 2 / ((ro ** 2 - ri ** 2) * ri ** 2)

    return k1 + k2


def axial(od, id, t_real):
    """
    Axial stress on a tubular due to pressure

    :param od: outer diameter, OD (in)
    :type od: float
    :param id: inner diameter, ID (in)
    :type id: float
    :param t_real: real tension (lbf)
    :type t_real: float
    :return: axial stress, sigma_a (psi)
    :rtype: float
    """
    A = np.pi / 4 * (od ** 2 - id ** 2)
    return t_real / A


def bending(od, id, t_eff, curvature):
    """
    Bending stress using the maximum of Lubinski or Beam Force

    :param od: outer diameter, OD (in)
    :type od: float
    :param id: inner diameter, ID (in)
    :type id: float
    :param t_eff: effective tension (lbf)
    :type t_eff: float
    :param curvature: curvature (deg/100 ft)
    :type curvature: float
    :return: bending stress, sigma_b (psi)
    :rtype: float
    """
    Acs = np.pi / 4 * (od ** 2 - id ** 2)
    Flub = lubinski(od, id, t_eff, curvature)
    Fbeam = beam(od, id, curvature)
    return max([Flub, Fbeam]) / Acs


def lubinski(od, id, t_eff, curvature):
    """
    Lubinski bending force

    :param od: outer diameter, OD (in)
    :type od: float
    :param id: inner diameter, ID (in)
    :type id: float
    :param t_eff: effective tension (lbf)
    :type t_eff: float
    :param curvature: curvature (deg/100 ft)
    :type curvature: float
    :return: Lubinski force, F_lub (psi)
    :rtype: float
    """
    curvature = curvature / 100
    num = 3385 * od * curvature * np.sqrt(t_eff) * np.sqrt((od ** 2 - id ** 2) / (od ** 2 + id ** 2))
    den = np.tanh(0.2 * np.sqrt(t_eff / (od ** 4 - id ** 4)))
    return num / den


def beam(od, id, curvature):
    """
    Beam bending force

    :param od: outer diameter, OD (in)
    :type od: float
    :param id: inner diameter, ID (in)
    :type id: float
    :param curvature: curvature (deg/100 ft)
    :type curvature: float
    :return: Beam force, F_beam (psi)
    :rtype: float
    """
    curvature = curvature / 100
    return 17135 * od * curvature * (od ** 2 - id ** 2)


def von_mises(sigma_r, sigma_t, sigma_a):
    """
    Von Mises stress condition without bending

    :param sigma_r: radial stress (psi)
    :type sigma_r: float
    :param sigma_t: tangential stress (psi)
    :type sigma_t: float
    :param sigma_a: axial stress (psi)
    :type sigma_a: float
    :return: Von Mises stress, sigma_vm (psi)
    :rtype: float
    """

    a = (sigma_r - sigma_t) ** 2
    b = (sigma_r - sigma_a) ** 2
    c = (sigma_t - sigma_a) ** 2
    return np.sqrt((a + b + c) / 2)


def von_mises_bending(sigma_r, sigma_t, sigma_a, sigma_b):
    """
    Von Mises stress condition with bending

    :param sigma_r: radial stress (psi)
    :type sigma_r: float
    :param sigma_t: tangential stress (psi)
    :type sigma_t: float
    :param sigma_a: axial stress (psi)
    :type sigma_a: float
    :param sigma_b: bending stress (psi)
    :type sigma_b: float
    :return: Von Mises stress, sigma_vm (psi)
    :rtype: float
    """

    a = (sigma_r - sigma_t) ** 2
    b = (sigma_r - (sigma_a - sigma_b)) ** 2
    c = (sigma_t - (sigma_a - sigma_b)) ** 2
    return np.sqrt((a + b + c) / 2)

