import matplotlib.pyplot as plt
import numpy as np
from math import ceil
from config import *


def collapse(scenarios, master):
    """
    Plots the minimum burst design strength  for each scenario.

    :param scenarios: scenarios list
    :type scenarios: list
    :param master: master scenario
    :type master: algorithm.Scenario
    """

    plt.figure()
    ax = plt.gca()
    xmax = list()
    for scenario in scenarios:
        if scenario.scenario == 'Collapse':
            plt.plot(scenario.collapse, scenario.md, label='{0}'.format(scenario.name))
            xmax.append(np.max(scenario.collapse))

    plt.plot(np.array(master.collapse) * SF_collapse, master.md, label='Collapse SF')
    plt.plot(master.strength_collapse, master.md, 'k--', label='Uniaxial Collapse Strength')
    plt.plot(master.strength_collapse_biax, master.md, 'k-.', label='Biaxial Collapse Strength')
    xmax.append(np.max(master.strength_collapse))
    xmax.append(np.max(master.strength_collapse_biax))
    xmax.append(np.max(np.array(master.collapse) * SF_collapse))

    plt.legend()
    plt.xlabel('Minimum Collapse Strength (psi)')
    plt.ylabel('Vertical Depth, TVD (ft)')
    plt.xlim([0, ceil(np.max(xmax) * SF_collapse / 1000) * 1000])
    ax.invert_yaxis()
    plt.grid()


def burst(scenarios, master):
    """
    Plots the minimum burst design strength  for each scenario.

    :param scenarios: scenarios list
    :type scenarios: list
    :param master: master scenario
    :type master: algorithm.Scenario
    """

    plt.figure()
    ax = plt.gca()
    xmax = list()
    for scenario in scenarios:
        if scenario.scenario == 'Burst':
            plt.plot(scenario.burst, scenario.md, label='{0}'.format(scenario.name))
            xmax.append(np.max(scenario.burst))

    plt.plot(np.array(master.burst) * SF_burst, master.md, label='Burst SF')
    plt.plot(master.strength_burst, master.md, 'k--', label='Burst Strength')
    xmax.append(np.max(np.array(master.burst) * SF_burst))
    xmax.append(np.max(master.strength_burst))

    plt.legend()
    plt.xlabel('Minimum Burst Strength (psi)')
    plt.ylabel('Vertical Depth, TVD (ft)')
    plt.xlim([0, ceil(np.max(xmax) * SF_burst / 1000) * 1000])
    ax.invert_yaxis()
    plt.grid()


def tension(scenarios, master, body=True):
    """
    Plots the real and effective tension for all scenarios.

    :param scenarios: scenarios list
    :type scenarios: list
    :param master: master scenario
    :type master: algorithm.Scenario
    """

    plt.figure()
    ax = plt.gca()
    for scenario in scenarios:
        if scenario.scenario == 'Tensile':
            if body is True:
                plt.plot(np.array(scenario.treal) * SF_tensile, scenario.md, label='Treal: {0}'.format(scenario.name))
                plt.plot(np.array(scenario.teff) * SF_tensile, scenario.md, label='Teff: {0}'.format(scenario.name))
            else:
                plt.plot(np.array(scenario.treal) * SF_joint, scenario.md, label='Treal: {0}'.format(scenario.name))
                plt.plot(np.array(scenario.teff) * SF_joint, scenario.md, label='Teff: {0}'.format(scenario.name))

    if body is True:
        plt.plot(master.strength_tensile, master.md, 'k--', label='Pipe Body Strength')
        plt.xlabel('Minimum Pipe Body Strength (lbf)')
    else:
        plt.plot(master.strength_joint, master.md, 'k--', label='Joint Strength')
        plt.xlabel('Minimum Joint Strength (lbf)')

    plt.legend()
    plt.ylabel('Vertical Depth, TVD (ft)')
    ax.invert_yaxis()
    plt.grid()


def stress(scenarios):
    plt.figure()
    ax = plt.gca()

    for scenario in scenarios:
        plt.plot(scenario.vonmises, scenario.md, label='{0} {1}'.format(scenario.scenario, scenario.name))

    plt.plot(scenarios[0].yp, scenario.md, 'k--', label='YP')
    plt.legend()
    plt.xlabel('Von Mises Stress (psi)')
    plt.ylabel('Vertical Depth, TVD (ft)')
    ax.invert_yaxis()
    plt.grid()


def show():
    plt.show()
