from Utilities import unitconverter as units
from CasingDesign import fluids, tubulars, api, stress
from copy import copy
from config import *
import numpy as np


def casing_strength(master):
    """
    Calculates the casing strength of the casing for all depths of one "scenario" object.
    Updates the Master scenario object

    :param master: master scenario
    :type master: Scenario
    """

    for i in range(len(master.md)):
        master.strength_burst.append(api.burst(master.od[i], master.id[i], master.wpf[i], master.grade[i], master.yp[i],
                                               coupling_type=master.conn[i], leak=leak_resistance))
        master.strength_joint.append(api.tensile_joint(master.od[i], master.id[i], master.wpf[i], master.grade[i],
                                                       master.yp[i], master.conn[i]))
        master.strength_tensile.append(api.tensile_body(master.od[i], master.id[i], master.yp[i]))
        master.strength_collapse.append(api.collapse(master.od[i], master.id[i], master.yp[i]))
        master.strength_collapse_biax.append(api.collapse(master.od[i], master.id[i], master.ypadj[i]))


def master_scenario(master, scenarios):
    """
    Defines the master scenario which is the worst case for each failure mode

    :param master: master scenario
    :type master: Scenario
    :param scenarios: scenarios list
    :type scenarios: list
    """

    burst_list = list()
    collapse_list = list()
    tension_list = list()

    for scenario in scenarios:
        if scenario.scenario == 'Burst':
            burst_list.append(scenario)
        if scenario.scenario == 'Collapse':
            collapse_list.append(scenario)
        if scenario.scenario == 'Tensile':
            tension_list.append(scenario)

    for i in range(len(burst_list[0].md)):
        shortlist = list()
        shortlist1 = list()
        for j in range(len(burst_list)):
            shortlist.append(burst_list[j].burst[i])
            shortlist1.append(burst_list[j])
        jmax = np.argmax(np.array(shortlist))
        master.burst.append(copy(shortlist1[jmax].burst[i]))
        master.md.append(copy(shortlist1[jmax].md[i]))
        master.od.append(copy(shortlist1[jmax].od[i]))
        master.id.append(copy(shortlist1[jmax].id[i]))
        master.wpf.append(copy(shortlist1[jmax].wpf[i]))
        master.grade.append(copy(shortlist1[jmax].grade[i]))
        master.conn.append(copy(shortlist1[jmax].conn[i]))
        master.yp.append(copy(shortlist1[jmax].yp[i]))

        shortlist = list()
        shortlist1 = list()
        for j in range(len(collapse_list)):
            shortlist.append(collapse_list[j].collapse[i])
            shortlist1.append(collapse_list[j])
        jmax = np.argmax(np.array(shortlist))
        master.collapse.append(copy(shortlist1[jmax].collapse[i]))
        master.pin.append(copy(shortlist1[jmax].pin[i]))
        master.pout.append(copy(shortlist1[jmax].pout[i]))
        master.axial.append(copy(shortlist1[jmax].axial[i]))
        master.radial.append(copy(shortlist1[jmax].radial[i]))
        master.tangential.append(copy(shortlist1[jmax].tangential[i]))
        master.treal.append(copy(shortlist1[jmax].treal[i]))
        master.teff.append(copy(shortlist1[jmax].teff[i]))
        master.scenario = 'Collapse'

        shortlist = list()
        shortlist1 = list()
        for scenario in scenarios:
            shortlist.append(scenario.vonmises[i])
            shortlist1.append(scenario)
        jmax = np.argmax(np.array(shortlist))
        master.vonmises.append(copy(shortlist1[jmax].vonmises[i]))

    yield_pt_adjust([master])
    for i in range(len(tension_list[0].md)):
        shortlist = list()
        shortlist1 = list()
        for j in range(len(tension_list)):
            shortlist.append(tension_list[j].treal[i])
            shortlist1.append(tension_list[j])
        jmax = np.argmax(np.array(shortlist))
        # master.treal[i] = shortlist1[jmax].treal[i]
        # master.teff[i] = shortlist1[jmax].teff[i]


def stress_state(scenarios):
    """
    Stress State for all tubulars.
    Updates the scenario object

    :param scenarios: scenarios list
    :type scenarios: list
    """
    for scenario in scenarios:
        for i in range(len(scenario.md)):
            scenario.axial.append(stress.axial(scenario.od[i], scenario.id[i], scenario.treal[i]))
            scenario.radial.append(stress.radial(scenario.od[i], scenario.id[i], scenario.pin[i], scenario.pout[i]))
            scenario.tangential.append(stress.tangential(scenario.od[i], scenario.id[i], scenario.pin[i], scenario.pout[i]))
            scenario.vonmises.append(stress.von_mises(scenario.radial[i], scenario.tangential[i], scenario.axial[i]))


def yield_pt_adjust(scenarios):
    """
    Biaxial yield point adjusted for collapse
    Updates the scenario object

    :param scenarios: scenarios list
    :type scenarios: list
    """
    for scenario in scenarios:
        for i in range(len(scenario.md)):
            if scenario.scenario == 'Collapse':
                if scenario.treal[i] >= 0:
                    scenario.ypadj.append(stress.biaxial_yield(scenario.yp[i], scenario.axial[i], tension=True))
                else:
                    scenario.ypadj.append(stress.biaxial_yield(scenario.yp[i], scenario.axial[i], tension=False))
            else:
                scenario.ypadj.append(scenario.yp[i])


