#standard
from datetime import datetime as dt
import sys
import time

#TCA
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCADataStore import DataStorage
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
from TCAOutput import TCA_Output
from TCACore import Timer


#Check for control file
if len(sys.argv) == 2:
    inputf = sys.argv[1]
else:
    inputf = "TCAinput.xml"

CF = ControlFiles(inputf)
CF.Load_files()

output = TCA_Output(CF)

RandomGen = Random_generator(CF.Control['Seed'])
RandomGen.add_generator_range('GapDistance', CF.Strategy["GapMinDistance"], CF.Strategy["GapMaxDistance"])
RandomGen.add_generator_range('GapTimeout', CF.Strategy["GapMinTime"], CF.Strategy["GapMaxTime"])
RandomGen.add_generator_range('psn', 0, 32767)  #range based on J2735
RandomGen.add_generator_range('LossPercent', 1, 100)

Algorithm = TCA_Algorithm(CF)

trj = Trajectories()
trj.load(CF)

tbl = DataStorage(trj.equip_vehicles, trj.equip_PDM, trj.equip_BSM)
if CF.Strategy['PDMCellularFlag']:
    tbl.df["cellular_enabled"][trj.equip_PDM] = True
if CF.Strategy['BSMCellularFlag']:
    tbl.df["cellular_enabled"][trj.equip_BSM] = True

if CF.Control['OutputLevel'] >=1:
    print "Number of PDM equipped vehicles = %d" % len(trj.equip_PDM)
    print "Number of BSM equipped vehicles = %d" % len(trj.equip_BSM)

LastTP = 0

timeit = False

if timeit:
    timer = Timer()

for tp, df in trj.read():

    if CF.Control["OutputLevel"] > 0:
        if tp % 1000 == 0:
           print "Time Step: %d" % (tp)

    if timeit:
        timer.start('Update Table')
    tbl.update(tp, df, RandomGen)

    timeStep = 1
    if tp - LastTP > 1 and LastTP != 0:
        timeStep = tp - LastTP

    if timeit:
        timer.stop()
        timer.start('CheckSnapshot')
    Algorithm.CheckSnapshot(tbl.df, timeStep, tp, CF)
    if timeit:
        timer.stop()

    #Check for cellular communication option. Else, transmit via RSEs
    if CF.Strategy['PDMCellularFlag'] or CF.Strategy['BSMCellularFlag']:
        if timeit:
            timer.start('CheckCellular')
        Algorithm.CheckCellular(tbl.df, CF, RandomGen)
        if timeit:
            timer.stop()

    if not CF.Strategy['PDMCellularFlag'] or not CF.Strategy['BSMCellularFlag']:
        if timeit:
            timer.start('ChkRSERange')
        Algorithm.ChkRSERange(tbl.df, CF)
        if timeit:
            timer.stop()

    if timeit and len(trj.equip_PDM) > 0:
        timer.start('PSNCheck')
    if len(trj.equip_PDM) > 0:
        Algorithm.PSNCheck(tbl.df, tp, RandomGen, CF)
    if timeit and len(trj.equip_PDM) > 0:
        timer.stop()

    LastTP = tp

if len(trj.equip_BSM) > 0:
    for ID in Algorithm.BSMBuffer.ActiveBuffers.keys():
        Algorithm.BSMBuffer.ClearBuffer(ID, LastTP + 2, Algorithm.BSMs, 2, -1, -1)
    output.WriteBSMList(Algorithm.BSMs, CF)


if len(trj.equip_PDM) > 0:
    for ID in Algorithm.SSBuffer.ActiveBuffers.keys():
        Algorithm.SSBuffer.ClearBuffer(ID, LastTP + 2, Algorithm.Snapshots, 2, -1, -1)
    output.WriteSSList(Algorithm.Snapshots, CF)


if CF.Control["OutputLevel"] > 0:
    print "End time %s" % (time.strftime('%X', time.localtime(time.time())))
    print "**********************************************"
    print "************  End Program  *******************"
    print "**********************************************"
if timeit:
    with open('timeit.csv', 'wb') as time_f:
        time_f.write(timer.write())
        time_f.write('\n\n')
        time_f.write(tbl.timer.write())

