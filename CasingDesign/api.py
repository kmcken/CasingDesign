from Utilities import mylogging
from config import *
import sqlite3
import numpy as np
from copy import copy


def tensile_joint(od, id, wpf, grade, yp, connection):
    """
    Tensile strength rating for the casing joints

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param wpf: weight per foot (lbm/ft)
    :type wpf: float
    :param grade: rated yield strength (1000 psi)
    :type grade: float
    :param yp: rated yield strength (psi)
    :type yp: float
    :param connection: connection (STC, LTC, or BTC)
    :type connection: str
    :return: tensile strength (psi)
    :rtype: float
    """

    coupling = get_5B_data(od, wpf, grade, connection)
    Up = ultimate_strength(grade, L=False)
    P_jf = tension_fracture(od, id, Up, coupling)
    P_jp = tension_pullout(od, id, yp, Up, coupling)

    return min([P_jf, P_jp])


def tensile_body(od, id, yp):
    """
    Tensile strength rating of the pipe body

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param yp: yield point (psi)
    :type yp: float
    :return: P_collapse (psi)
    :rtype: float
    """
    return np.pi / 4 * yp * (od ** 2 - id ** 2)


def tension_pullout(od, id, yp, up, coupling):
    """
    Tensile strength rating for pullout failure of the joint

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param yp: yield strength (psi)
    :type yp: float
    :param up: minimum ultimate strength of the pipe (psi)
    :type up: float
    :param coupling: coupling
    :type coupling: API5B
    :return: joint fracture strength (psi)
    :rtype: float
    """
    if coupling.type != 'BTC':
        Ajp = area_last_thread(od, id)
        L = coupling.L4 - coupling.M
        return 0.95 * Ajp * L * ((0.74 * np.power(od, -0.59) * up) / (0.5 * L + 0.14 * od) + yp / (L + 0.14 * od))

    A = np.pi / 4 * (od ** 2 - id ** 2)
    return 0.95 * A * up * (1.008 - 0.0396 * (1.083 - yp / up) * od)


def tension_fracture(od, id, up, coupling):
    """
    Tensile strength rating for fracture failure of the joint

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param up: minimum ultimate strength of the pipe (psi)
    :type up: float
    :param coupling: coupling
    :type coupling: API5B
    :return: joint fracture strength (psi)
    :rtype: float
    """

    if coupling.type == 'BTC':
        A = np.pi / 4 * (coupling.W ** 2 - diameter_root(coupling) ** 2)
    else:
        A = area_last_thread(od, id)
    return 0.95 * A * up


def ultimate_strength(grade, L=False):
    """
    Ultimate tensile strength from Baker TechFact

    :param grade: pipe grade (1000 psi)
    :type grade: int
    :param L: Grade L-80
    :type L: bool
    :return: ultimate strength (psi)
    :rtype: float
    """
    if L is True:
        return 95000
    if grade == 75:
        return 95000
    if grade == 80:
        return 100000
    if grade == 95:
        return 105000
    return 125000


def area_last_thread(od, id):
    """
    Cross-sectional area of the pipe wall under the last perfect thread, Ajp

    :param od: pipe outer diameter (in)
    :type od: float
    :param id: pipe inner diameter (in)
    :type id: float
    :return: Ajp (in2)
    :rtype: float
    """

    return np.pi / 4 * ((od - 0.1425) ** 2 - id ** 2)


def burst(od, id, weight, grade, yp, coupling_type='LTC', leak=False):
    """
    Burst rating of the casing

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param weight: weight per foot (lbf.ft)
    :type: weight: float
    :param grade: rated yield point (1000 psi)
    :type grade: int
    :param yp: yield point (psi)
    :type yp: int
    :param coupling_type: coupling type (STC, BTC, or LTC)
    :type coupling_type: str
    :param leak: include leak resistance
    :type leak: bool
    :return: P_collapse (psi)
    :rtype: float
    """

    coupling = get_5B_data(od, weight, grade, coupling_type)
    P_b = burst_body(od, id, yp)
    P_c = burst_coupling(coupling)
    if leak is True:
        P_lr = burst_leak(coupling, modulus=30e6)
        return min([P_b, P_c, P_lr])
    return min([P_b, P_c])


def burst_body(od, id, yp):
    """
    Burst rating of the pipe body

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param yp: yield point (psi)
    :type yp: float
    :return: P_collapse (psi)
    :rtype: float
    """
    t = (od - id) / 2
    return 0.875 * 2 * yp * t / (od)


