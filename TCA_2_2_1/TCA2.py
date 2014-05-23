#standard
import sys
import time

import pandas as pd

#TCA
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCADataStore import DataStorage
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
from TCAOutput import TCA_Output
from TCACore import Timer, logger
from TCARegions import Load_Regions


#Check for control file
if len(sys.argv) == 2:
    inputf = sys.argv[1]
else:
    inputf = "TCAinput.xml"

timer = Timer(enabled=False)
timer.start('1_main')

CF = ControlFiles(inputf)

CF.Load_files()

if CF.Control['RegionsFile'] is not None:
    if CF.Control["FileType"] == "VISSIM":
        unit_conversion = 100 / 2.54 / 12
    else:
        unit_conversion = 1
    R = Load_Regions(CF.Control['RegionsFile'],CF.Control['Seed'],unit_conversion)
    print "Loading Regions File %s" % CF.Control['RegionsFile']
else:
    R = None

if CF.Error_count() > 0:
    logger.critical("Errors in the control and/or strategy file, see TCA_Input_Summary.csv file for details")
    sys.exit()

RandomGen = Random_generator(CF.Control['Seed'])
RandomGen.add_generator_int('GapDistance', CF.Strategy["GapMinDistance"], CF.Strategy["GapMaxDistance"])
RandomGen.add_generator_int('GapTimeout', CF.Strategy["GapMinTime"], CF.Strategy["GapMaxTime"])
RandomGen.add_generator_int('psn', 0, 32767)  #range based on J2735
RandomGen.add_generator_int('LossPercent', 1, 100)

Algorithm = TCA_Algorithm(CF)

trj = Trajectories()
trj.load(CF)
output = TCA_Output(CF, R)

tbl = DataStorage(trj.equip_vehicles, R, trj.equip_PDM, trj.equip_BSM, trj.equip_DualPDMBSM, trj.DSRC_list,
                  trj.cellular_list, trj.dualcomm_list, trj.include_accel)

pdm = False

if len(trj.equip_PDM) > 0 or  len(trj.equip_DualPDMBSM) > 0:
    pdm = True

LastTP = 0.0

with open('time_testing.csv', 'wb') as time_f:
    time_f.write('time_period, active, BSMs, PDMs, buff_keys,  run_time, Update_time, CheckSnapshot, CheckDSRC, '
                 + 'CheckCellular, PSNCheck, alg_check_dsrc_select_vehicles, alg_check_dsrc_Find_RSE_Ranges, '
                 + 'alg_check_dsrc_Transmit\n')

for tp, df in trj.read(CF.Control['FileType']):

    timer.start('tp')

    logger.debug('tp %d number of vehicles %d' % (tp, len(df)))

    Algorithm.BSMBuffer = {}

    if CF.Control["OutputLevel"] > 0:
        if tp % 1000 == 0:
           logger.info("Time Step: %d" % (tp))

    timer.start('2_Update_Table')
    timeStep = tp-LastTP
    tbl.update(tp, df, RandomGen, CF, time_step = timeStep)
    timer.stop('2_Update_Table')


    if len(trj.equip_BSM) > 0 or len(trj.equip_DualPDMBSM) > 0:
        if CF.Control['RegionsFile'] is not None:
            timer.start('3_CheckRegions')
            Algorithm.CheckRegion(tbl.df, tp, CF, R)
            timer.stop('3_CheckRegions')
        timer.start('4_CheckBrakes')
        Algorithm.CheckBrakes(tbl.df, CF)
        timer.stop('4_CheckBrakes')

    if tp % 1 == 0:
        checkPDM = True
    else:
        checkPDM = False

    if checkPDM and pdm:
        timer.start('5_CheckSnapshot')
        Algorithm.CheckPDMSnapshot(tbl.df, timeStep, tp, CF, R)
        timer.stop('5_CheckSnapshot')


    timer.start('6_CheckDSRC')
    Algorithm.CheckDSRC(tbl.df, CF, checkPDM, pdm, tp, R, RandomGen)
    timer.stop('6_CheckDSRC')

    timer.start('7_CheckCellular')
    Algorithm.CheckCellular(tbl.df, CF, RandomGen, checkPDM, pdm, tp, R)
    timer.stop('7_CheckCellular')

    if checkPDM and pdm:
        timer.start('8_PSNCheck')
        Algorithm.PSNCheck(tbl.df, tp, RandomGen, CF)
        timer.stop('8_PSNCheck')

    LastTP = tp

    if len(Algorithm.BSMs) >= Algorithm.BSM_limit:
        df_BSMs = pd.DataFrame(Algorithm.BSMs)
        df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"], index=False,  mode='a')
        Algorithm.BSMs = []

    timer.stop('tp')

    if tp % 100 ==0:
        with open('time_testing.csv', 'a') as time_f:
            time_f.write('%s,%d,%d,%d,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' %
                         (str(tp),
                         len(tbl.df[(tbl.df['active'])]),
                         len(Algorithm.BSMs),
                         len(Algorithm.PDMs),
                         len(Algorithm.PDMBuffer.ActiveBuffers.keys()),
                         str(timer.current('tp')),
                         str(timer.current('Update_Table')),
                         str(timer.current('CheckSnapshot')),
                         str(timer.current('CheckDSRC')),
                         str(timer.current('CheckCellular')),
                         str(timer.current('PSNCheck')),
                         str(Algorithm.timer.current('alg_check_dsrc_select_vehicles')),
                         str(Algorithm.timer.current('alg_check_dsrc_Find_RSE_Ranges')),
                         str(Algorithm.timer.current('alg_check_dsrc_Transmit')),
                         ))

if len(trj.equip_BSM) > 0 or len(trj.equip_DualPDMBSM) > 0:
    df_BSMs = pd.DataFrame(Algorithm.BSMs)
    df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"], index=False,  mode='a')


if len(trj.equip_PDM) > 0 or len(trj.equip_DualPDMBSM) > 0:
    for ID in Algorithm.PDMBuffer.ActiveBuffers.keys():
        Algorithm.PDMBuffer.ClearBuffer(ID, LastTP + 2, Algorithm.PDMs, 2, -1, -1)
    output.WriteSSList(Algorithm.PDMs, CF)


timer.stop('1_main')
if CF.Control["OutputLevel"] > 0:
    logger.info("End time %s" % (time.strftime('%X', time.localtime(time.time()))))
    logger.info("************  End Program  *******************")
if timer.enabled:
    with open('timeit.csv', 'wb') as time_f:
        time_f.write(timer.header())
        time_f.write(timer.write())
        time_f.write('\n\n')
        time_f.write(tbl.timer.write())
        time_f.write('\n\n')
        time_f.write(Algorithm.timer.write())
del Algorithm
