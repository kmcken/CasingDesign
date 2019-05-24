from Utilities import unitconverter as units, readfromfile as read, mylogging
import csv
from config import *


def pressure(depth, inside, outside):
    """
    Pressure both inside and outside of the casing for a given depth

    :param depth: depth of interest (m)
    :type depth: float
    :param inside: fluid column profile inside the casing
    :type inside: Fluids
    :param outside: fluid column profile outside the casing
    :type outside: Fluids
    :return: pressure at depth (Pa)
    :rtype: float
    """

    return pressure_single(depth, inside), pressure_single(depth, outside)


def pressure_single(depth, fluid_column):
    """
    Pressure at a given depth for fluid column

    :param depth: depth of interest (m)
    :type depth: float
    :param fluid_column: fluid column profile
    :type fluid_column: Fluids
    :return: pressure at depth (Pa)
    :rtype: float
    """

    if depth > units.to_si(total_depth, depth_unit):
        mylogging.alglog.info('Fluids: Depth is greater than TD.')
        print('Fluids: Depth is greater than TD.')

    pressure = fluid_column.surface_pressure
    i = 0
    try:
        bottom = fluid_column.top[i + 1]
    except IndexError:
        bottom = units.to_si(total_depth, 'ft')

    while bottom < depth:
        pressure += (bottom - fluid_column.top[i]) * fluid_column.density[i] * units.to_si(1, 'gn')
        i += 1
        try:
            bottom = fluid_column.top[i + 1]
        except IndexError:
            bottom = units.to_si(total_depth, depth_unit)

    pressure += (depth - fluid_column.top[i]) * fluid_column.density[i] * units.to_si(1, 'gn')
    return pressure


def hydrostatic(head, density):
    """
    Hydrostatic pressure

    :param head: vertical length (m)
    :type head: float
    :param density: fluid density (kg/m3)
    :type density: float
    :return: hydrostatic pressure (Pa)
    :rtype: float
    """
    return head * density * units.to_si(1, 'gn')


class Fluids:
    """Converts all inputs to SI units."""
    def __init__(self, scenario, inside=True, path=root + '/Data/Scenario/'):
        self.scenario = scenario
        self.inside = inside
        self.file = None
        self.top = None
        self.density = None
        self.closed = None
        self.surface_pressure = None
        self.downhole_pressure = None

        if scenario is not None:
            try:
                self.get_fluid_data(path)
            except KeyError:
                pass
            else:
                mylogging.runlog.info('Fluids: Populate Fluids object with tubular inside fluid data.')

    def get_fluid_data(self, path):
        if isinstance(self.inside, bool) is False:
            mylogging.runlog.info('Read: KeyError - Inside/Outside not specified for {0} scenario.'
                                  .format(self.scenario))
            print('Error: KeyError - Inside/Outside not specified for {0} scenario.'.format(self.scenario))
            raise KeyError

        if self.inside is True:
            mylogging.runlog.info('Read: {0} fluid data for {1} scenario.'.format('inside', self.scenario))
        else:
            mylogging.runlog.info('Read: {0} fluid data for {1} scenario.'.format('inside', self.scenario))

        if self.inside is True:
            self.file = path + 'PressureInside.csv'
        else:
            self.file = path + 'PressureOutside.csv'

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
                values.append(float(lines[i][index[1]]))
            return values, lines[index[0] + 1][index[1]]

        try:
            index = entry_index('Surface Pressure', lines)
        except IndexError:
            mylogging.runlog.info('Read: Missing {0} for {1} scenario, assumed 0.'
                                  .format('Surface Pressure', self.scenario))
            print('Read: Missing {0} for {1} scenario, assumed 0.'.format('Surface Pressure', self.scenario))
            self.surface_pressure = 0
        else:
            try:
                self.surface_pressure = units.to_si(float(lines[index][1]), lines[index][2])
            except:
                print("Error: read 'Surface Pressure' in {0}".format(self.file))

        try:
            index = entry_index('Closed', lines)
        except IndexError:
            mylogging.runlog.info('Read: Missing {0} for {1} scenario, assumed 0.'.format('Closed', self.scenario))
            print('Read: Missing {0} for {1} scenario, assumed 0.'.format('Closed', self.scenario))
            self.closed = True
        else:
            try:
                self.closed = bool(lines[index][1])
            except:
                print("Error: read 'Closed' in {0}".format(self.file))

        try:
            index = entry_index('Top (TVD)', lines, column=True)
        except IndexError:
            mylogging.runlog.info('Read: Missing {0}.'.format('fluid top data'))
            print('Read: Missing {0} for {1}.'.format('fluid top data'))
            self.closed = True
        else:
            values, unit = depth_entry(index)
            values = units.to_si(values, unit)
            self.top = tuple(values)

        try:
            index = entry_index('Density', lines, column=True)
        except IndexError:
            mylogging.runlog.info('Read: Missing {0} for {1} scenario, assumed 0.'.format('fluid top data', self.scenario))
            print('Read: Missing {0} for {1} scenario, assumed 0.'.format('fluid top data', self.scenario))
            self.closed = True
        else:
            values, unit = depth_entry(index)
            if unit == 'psi/ft':
                values = units.to_si(values, 'psi/ft') / units.to_si(1, 'gn')
            else:
                values = units.to_si(values, unit)
            self.density = tuple(values)