def burst_leak(coupling, modulus=30e6):
    """
    Leak resistance rating of the casing.

    :param coupling: API5B coupling data
    :type coupling: API5B
    :param modulus: Young's Modulus (30e6 psi)
    :type modulus: float
    :return: coupling leak resistance rating
    :rtype: float
    """

    return modulus * coupling.T * coupling.A * (coupling.W ** 2 - coupling.E1 ** 2) / \
           (2 * coupling.tpi * coupling.E1 * coupling.W ** 2)


def burst_coupling(coupling):
    """
    Burst rating of the coupling

    :param coupling: API5B coupling data
    :type coupling: API5B
    :return: coupling burst rating
    :rtype: float
    """

    d1 = diameter_root(coupling)
    return coupling.yp * (coupling.W - d1) / coupling.W


def diameter_root(coupling):
    """
    Diameter of the root of the coupling thread at the end of the pipe in the power-tight position for STC and LTC.

    :param coupling: coupling class data
    :type coupling: API5B
    :return: Diameter of the root of the coupling thread, d1 (in)
    :rtype: float
    """

    if coupling.type is 'BTC':
        return coupling.E7 - (coupling.L7 + coupling.I) * coupling.T + 0.062
    return coupling.E1 - (coupling.L1 + coupling.A/coupling.tpi) * coupling.T + coupling.H - 2 * coupling.Srn


def collapse(od, id, yp):
    """
    Collapse strength

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param yp: yield point (psi)
    :type yp: float
    :return: P_collapse (psi)
    :rtype: float
    """
    t = (od - id) / 2
    Dt = od / t

    p_ypc = collapse_minimum(od, id, yp)
    p_pc = collapse_plastic(od, id, yp)
    p_tc = collapse_transition(od, id, yp)
    p_ec = collapse_elastic(od, id)

    A = A_5C3_calc(yp)
    B = B_5C3_calc(yp)
    C = C_5C3_calc(yp)
    F = F_5C3_calc(yp)
    G = G_5C3_calc(yp)

    ratio_plastic = (np.sqrt((A - 2) ** 2 + 8 * (B + C / yp)) + A - 2) / (2 * (B + C / yp))
    ratio_transition = yp * (A - F) / (C + yp * (B - G))
    ratio_elastic = (2 + B / A) / (3 * B / A)

    if Dt <= ratio_plastic:
        return p_ypc
    if Dt <= ratio_transition:
        return p_pc
    if Dt <= ratio_elastic:
        return p_tc
    return p_ec


def collapse_minimum(od, id, yp):
    """
    Collapse pressure that generates minimum yield stress

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param yp: yield point (psi)
    :type yp: float
    :return: P_yp (psi)
    :rtype: float
    """

    t = (od - id) / 2
    Dt = od / t
    return 2 * yp * ((Dt - 1) / Dt ** 2)


def collapse_plastic(od, id, yp):
    """
    The minimum collapse pressure for plastic failure.

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param yp: yield point (psi)
    :type yp: float
    :return: P_yp (psi)
    :rtype: float
    """

    A = A_5C3_calc(yp)
    B = B_5C3_calc(yp)
    C = C_5C3_calc(yp)
    t = (od - id) / 2
    Dt = od / t

    return yp * (A / Dt - B) - C


def collapse_transition(od, id, yp):
    """
    The minimum collapse pressure for the transition between plastic and elastic failure.

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :param yp: yield point (psi)
    :type yp: float
    :return: P_yp (psi)
    :rtype: float
    """
    F = F_5C3_calc(yp)
    G = G_5C3_calc(yp)
    t = (od - id) / 2
    Dt = od / t

    return yp * (F / Dt - G)


def collapse_elastic(od, id):
    """
    The minimum collapse pressure for elastic failure.

    :param od: outer diameter (in)
    :type od: float
    :param id: inner diameter (in)
    :type id: float
    :return: P_yp (psi)
    :rtype: float
    """
    t = (od - id) / 2
    Dt = od / t

    return 46950000 / (Dt * (Dt - 1) ** 2)


def A_5C3_calc(yp):
    """
    Calculated A value from API 5C3

    :param yp: yield point (psi)
    :type yp: float
    :return: A
    """

    return 2.8762 + 0.10679e-5 * yp + 0.21301e-10 * yp ** 2 - 0.53132e-16 * yp ** 3


def B_5C3_calc(yp):
    """
    Calculated B value from API 5C3

    :param yp: yield point (psi)
    :type yp: float
    :return: B
    """

    return 0.026233 + 0.50609e-6 * yp


def C_5C3_calc(yp):
    """
    Calculated C value from API 5C3

    :param yp: yield point (psi)
    :type yp: float
    :return: C
    """

    return - 465.93 + 0.030867 * yp - 0.10483e-7 * yp ** 2 + 0.36989e-13 * yp ** 3


