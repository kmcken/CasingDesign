from Utilities import mylogging, unitconverter as units
from config import *
import sqlite3
import csv
import numpy as np
import os
import pandas as pd


def get_scenarios(path=root + '/Data/Scenario/'):
    scenario_paths, scenario_names = list(), list()

    for directory in os.walk(path):
        if directory[0] is not path:
            scenario_paths.append(directory[0])
            scenario_names.append(directory[0].split('/')[-1])
    return scenario_names, scenario_paths


def find(header, listoflists):
    for i, entries in enumerate(listoflists):
        try:
            j = entries.index(header)
        except ValueError:
            continue
        yield i, j


def fluid_data(name, inside=True, path=root + '/Data/Scenario/'):
    if inside is True:
        file_path = path + name + '/' + 'PressureInside.csv'
    else:
        file_path = path + name + '/' + 'PressureOutside.csv'


def gfunction(name='G7', path=root + '/Data/G-Function/'):
    mylogging.runlog.info('Read: {0} G-Function.'.format(name))
    file = path + name + '.csv'
    with open(file, 'r') as f:
        reader = csv.reader(f)
        lines = list(reader)
    lines.pop(0)

    mach, cd = list(), list()
    for line in lines:
        mach.append(float(line[0]))
        cd.append(float(line[1]))

    return np.array(mach), np.array(cd)


def get_inventory(connection=None, database=root + '/Data/CasingCatalog.db'):
    """
    Get all of the casing inventory

    :param database: database file path
    :type database: str
    :param connection: casing connection type
    :type connection:str
    :return: Casing inventory
    :rtype: pd.DataFrame
    """

    try:
        (cursor, conn) = open_database(database)
    except FileNotFoundError:
        raise FileNotFoundError
    except sqlite3.InterfaceError:
        raise FileNotFoundError

    if connection == 'STC':
        cursor.execute('SELECT * FROM Inventory WHERE Conn=?', ['STC'])
    elif connection == 'LTC':
        cursor.execute('SELECT * FROM Inventory WHERE Conn=?', ['LTC'])
    elif connection == 'BTC':
        cursor.execute('SELECT * FROM Inventory WHERE Conn=?', ['BTC'])
    else:
        cursor.execute('SELECT * FROM Inventory')


    try:
        inventory = cursor.fetchall()
    except IndexError:
        print('DATABASE: Coupling does not exist in API 5B.')
        close_database(cursor, conn)
        raise IndexError('DATABASE: Coupling does not exist in API 5B.')
    else:
        close_database(cursor, conn)

    df = pd.DataFrame(inventory, columns=['OD', 'WPF', 'Grade', 'Connection', 'ID', 'DriftID', 'Cost'])
    YP = list()
    for item in df.Grade:
        YP.append(units.to_si(float(item.split('-')[1]) * 1000, 'psi'))

    df.insert(3, 'YP', YP)
    df = df.sort_values(by=['Cost', 'WPF'])
    df.OD = units.to_si(df.OD, 'in')
    df.ID = units.to_si(df.ID, 'in')
    df.DriftID = units.to_si(df.DriftID, 'in')
    df.WPF = units.to_si(df.WPF, 'lbm/ft')
    df.Cost = units.from_si(df.Cost, 'ft')
    return df


def open_database(file=None):
    if file is None:
        mylogging.runlog.error('DATABASE: Missing file input.')
        raise FileNotFoundError('DATABASE: Missing file input.')

    mylogging.runlog.info('DATABASE: Opening {0} database.'.format(file))
    try:
        conn = sqlite3.connect(file)
    except sqlite3.InterfaceError:
        mylogging.runlog.error('DATABASE: Database interface error.')
        raise sqlite3.InterfaceError
    else:
        cursor = conn.cursor()
        mylogging.runlog.info('DATABASE: Database {0} opened.'.format(file))
        return cursor, conn


def close_database(cursor, conn):
    cursor.close()
    conn.close()
    mylogging.runlog.info('DATABASE: Database closed.')
