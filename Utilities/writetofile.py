from Utilities import mylogging
import numpy as np
import os

root_path = os.path.dirname(os.path.dirname(__file__))


def casing_spec(casing):
    file = root_path + '/Data/Casing/Casing.csv'
    header = ['TVD,North,East,TVD Std, North, Std, East Std, UpDown, RightLeft, ForwardBackward, '
              'UpDown Std, RightLeft Std, ForwardBackward Std\n'
              'ft,ft,ft,ft,ft,ft,ft,ft,ft,ft,ft,ft\n']


def survey_error(survey_error):
    """
    Writes the final survey error to file

    :param survey_error: SurveyError object
    """

    mylogging.runlog.info('Write: Writing the survey to .csv.')
    file = root_path + '/Results/Error/{0}_{1}.csv'.format(survey_error.name, survey_error.method)

    header = ['TVD,North,East,TVD Std, North, Std, East Std, UpDown, RightLeft, ForwardBackward, '
              'UpDown Std, RightLeft Std, ForwardBackward Std\n'
              'ft,ft,ft,ft,ft,ft,ft,ft,ft,ft,ft,ft\n']


def complete_survey(survey, rnd=False):
    """
    Writes complete survey to file
    :param survey: SurveyMethod object
    :param rnd: round to nearest 100th
    :type rnd: bool
    """

    mylogging.runlog.info('Write: Writing the survey to .csv.')
    file = root_path + '/Results/{0}_{1}.csv'.format(survey.name, survey.method)

    if survey.errN is not None:
        header = ['MD,Inc,Azi,TVD,North,East,Closure,Departure,Section,DLS,Build,Turn,Target,Error North,Error East,Error TVD\n',
                  'ft,dega,dega,ft,ft,ft,dega,ft,ft,dega/100ft,dega/100ft,dega/100ft,dega,ft,ft,ft\n']

        if rnd is True:
            md, inc, azi = np.round(survey.md, 2), np.round(survey.inc, 2), np.round(survey.azi, 2)
            tvd, ns, ew = np.round(survey.tvd, 2), np.round(survey.north, 2), np.round(survey.east, 2)
            closure, departure = np.round(survey.closure, 2), np.round(survey.departure, 2)
            section = np.round(survey.section, 2)
            dls, build, turn = np.round(survey.dls, 2), np.round(survey.build, 2), np.round(survey.turn, 2)
            errN, errE, errV = np.round(survey.errN, 2), np.round(survey.errE, 2), np.round(survey.errV, 2)
        else:
            md, inc, azi, tvd, ns, ew = survey.md, survey.inc, survey.azi, survey.tvd, survey.north, survey.east
            closure, departure, section = survey.closure, survey.departure, survey.section
            dls, build, turn = survey.dls, survey.build, survey.turn
            errN, errE, errV = survey.errN, survey.errE, survey.errV

        f = open(file, 'w')
        f.writelines(header)
        for i in range(len(survey.md)):
            line = [str(md[i]) + ',' + str(inc[i]) + ',' + str(azi[i]) + ',' + str(tvd[i]) + ','
                    + str(ns[i]) + ',' + str(ew[i]) + ',' + str(closure[i]) + ','
                    + str(departure[i]) + ',' + str(section[i]) + ',' + str(dls[i]) + ','
                    + str(build[i]) + ',' + str(turn[i]) + ',' + str(survey.target) + ','
                    + str(errN[i]) + ',' + str(errE[i]) + ',' + str(errV[i]) + '\n']
            f.writelines(line)
        f.close()
    else:
        header = ['MD,Inc,Azi,TVD,North,East,Closure,Departure,Section,DLS,Build,Turn,Target\n',
                  'ft,dega,dega,ft,ft,ft,dega,ft,ft,dega/100ft,dega/100ft,dega/100ft,dega\n']

        if rnd is True:
            md, inc, azi = np.round(survey.md, 2), np.round(survey.inc, 2), np.round(survey.azi, 2)
            tvd, ns, ew = np.round(survey.tvd, 2), np.round(survey.north, 2), np.round(survey.east, 2)
            closure, departure = np.round(survey.closure, 2), np.round(survey.departure, 2)
            section = np.round(survey.section, 2)
            dls, build, turn = np.round(survey.dls, 2), np.round(survey.build, 2), np.round(survey.turn, 2)
        else:
            md, inc, azi, tvd, ns, ew = survey.md, survey.inc, survey.azi, survey.tvd, survey.north, survey.east
            closure, departure, section = survey.closure, survey.departure, survey.section
            dls, build, turn = survey.dls, survey.build, survey.turn

        f = open(file, 'w')
        f.writelines(header)
        for i in range(len(survey.md)):
            line = [str(md[i]) + ',' + str(inc[i]) + ',' + str(azi[i]) + ',' + str(tvd[i]) + ','
                    + str(ns[i]) + ',' + str(ew[i]) + ',' + str(closure[i]) + ','
                    + str(departure[i]) + ',' + str(section[i]) + ',' + str(dls[i]) + ','
                    + str(build[i]) + ',' + str(turn[i]) + ',' + str(survey.target) + '\n']
            f.writelines(line)
        f.close()


def survey_measurements(md, inc, azi, file):
    """
    Writes the survey measurements to csv
    :param md: measured depth
    :type md: list
    :param inc: inclination
    :type inc: list
    :param azi: azimuth
    :type azi: list
    :param file: file path
    :type file: str
    """
    mylogging.runlog.info('Write: Writing the survey to .csv.')

    header = ['MD,Inc,Azi\n', 'ft,dega,dega\n']

    f = open(file, 'w')
    f.writelines(header)
    for i in range(len(md)):
        f.writelines([str(md[i]) + ',' + str(inc[i]) + ',' + str(azi[i]) + '\n'])
    f.close()