def F_5C3_calc(yp):
    """
    Calculated F value from API 5C3

    :param yp: yield point (psi)
    :type yp: float
    :return: f
    """

    A = A_5C3_calc(yp)
    B = B_5C3_calc(yp)
    X = B / A
    num = 46.95e6 * (3 * X / (2 + X)) ** 3
    den = yp * (3 * X / (2 + X) - X) * (1 - 3 * X / (2 + X)) ** 2

    return num / den


def G_5C3_calc(yp):
    """
    Calculated G value from API 5C3

    :param yp: yield point (psi)
    :type yp: float
    :return: G
    """

    A = A_5C3_calc(yp)
    B = B_5C3_calc(yp)
    X = B / A
    F = F_5C3_calc(yp)

    return F * X


class API5B:
    def __init__(self):
        self.type = None  # STC, LTC, or BTC
        self.round = None  # round is True; buttress is False
        self.D = None  # Size Outer Diameter
        self.D4 = None  # Major Diameter
        self.W = None  # Coupling OD
        self.wpf = None  # Preferred WPF, if any
        self.grade = None  # Minimum grade, if any
        self.yp = None  # Yield Point
        self.tpi = 8  # No of threads per inch
        self.L1 = None  # End of Pipe to Hand-Tight Plane Length
        self.L2 = None  # Effective Threads Length
        self.L4 = None  # End of Pipe to Vanish Point Length
        self.L7 = None  # Perfect Threads Length
        self.g = None  # Imperfect Threads Length
        self.E1 = None  # Pitch Diameter at Hand-Tight Plane
        self.E7 = None  # Pitch Diameter
        self.Ef = None  # Faces of Coupling to Plane Length
        self.J = None  # End of Pipe to Center of Coupling, Power-Tight Make-Up
        self.Jn = None  # Enf of Pipe to Center of Coupling, Hand-Tight Make-Up
        self.M = None  # Face of Coupling to Hand-Tight Plane Length
        self.Q = None  # Diameter of Coupling Recess
        self.q = None  # Depth of Coupling Recess
        self.A = None  # Hand-Tight Standoff no. of Thread Turns
        self.A1 = None  # End of Pipe to Triangle Stamp
        self.Lc = None  # Full Crest Threads from Enf of Pipe Minimum Length
        self.H = None  # Thread height
        self.Ibtc = None
        self.T = 0.0625  # Taper in/in
        self.Srn = None
        self.MakeUp = 1.0  # Make-up loss of length