def tension(scenarios, casing):
    """
    Treal and Teff for all scenarios
    Updates the scenario object

    :param scenarios: scenarios list
    :type scenarios: list
    :param casing: casing details
    :type tubulars.Casing
    """

    for scenario in scenarios:
        for depth in scenario.md:
            treal = tubulars.tension_real(units.to_si(depth, 'ft'), casing, scenario.fluid_in, scenario.fluid_out)
            if scenario.name == 'OMW':
                treal += units.to_si(mop, 'lbf')
            teff = tubulars.tension_eff(treal, units.to_si(depth, 'ft'), casing, scenario.fluid_in, scenario.fluid_out)
            scenario.treal.append(units.from_si(treal, 'lbf')), scenario.teff.append(units.from_si(teff, 'lbf'))


def collapse(scenarios):
    """
    Design equation for collapse.
    Updates the scenario object

    :param scenarios: scenarios list
    :type scenarios: list
    :param safety_factor: SF for collapse
    :type safety_factor: float
    """
    for scenario in scenarios:
        # if scenario.scenario == 'Collapse':
            for i in range(len(scenario.md)):
                s = scenario.pout[i] - scenario.pin[i]
                if s < 0:
                    s = 0
                scenario.collapse.append(s)


def burst(scenarios):
    """
    Design equation for burst.
    Updates the scenario object

    :param scenarios: scenarios list
    :type scenarios: list
    :param safety_factor: SF for burst
    :type safety_factor: float
    """
    for scenario in scenarios:
        # if scenario.scenario == 'Burst':
            for i in range(len(scenario.md)):
                s = scenario.pin[i] - scenario.pout[i]
                if s < 0:
                    s = 0
                scenario.burst.append(s)


def pressure(scenarios):
    """
    Calculates pressure at every depth interval for all scenarios
    Updates the scenario object

    :param scenarios: scenarios list
    :type scenarios: list
    """
    for scenario in scenarios:
        for depth in scenario.md:
            pin, pout = fluids.pressure(units.to_si(depth, 'ft'), scenario.fluid_in, scenario.fluid_out)
            scenario.pin.append(units.from_si(pin, 'psi'))
            scenario.pout.append(units.from_si(pout, 'psi'))


def update_casing(casing, scenario):
    """
    Updates the casing to every interval.
    Updates the scenario object

    :param scenario: Scenario object
    :type scenario: Scenario
    :param casing: Casing object
    :type casing: tubulars.Casing
    """
    OD, ID, YP, Conn, Grade, WPF = list(), list(), list(), list(), list(), list()
    top = np.round(units.from_si(list(copy(casing.top)), 'ft'))

    casing_id = list()
    j = 1
    for i in range(len(scenario.md)):
        if j == len(casing.top):
            pass
        elif scenario.md[i] > top[j]:
            j += 1
        casing_id.append(j - 1)
        OD.append(np.round(units.from_si(casing.od[j - 1], 'in'), 1))
        ID.append(np.round(units.from_si(casing.id[j - 1], 'in'), 3))
        YP.append(np.round(units.from_si(casing.yp[j - 1], 'psi'), -3))
        WPF.append(np.round(units.from_si(casing.wpf[j - 1], 'lbm/ft'), 1))
        Grade.append(casing.grade[j - 1])
        Conn.append(casing.connection[j - 1])

    scenario.od = OD
    scenario.id = ID
    scenario.yp = YP
    scenario.conn = Conn
    scenario.wpf = WPF
    scenario.grade = Grade


def update_depth(casing, scenario):
    """
    Updates the depth at every 1 ft interval; at casing breaks, pressure calculated on each side (0.01 ft).
    Updates the scenario object

    :param scenario: Scenario object
    :type scenario: Scenario
    :param casing: Casing object
    :type casing: tubulars.Casing
    """

    md = list()
    top = list(copy(casing.top))
    top.pop(0)

    for i in range(total_depth + 1):
        md.append(i)
        try:
            top[0]
        except IndexError:
            pass
        else:
            if i == np.round(units.from_si(top[0], 'ft')):
                md.append(i + 0.01)
                top.pop(0)

    scenario.md = md


def get_scenarios(path=root+'/Data/Scenario'):
    """
    Initializes the failure scenarios

    :param path: Directory path to the scenarios
    :return:
    """
    scenario_list = list()
    r, d, f = os.walk(path + "/Burst")

    for scenario in r[1]:
        scenario_list.append(Scenario('Burst', path + '/Burst/' + scenario + '/'))
        scenario_list[-1].name = scenario

    r, d, f = os.walk(path + "/Collapse")
    for scenario in r[1]:
        scenario_list.append(Scenario('Collapse', path + '/Collapse/' + scenario + '/'))
        scenario_list[-1].name = scenario

    r, d, f = os.walk(path + "/Tensile")
    for scenario in r[1]:
        scenario_list.append(Scenario('Tensile', path + '/Tensile/' + scenario + '/'))
        scenario_list[-1].name = scenario
    return scenario_list


class Scenario:
    def __init__(self, scenario=None, path=None):
        self.path = path
        self.scenario = scenario
        self.name = None
        self.md = list()
        self.treal = list()
        self.teff = list()
        self.pin = list()
        self.pout = list()
        self.axial = list()
        self.radial = list()
        self.tangential = list()
        self.vonmises = list()
        self.od = list()
        self.id = list()
        self.yp = list()
        self.ypadj = list()
        self.conn = list()
        self.grade = list()
        self.wpf = list()
        self.strength_burst = list()
        self.strength_collapse = list()
        self.strength_collapse_biax = list()
        self.strength_tensile = list()
        self.strength_joint = list()
        self.fluid_in = None
        self.fluid_out = None
        self.burst = list()
        self.collapse = list()

        if self.path is not None:
            self.fluid_in = fluids.Fluids(self.scenario, True, self.path)
            self.fluid_out = fluids.Fluids(self.scenario, False, self.path)
