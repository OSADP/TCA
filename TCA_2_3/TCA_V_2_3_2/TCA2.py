#standard
import sys
import time


#TCA
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
# from TCAOutput import TCA_Output
from TCACore import logger, report_errors, clear_old_files
from TCARegions import Load_Regions
from TCASpacePartitioning import Location_Tree
from TCANetData import CLNetData


def main():
    """
    TCA main procedure

    """

    if len(sys.argv) == 2:
        input_file = sys.argv[1]
    else:
        input_file = "TCAinput.xml"


    program_st = time.time()

    CF = ControlFiles(input_file)
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
        Algorithm.BSMBuffer = {}

        if CF.Control["OutputLevel"] > 0:
            if tp % 1000 == 0:
               logger.info("Time Step: %d" % (tp))

        Algorithm.tbl.remove_non_active_vehicles(vehicles)

        vehicles_data = Algorithm.pull_veh_data(vehicles, tp)

        range_data = RSE_Tree.find_ranges(vehicles_data)

        for veh_data in vehicles_data:
            # veh_data = Algorithm.pull_veh_data(vehicle, tp)

            #if vehicle equipped
            if veh_data is not None:

                if veh_data['BSM_equipped']:
                    if CF.Control['RegionsFile'] is not None:
                        Algorithm.CheckRegion(veh_data, tp)
                    Algorithm.CheckBrakes(veh_data)

                #if SPOT equipped
                if veh_data['SPOT_equipped']:
                    Algorithm.CheckSPOT(veh_data, tp)
                    Algorithm.CheckSPOTdevice(veh_data, tp)

                #if PDM equipped
                if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                    Algorithm.CheckPDMSnapshot(veh_data, tp)

                if veh_data['DSRC_enabled']:
                    Algorithm.CheckDSRC(veh_data, tp, range_data)

                Algorithm.CheckCellular(veh_data, tp)

                if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                    Algorithm.PSNCheck(veh_data, tp)

                if veh_data['BSM_equipped']:
                    Algorithm.BSM_tmp_ID_check(veh_data, tp)

                Algorithm.Write_BSMs(CF)
                Algorithm.Write_CAM(CF)

                Algorithm.tbl.previous_values(veh_data)

        LastTP = tp

    if len(Algorithm.BSMs) > 0 :
        Algorithm.Write_BSMs(CF=CF, clear_buffer=True)

    if len(Algorithm.CAMs) > 0 :
        Algorithm.Write_CAM(CF=CF, clear_all=True)


    if len(Algorithm.PDMs) > 0 :
        for ID in Algorithm.PDMBuffer.ActiveBuffers.keys():
            Algorithm.PDMBuffer.ClearBuffer(vehicleID = ID, locT = LastTP + 2, Snapshots = Algorithm.PDMs,
                                            reason = 2, transmitted_to = -1, transTime = -1)
        Algorithm.Write_PDMs(CF, clear_buffer=True)
        # output_files.WriteSSList(Algorithm.PDMs, CF)

    if len(Algorithm.TravelSPOTmsgs) > 0:
        Algorithm.Write_SPOT(CF, clear_all=True)
        # output_files.WriteSPOTList(Algorithm.TravelSPOTmsgs, Algorithm.BehaviorSPOTmsgs, CF)

    if CF.Control["OutputLevel"] > 0:
        Algorithm.tbl.list_veh_counts()

    if CF.Control["OutputLevel"] > 0:
        ed_time = time.time()
        logger.info("End time %s (%f)" % (time.strftime('%X', time.localtime(ed_time)), (ed_time - program_st) ))
        logger.info("*******************  End Program  *******************")

    del Algorithm



if __name__ == '__main__':
    main()