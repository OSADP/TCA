#standard
import sys
import time


#TCA
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
# from TCAOutput import TCA_Output
from TCACore import Timer, logger, report_errors, clear_old_files, write_default, write_default_regions, control_values, strategy_values
from TCARegions import Load_Regions
from TCASpacePartitioning import Location_Tree
from TCANetData import CLNetData

import argparse

def main():
    """
    TCA main procedure

    """
    parser = argparse.ArgumentParser(description = 'The Trajectory Conversion Algorithm (TCA) Software is designed to test different strategies for producing, transmitting, and storing Connected \
        Vehicle information.The TCA reads in and uses vehicle trajectory information, Roadside Equipment (RSE) location information, cellular region information, event region information, and strategy \
        information to produce a series of snapshots that the vehicle would produce. Vehicles can be equipped to generate and transmit Probe Data Messages (PDMs), Basic Safety Messages (BSMs), ITS SPOT \
        messages, or European CAM which can be transmitted by either Dedicated Short Range Communication (DSRC), cellular, or both.')
    parser.add_argument('input_file', help = 'TCA input file', default = 'TCAinput.xml', nargs = '?')
    parser.add_argument('--makeInput', help = 'Make input file with specified filename, strategy file(Default_Strategy.xml), Regions File(Default_Regions.xml)')
    parser.add_argument('--makeStrategy', help = 'Make strategy file with specified filename')
    parser.add_argument('--makeRegions', help = 'Make Regions file with specified filename')

    args = parser.parse_args()
    if args.makeInput or args.makeStrategy or args.makeRegions:
        if args.makeInput:
            write_default(args.makeInput, 'ControlFile', control_values)
            write_default("Default_Strategy.xml", 'Strategy', strategy_values)
            write_default_regions('Default_Regions.xml')
        if args.makeStrategy:
            write_default(args.makeStrategy, 'Strategy', strategy_values)
        if args.makeRegions:
            write_default_regions(args.makeRegions)
        sys.exit()
    

    program_st = time.time()
    CF = ControlFiles(args.input_file)
    CF.Load_files()


    if CF.Control["FileType"] == "VISSIM":
        unit_conversion = 100 / 2.54 / 12 # Converts meters to ft (for x,y coordinates)
    else:
        unit_conversion = 1

    if CF.Control['RegionsFile'] is not None:
        Regions = Load_Regions(CF.Control['RegionsFile'], CF.Control['Seed'], unit_conversion)
        if CF.Control["OutputLevel"] > 0:
            logger.info("Loading Regions File %s" % CF.Control['RegionsFile'])
    else:
        Regions = None

    if CF.Control["RSELocationFile"] is not None:
       RSEs = CLNetData(unit_conversion)
       errors = RSEs.RSELoad(CF.Control["RSELocationFile"], CF)
       report_errors(errors)
       RSE_Tree = Location_Tree(RSEs.RSEList, CF.Strategy["MinRSERange"])
    else:
        RSEs = None
        RSE_Tree = None

    if CF.Control["SPOTLocationFile"] is not None:
        SPOTdevices = CLNetData(unit_conversion)
        errors = SPOTdevices.SPOTLoad(CF.Control["SPOTLocationFile"], CF)
        report_errors(errors)
        SPOT_Tree = Location_Tree(SPOTdevices.SPOTList, CF.Strategy["SPOTdeviceRange"])
    else:
        SPOT_Tree = None


    trajectory_file = Trajectories(CF.Control['TrajectoryFileName'], CF.Control['OutputLevel'], CF.Control["FileType"])

    clear_old_files(CF)

    Algorithm = TCA_Algorithm(CF, RSEs, RSE_Tree, CF.Control['Seed'], Regions, SPOT_Tree)

    LastTP = 0.0


    for tp, vehicles in trajectory_file.read_by_tp(CF):

        if CF.Control["OutputLevel"] > 0:
            if tp % 1000 == 0:
               logger.info("Time Step: %d" % (tp))

        # Remove vehicle data of vehicles not seen in the concurrent timestep
        Algorithm.tbl.remove_non_active_vehicles(vehicles)

        vehicles_data = Algorithm.pull_veh_data(vehicles, tp)

        if RSE_Tree is not None:
            range_data = RSE_Tree.find_ranges(vehicles_data)

        for veh_data in vehicles_data:

            #if vehicle equipped
            if veh_data is not None:

                if veh_data['BSM_equipped']:
                    Algorithm.BSM.CheckBrakes(veh_data)

                if CF.Control['RegionsFile'] is not None:
                    Regions.CheckRegions(veh_data, tp)

                #if SPOT equipped
                if veh_data['SPOT_equipped']:
                    Algorithm.SPOT.CheckMessage(veh_data, tp) 
                    Algorithm.SPOT.CheckRange(veh_data, tp) 

                #if PDM equipped
                if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                    Algorithm.PDM.CheckMessage(veh_data, tp) 

                if veh_data['DSRC_enabled'] and CF.Control['RSELocationFile'] != None:
                    Algorithm.CheckDSRC(veh_data, tp, range_data)

                Algorithm.CheckCellular(veh_data, tp)

                if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                    Algorithm.PDM.PSNCheck(veh_data, tp)

                if veh_data['BSM_equipped']:
                    Algorithm.BSM.tmp_ID_check(veh_data, tp)

                Algorithm.BSM.Write()
                Algorithm.CAM.Write()

                Algorithm.tbl.previous_values(veh_data)

        LastTP = tp

    if len(Algorithm.BSM.BSM_list) > 0 :
        Algorithm.BSM.Write(clear_buffer=True)

    if len(Algorithm.CAM.CAM_list) > 0 :
        Algorithm.CAM.Write(clear_all=True)

    if len(Algorithm.PDM.PDM_list) > 0 :
        Algorithm.PDM.Write(clear_buffer=True, LastTP = LastTP)

    if len(Algorithm.SPOT.Travelmsgs) > 0:
        Algorithm.SPOT.Write(clear_all=True)

    if CF.Control["OutputLevel"] > 0:
        Algorithm.tbl.list_veh_counts()

    if CF.Control["OutputLevel"] > 0:
        ed_time = time.time()
        logger.info("End time %s (%f)" % (time.strftime('%X', time.localtime(ed_time)), (ed_time - program_st) ))
        logger.info("*******************  End Program  *******************")


    del Algorithm



if __name__ == '__main__':
    main()