from Utilities import mylogging, unitconverter as units, readfromfile as read
from CasingDesign import fluids, tubulars, plot, api, stress, algorithm
from config import *
from copy import copy


def __init__():
    mylogging.runlog.info("START: Now, lets get this thing on the hump. We got some flyin' to do.")
    print("Now, lets get this thing on the hump. We got some flyin' to do.")

    inventory = read.get_inventory('STC')
    if inventory.count(0).OD == 0:
        conn = 1
        inventory = read.get_inventory('LTC')

    init_casing = tubulars.Casing()
    # init_casing.top = list([0])
    # init_casing.od = list([inventory.OD[0]])
    # init_casing.id = list([inventory.ID[0]])
    # init_casing.wpf = list([inventory.WPF[0]])
    # init_casing.yp = list([inventory.YP[0]])
    # init_casing.grade = list([inventory.Grade[0]])
    # init_casing.connection = list([inventory.Connection[0]])
    # init_casing.cost = list([inventory.Cost[0]])

    scenarios = algorithm.get_scenarios()

    return inventory, init_casing, scenarios


if __name__ == '__main__':
    inventory, casing, scenarios = __init__()
    for scenario in scenarios:
        algorithm.update_depth(casing, scenario)
        algorithm.update_casing(casing, scenario)

    print('Inside and Outside Pressure')
    algorithm.pressure(scenarios)

    print('Real and Effective Tension')
    algorithm.tension(scenarios, casing)

    print('Design Eqn')
    algorithm.burst(scenarios)
    algorithm.collapse(scenarios)

    print('Stress State')
    algorithm.stress_state(scenarios)
    algorithm.yield_pt_adjust(scenarios)

    print('Master Scenario')
    master = algorithm.Scenario()
    algorithm.master_scenario(master, scenarios)

    print('Casing Strength')
    algorithm.casing_strength(master)

    print('Plots')
    plot.burst(scenarios, master)
    plot.collapse(scenarios, master)
    plot.tension(scenarios, master, body=True)
    plot.tension(scenarios, master, body=False)
    plot.stress(scenarios)
    plot.show()

    print("We'll meet again.")
    mylogging.runlog.info("End: We'll meet again.")