def get_5B_data(od, weight, grade, coupling_type, database=root + '/Data/APIspecifications.db'):
    """
    Gets API 5B specification data for casing couplings.

    :param od: outer diameter, OD (in)
    :type od: float
    :param weight: weight per foot, WPF (lbf/ft)
    :type weight: float
    :param grade: pipe grade yield point
    :type grade: int
    :param coupling_type: coupling type STC, LTC, or BTC
    :type coupling_type: str
    :param database: database file path
    :type database: str
    :return: 5C3 class object for the grade
    :rtype: API5B
    """

    data = API5B()
    data.D = od
    data.wpf = weight
    data.type = coupling_type
    data.grade = grade
    data.yp = float(grade.split('-')[1]) * 1000

    try:
        (cursor, conn) = open_database(database)
    except FileNotFoundError:
        raise FileNotFoundError
    except sqlite3.InterfaceError:
        raise FileNotFoundError

    if data.type == 'STC':
        cursor.execute('SELECT D4, WPF, YP, TPI, H, L1, L2, L4, E1, J, M, Q, qdepth, A, Lc, Srn, W, MLR3 FROM STC WHERE D=?', [data.D])
    elif data.type == 'BTC':
        cursor.execute('SELECT D4, TPI, g, L7, L4, E7, J, Jn, Ef, A1, A, Q, Lc, I, T, W, MLR3 FROM BTC WHERE D=?', [data.D])
    else:
        cursor.execute('SELECT D4, YP, TPI, H, L1, L2, L4, E1, J, M, Q, qdepth, A, Lc, Srn, W, MLR3 FROM LTC WHERE D=?', [data.D])

    try:
        constants = cursor.fetchall()
    except IndexError:
        print('DATABASE: Coupling does not exist in API 5B.')
        close_database(cursor, conn)
        raise IndexError('DATABASE: Coupling does not exist in API 5B.')

    close_database(cursor, conn)

    if data.type == 'STC':
        yp_check = False
        if len(constants) is not 1:
            yp_check = False
            for i in range(len(constants)):
                if constants[i][1] == np.round(weight, 2):
                    constants = constants[i]
                    break
                else:
                    yp_check = True
        else:
            constants = constants[0]

        if yp_check is True:
            j = None
            pop_j = False
            for i in range(len(constants)):
                if constants[i][1] is not None:
                    j = copy(i)
                    pop_j = True
            if pop_j is True:
                constants.pop(j)

            if constants[0][2] is None:
                if grade >= constants[1][2]:
                    constants = constants[1]
                else:
                    constants = constants[0]
            elif grade >= constants[0][2]:
                constants = constants[0]
            else:
                constants = constants[1]

        data.D4 = float(constants[0])
        try:
            data.wpf = float(constants[1])
        except TypeError:
            pass
        try:
            data.yp = int(constants[2])
        except TypeError:
            pass
        try:
            data.tpi = int(constants[3])
        except TypeError:
            pass
        data.H = float(constants[4])
        data.L1 = float(constants[5])
        data.L2 = float(constants[6])
        data.L4 = float(constants[7])
        data.E1 = float(constants[8])
        data.J = float(constants[9])
        data.M = float(constants[10])
        data.Q = float(constants[11])
        data.q = float(constants[12])
        data.A = float(constants[13])
        data.Lc = float(constants[14])
        data.Srn = float(constants[15])
        data.W = float(constants[16])
        data.MakeUp = float(constants[17])

    if data.type == 'LTC':
        if len(constants) is not 1:
            if constants[0][1] is None:
                if grade >= constants[1][1]:
                    constants = constants[1]
                else:
                    constants = constants[0]
            elif grade >= constants[0][1]:
                constants = constants[0]
            else:
                constants = constants[1]
        else:
            constants = constants[0]

        data.D4 = float(constants[0])
        try:
            data.yp = int(constants[1])
        except TypeError:
            pass
        try:
            data.tpi = int(constants[2])
        except TypeError:
            pass
        data.H = float(constants[3])
        data.L1 = float(constants[4])
        data.L2 = float(constants[5])
        data.L4 = float(constants[6])
        data.E1 = float(constants[7])
        data.J = float(constants[8])
        data.M = float(constants[9])
        data.Q = float(constants[10])
        data.q = float(constants[11])
        data.A = float(constants[12])
        data.Lc = float(constants[13])
        data.Srn = float(constants[14])
        data.W = float(constants[15])
        data.MakeUp = float(constants[16])

    if data.type == 'BTC':
        data.D4 = float(constants[0][0])
        data.tpi = int(constants[0][1])
        data.g = float(constants[0][2])
        data.L7 = float(constants[0][3])
        data.L4 = float(constants[0][4])
        data.E7 = float(constants[0][5])
        data.J = float(constants[0][6])
        data.Jn = float(constants[0][7])
        data.Ef = float(constants[0][8])
        data.A1 = float(constants[0][9])
        data.A = float(constants[0][10])
        data.Q = float(constants[0][11])
        data.Lc = float(constants[0][12])
        data.I = float(constants[0][13])
        data.T = float(constants[0][14])
        data.W = float(constants[0][15])
        data.MakeUp = float(constants[0][16])

    return data


class API5C3:
    def __init__(self):
        self.grade = None
        self.A = None
        self.B = None
        self.C = None
        self.F = None
        self.G = None
        self.DtLow = None
        self.DtPlastic = None
        self.DtElastic = None


def get_5C3_data(grade, database=root + '/Data/APIspecifications.db'):
    """
    Gets API 5C3 specification data

    :param grade: pipe grade
    :type grade: str
    :param database: database file path
    :type database: str
    :return: 5C3 class object for the grade
    :rtype: API5C3
    """

    try:
        (cursor, conn) = open_database(database)
    except FileNotFoundError:
        raise FileNotFoundError
    except sqlite3.InterfaceError:
        raise FileNotFoundError

    cursor.execute('SELECT A, B, C, F, G, DtLow, DtPlastic, DtElastic FROM API5C3 WHERE Grade=?', [grade])

    try:
        constants = cursor.fetchall()[0]
    except IndexError:
        print('DATABASE: {0} grade does not exist in API 5C3.'.format(grade))
        raise IndexError('DATABASE: {0} grade does not exist in API 5C3.'.format(grade))

    close_database(cursor, conn)

    data = API5C3()
    data.grade = grade
    data.A, data.B, data.C, data.F, data.G = constants[0], constants[1], constants[2], constants[3], constants[4]
    data.DtLow, data.DtPlastic, data.DtElastic = constants[5], constants[6], constants[7]
    return data


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

