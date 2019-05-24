from Utilities import unitconverter as units, readfromfile as read, mylogging
from CasingDesign import fluids
import csv
from config import *
import numpy as np


def tension_eff(t_real, depth, casing, inside, outside):
    """
    Effective tension at depth

    :param t_real: T_real (N)
    :type t_real: float
    :param depth: depth of interest (m)
    :type depth: float
    :param casing: casing string specifications object
    :type casing: Casing
    :param inside: fluids column object
    :type inside: fluids.Fluid
    :param outside: fluids column object
    :type outside: fluids.Fluid
    :return: T_eff (N)
    :rtype: float
    """

    i = 0
    od, id = casing.od[0], casing.id[0]
    while depth - casing.top[i] >= 0:
        od, id = casing.od[i], casing.id[i]
        i += 1
        try:
            casing.top[i]
        except IndexError:
            break

    area_out, area_in = area(od), area(id)
    p_in, p_out = fluids.pressure(depth, inside, outside)
    return t_real + p_out * area_out - p_in * area_in


def tension_real(depth, casing, inside, outside):
    """
    Real tension at depth

    :param depth: depth of interest (m)
    :type depth: float
    :param casing: casing string specifications object
    :type casing: Casing
    :param inside: fluids column object
    :type inside: fluids.Fluid
    :param outside: fluids column object
    :type outside: fluids.Fluid
    :return: T_real (N)
    :rtype: float
    """

    if depth > units.to_si(total_depth, depth_unit):
        mylogging.alglog.info('Tubulars: Depth is greater than TD.')
        raise ValueError('Tubulars: Depth is greater than TD.')

    if depth < 0:
        mylogging.alglog.info('Tubulars: Depth is less than 0.')
        raise ValueError('Tubulars: Depth is greater than TD.')

    td = units.to_si(total_depth, depth_unit)
    t_real = - units.to_si(slack_off, weight_unit) \
             + fluids.pressure_single(td, inside) * area(casing.id[-1]) \
             - fluids.pressure_single(td, outside) * area(casing.od[-1])

    if depth >= casing.top[-1]:
        t_real += (td - depth) * casing.wpf[-1] * units.to_si(1, 'gn')
        return t_real

    t_real += (td - casing.top[-1]) * casing.wpf[-1] * units.to_si(1, 'gn')

    i = 1
    while True:
        t_real += fluids.pressure_single(casing.top[::-1][i - 1], inside) * (area(casing.id[::-1][i]) - area(casing.id[::-1][i - 1])) \
                  - fluids.pressure_single(casing.top[::-1][i - 1], outside) * (area(casing.od[::-1][i]) - area(casing.od[::-1][i - 1]))
        if casing.top[::-1][i - 1] > depth >= casing.top[::-1][i]:
            t_real += (casing.top[::-1][i - 1] - depth) * casing.wpf[::-1][i] * units.to_si(1, 'gn')
            return t_real
        else:
            t_real += (casing.top[::-1][i - 1] - casing.top[::-1][i]) * casing.wpf[::-1][i] * units.to_si(1, 'gn')
            i += 1


def area(diameter):
    """
    Calculates area of a circle
    :param diameter: diameter (m)
    :type diameter: float
    :return: area (m2)
    :rtype: float
    """
    return np.pi / 4 * diameter ** 2


class Casing:
    def __init__(self, defined=True, path=root + '/Data/Casing/Casing.csv'):
        self.defined = defined
        self.file = path
        self.od = None
        self.id = None
        self.top = None
        self.wpf = None
        self.yp = None
        self.grade = None
        self.connection = None
        self.cost = None

        if defined is True:
            try:
                self.get_casing_data(self.file)
            except KeyError:
                pass
            else:
                mylogging.runlog.info('Casing: Populate Casing object from file.')

    def get_casing_data(self, file):
        with open(self.file, 'r') as f:
            reader = csv.reader(f)
            lines = list(reader)

        def entry_index(entry, file_lines, column=False):
            entry_matches = list()
            matches = read.find(entry, file_lines)
            [entry_matches.append(match) for match in matches]
            if column is False:
                return entry_matches.pop(0)[0]
            else:
                return entry_matches.pop(0)

        def depth_entry(index):
            values = list()
            for i in range(index[0] + 2, len(lines)):
                try:
                    values.append(float(lines[i][index[1]]))
                except ValueError:
                    values.append(lines[i][index[1]])
            return values, lines[index[0] + 1][index[1]]

        try:
            index = entry_index('Top', lines, column=True)
        except IndexError:
            mylogging.runlog.info('Read: Missing {0}.'.format('fluid top data'))
            print('Read: Missing {0}.'.format('fluid top data'))
            self.closed = True
        else:
            values, unit = depth_entry(index)
            values = units.to_si(values, unit)
            self.top = values

        try:
            index = entry_index('OD', lines, column=True)
        except IndexError:
            mylogging.runlog.exception('Read: Missing {0}, assumed {1} {2}.'.format('OD data', hole_size, diameter_unit))
            print('Read: Missing {0}, assumed {1} {2}.'.format('OD data', hole_size, diameter_unit))
            self.od = list()
            [self.od.append(units.to_si(hole_size, diameter_unit)) for i in range(len(self.top))]
        else:
            values, unit = depth_entry(index)
            values = units.to_si(values, unit)
            self.od = values

        try:
            index = entry_index('ID', lines, column=True)
        except IndexError:
            mylogging.runlog.exception('Read: Missing {0}.'.format('ID data'))
            print('Read: Missing {0}.'.format('ID data'))
        else:
            values, unit = depth_entry(index)
            values = units.to_si(values, unit)
            self.id = values

        try:
            index = entry_index('WPF', lines, column=True)
        except IndexError:
            mylogging.runlog.error('Read: Missing {0}.'.format('weight per foot data'))
            print('Read: Missing {0}.'.format('weight per foot data'))
            raise KeyError('Read: Missing {0}.'.format('weight per foot data'))
        else:
            values, unit = depth_entry(index)
            values = units.to_si(values, unit)
            self.wpf = values

        try:
            index = entry_index('Grade', lines, column=True)
        except IndexError:
            mylogging.runlog.error('Read: Missing {0}.'.format('yield point data'))
            print('Read: Missing {0}.'.format('yield point data'))
            raise KeyError('Read: Missing {0}.'.format('yield point data'))
        else:
            values, unit = depth_entry(index)
            self.grade = tuple(values)
            yp = list()
            for grade in values:
                yp.append(units.to_si(float(grade.split('-')[1]) * 1000, unit))
            self.yp = yp

        try:
            index = entry_index('Connection', lines, column=True)
        except IndexError:
            mylogging.runlog.error('Read: Missing {0}.'.format('connection data'))
            print('Read: Missing {0}.'.format('connection data'))
            raise KeyError('Read: Missing {0}.'.format('connection data'))
        else:
            values, unit = depth_entry(index)
            self.connection = values
