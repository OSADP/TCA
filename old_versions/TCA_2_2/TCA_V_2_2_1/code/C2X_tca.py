#standard
import time
import sys
import logging
from datetime import datetime as dt

#external
import c2x
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

#============================================================================
class C2X_tca (c2x.ApplicationBase):
    def __init__ (self, Debugger):
        """Constructor, needs to call the base-class constructor explicitely,
        otherwise c2x.run() will complain about non-matching signature."""

        c2x.ApplicationBase.__init__ (self)
        print "\nc2x initialized"


    def processTimestep (self):
        """This method is called every timestep for each class derived from
        c2x.ApplicationBase which is started with the <run()> function.
        TCA currently only runs every second
        VISSIM runs every tenth of a second
        """

        try:
            global vissimtimeit

            if not vissimtimeit:
                global LastTP
                global Snapshots
                global PDMBuffer
                global BSMBuffer

                tp = c2x.getCurrentTime()

                if CF.Control["OutputLevel"] > 0:
                    if tp % 1000 == 0:
                       logger.info("Time Step: %d" % (tp))
                       # logger.info("len of bsm: %d   len of pdm: %d" % (len(Algorithm.BSMs), len(Algorithm.PDMs) ))
                       temp_df = tbl.df[(tbl.df['active'])]
                       logger.info("Vehicle count: %d" % (len(temp_df)))

                vehicles = c2x.getVehicles()

                if len (vehicles) == 0:
                    LastTP = tp
                    return

                pdm = False
                cellular_comm = False
                vehicle_list = []
                for vehicle in vehicles:
                    if vehicle.TypeID in CF.Control['PDMBSMDSRCVehicleTypes'] or vehicle.ID in CF.Control['PDMBSMDSRCVehicleIDs']:
                            pdm = True
                            vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600,  #convert m/s to mph
                                        'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                        'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                        'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                        'PDM_equipped' : True,
                                        'BSM_equipped' : True,
                                        'DSRC_enabled' : True,
                                        'cellular_enabled' : False,
                                        'dual_enabled' : False,
                            })

                    elif vehicle.TypeID in CF.Control['PDMBSMCellularVehicleTypes'] or vehicle.ID in CF.Control['PDMBSMCellularVehicleIDs']:
                            pdm = True
                            cellular_comm = True
                            vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                                        'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                        'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                        'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                        'PDM_equipped' : True,
                                        'BSM_equipped' : True,
                                        'DSRC_enabled' : False,
                                        'cellular_enabled' : True,
                                        'dual_enabled' : False,
                            })
                    elif vehicle.TypeID in CF.Control['PDMBSMDualCommVehicleTypes'] or vehicle.ID in CF.Control['PDMBSMDualCommVehicleIDs']:
                            cellular_comm = True
                            pdm = True
                            vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                                        'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                        'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                        'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                        'PDM_equipped' : True,
                                        'BSM_equipped' : True,
                                        'DSRC_enabled' : False,
                                        'cellular_enabled' : False,
                                        'dual_enabled' : True,
                            })

                    elif vehicle.TypeID in CF.Control['BSMDSRCVehicleTypes'] or vehicle.ID in CF.Control['BSMDSRCVehicleIDs']:
                            vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                                        'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                        'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                        'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                        'PDM_equipped' : False,
                                        'BSM_equipped' : True,
                                        'DSRC_enabled' : True,
                                        'cellular_enabled' : False,
                                        'dual_enabled' : False,
                            })

                    elif vehicle.TypeID in CF.Control['BSMCellularVehicleTypes'] or vehicle.ID in CF.Control['BSMCellularVehicleIDs']:
                            cellular_comm = True
                            vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                                        'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                        'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                        'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                        'PDM_equipped' : False,
                                        'BSM_equipped' : True,
                                        'DSRC_enabled' : False,
                                        'cellular_enabled' : True,
                                        'dual_enabled' : False,
                            })
                    elif vehicle.TypeID in CF.Control['BSMDualCommVehicleTypes'] or vehicle.ID in CF.Control['BSMDualCommVehicleIDs']:
                            cellular_comm = True
                            vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                                        'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                        'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                        'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                        'PDM_equipped' : False,
                                        'BSM_equipped' : True,
                                        'DSRC_enabled' : False,
                                        'cellular_enabled' : False,
                                        'dual_enabled' : True,
                            })

                    elif vehicle.TypeID in CF.Control['PDMDSRCVehicleTypes'] or vehicle.ID in CF.Control['PDMDSRCVehicleIDs']:
                        pdm = True
                        vehicle_list.append({
                                    'vehicle_ID':vehicle.ID,
                                    'time' : tp,
                                    'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                                    'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                    'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                    'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                    'PDM_equipped' : True,
                                    'BSM_equipped' : False,
                                    'DSRC_enabled' : True,
                                    'cellular_enabled' : False,
                                    'dual_enabled' : False,
                        })

                    elif vehicle.TypeID in CF.Control['PDMCellularVehicleTypes'] or vehicle.ID in CF.Control['PDMCellularVehicleIDs']:
                            pdm = True
                            cellular_comm = True
                            vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                                        'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                        'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                        'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                        'PDM_equipped' : True,
                                        'BSM_equipped' : False,
                                        'DSRC_enabled' : False,
                                        'cellular_enabled' : True,
                                        'dual_enabled' : False,
                            })
                    elif vehicle.TypeID in CF.Control['PDMDualCommVehicleTypes'] or vehicle.ID in CF.Control['PDMDualCommVehicleIDs']:
                            pdm = True
                            cellular_comm = True
                            vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                                        'accel_instantaneous' : vehicle.Acceleration * 100 / 2.54 / 12, #convert to ft/s^2
                                        'location_x' : vehicle.Position.X * 100 / 2.54 / 12, #convert meters to feet
                                        'location_y' : vehicle.Position.Y * 100 / 2.54 / 12, #convert meters to feet
                                        'PDM_equipped' : True,
                                        'BSM_equipped' : False,
                                        'DSRC_enabled' : False,
                                        'cellular_enabled' : False,
                                        'dual_enabled' : True,
                            })

                if len(vehicle_list) == 0:
                    return
                df = pd.DataFrame(vehicle_list)

                Algorithm.BSMBuffer = {}

                timeStep = tp - LastTP
                timer.start('Update Table')
                tbl.update(tp, df,RandomGen, CF,TCA_version = 'vissim', time_step = timeStep)
                timer.stop()


                if CF.Control['RegionsFile'] is not None:
                    timer.start('CheckRegions')
                    Algorithm.CheckRegion(tbl.df, tp, CF, R)
                    timer.stop()

                timer.start('CheckBrakes')
                Algorithm.CheckBrakes(tbl.df, CF)
                timer.stop()

                if tp % 1 == 0:
                    checkPDM = True
                else:
                    checkPDM = False

                if checkPDM and pdm:
                    timer.start('CheckSnapshot')
                    Algorithm.CheckPDMSnapshot(tbl.df, timeStep, tp, CF, R)
                    timer.stop()

                timer.start('CheckDSRC')
                Algorithm.CheckDSRC(tbl.df, CF, checkPDM, pdm, tp, R, RandomGen)
                timer.stop()



                if cellular_comm:
                    timer.start('CheckCellular')
                    Algorithm.CheckCellular(tbl.df, CF, RandomGen, checkPDM, pdm, tp, R)
                    timer.stop()


                if checkPDM:
                    timer.start('PSNCheck')
                    Algorithm.PSNCheck(tbl.df, tp, RandomGen, CF)
                    timer.stop()


                if len(Algorithm.BSMs) >= Algorithm.BSM_limit:
                    df_BSMs = pd.DataFrame(Algorithm.BSMs)
                    df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"], index=False,  mode='a')
                    Algorithm.BSMs = []


                #Go through vehicles and change the color if a snapshot is generated
                if changecolor:
                    color_display_time = CF.Control['ColorDisplayDuration']

                    for vehicle in vehicles:
                        select = (tbl.df['vehicle_ID'] == vehicle.ID)

                        # if int(tbl.df['hard_braking'][select])==1:
                        #     vehicle.setColor(204,0,0) #red

                        # elif int(tbl.df['ExtLights'][select])==1 and int(tbl.df['Wipers'][select])==1:
                        #     vehicle.setColor(102,204,0) #Green

                        # elif int(tbl.df['Wipers'][select])==1:
                        #     vehicle.setColor(0,0,204) #blue

                        # elif int(tbl.df['ExtLights'][select])==1:
                        #     vehicle.setColor(255,255,71) #yellow

                        # elif (tbl.df['AirTemp'][select] > 35):
                        #     vehicle.setColor(102,0,102) #dark purple

                        # elif (tbl.df['AirTemp'][select] > 25):
                        #     vehicle.setColor(255,0,255)  #light purple

                        # else :
                        #     vehicle.setColor(255,255,255) #Change color to white

                        if (tbl.df['time_of_start_snapshot'][select] - tp + color_display_time > 0):
                            vehicle.setColor(102,204,0)   #Change color to green for start PDM SS

                        elif (tbl.df['time_of_last_stop'][select] - tp + color_display_time > 0):
                            vehicle.setColor(204,102,0)   #Change color to orange for stop PDM SS

                        elif (tbl.df['dsrc_transmit_pdm'][select] and (tbl.df['time_of_last_transmit'][select] - tp + color_display_time > 0)):
                            vehicle.setColor(0,0,0) #Change to black for PDM DSRC transmission

                        elif ((not tbl.df['dsrc_transmit_pdm'][select]) and (tbl.df['time_of_last_transmit'][select] - tp + color_display_time > 0)):
                            vehicle.setColor(0,204,204) #Change to light blue for PDM cellular transmission

                        elif (tbl.df['time_of_periodic_snapshot'][select] - tp + color_display_time > 0):
                            vehicle.setColor(204,0,204)    #Change color to purple for periodic PDM

                        elif (tbl.df['BSM_equipped'][select] and tbl.df['PDM_equipped'][select]):
                            vehicle.setColor(255,255,71) #Change to yellow for Dual PDM-BSM vehicles

                        elif ((not tbl.df['BSM_equipped'][select]) and tbl.df['PDM_equipped'][select]):
                            vehicle.setColor(0,204,102) #Change to teal for PDM-only vehicles

                        elif (tbl.df['BSM_equipped'][select]):
                            vehicle.setColor(0,0,204)   #Change BSM-only vehicles to blue

                        else :
                            vehicle.setColor(255,255,255) #Change color to white

                LastTP = tp

        except:
            raise
            time.sleep(1000)

#----------------------------------------------------------------------

def tca_v(inputf = 'code/TCAinput.xml'):

    global timer
    global timeval
    global vissimtimeit
    global changecolor

    timer = Timer(enabled=True)

    vissimtimeit = False #True: time VISSIM without the TCA running.
    changecolor = True

    try:

        global tbl
        global LastTP
        global CF
        global RandomGen
        global Algorithm
        global output
        global logger
        global R

        LastTP = 0
        if len(sys.argv) == 2:
            inputf = sys.argv[1]
        CF = ControlFiles(inputf, TCA_version = 'vissim')
        CF.Load_files()
        CF.Control['AccelColumn'] = True

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
            logging.critical("Errors in the control and/or strategy file, see TCA_Input_Summary.csv file for details")
            sys.exit()

        output = TCA_Output(CF,R)

        RandomGen = Random_generator(CF.Control['Seed'])
        RandomGen.add_generator_int('GapDistance', CF.Strategy["GapMinDistance"], CF.Strategy["GapMaxDistance"])
        RandomGen.add_generator_int('GapTimeout', CF.Strategy["GapMinTime"], CF.Strategy["GapMaxTime"])
        RandomGen.add_generator_int('psn', 0, 32767)  #range based on J2735
        RandomGen.add_generator_int('LossPercent', 1, 100)

        Algorithm = TCA_Algorithm(CF)

        tbl = DataStorage(list(xrange(int(CF.Control['NumberEquippedVehicles']))), Regions = R, accel_included = True, time_step = 0.1)
        app = C2X_tca(CF.Control["OutputLevel"])
        timer.start('Total Runtime')

        logger.debug('TEST TEST')

        app.run()

        if not vissimtimeit:
            select_PDM = (tbl.df['PDM_equipped']) & (tbl.df['BSM_equipped']==False)
            select_BSM = (tbl.df['BSM_equipped']) & (tbl.df['PDM_equipped']==False)
            select_DualPDMBSM = (tbl.df['PDM_equipped']) & (tbl.df['BSM_equipped'])
            pdm = len(tbl.df[(select_PDM & (tbl.df['total_time_in_network'] > 0))])
            bsm = len(tbl.df[(select_BSM & (tbl.df['total_time_in_network'] > 0))])
            dual = len(tbl.df[(select_DualPDMBSM & (tbl.df['total_time_in_network'] > 0))])
            pdm_dsrc = len(tbl.df[(select_PDM & tbl.df['DSRC_enabled'])])
            pdm_cell = len(tbl.df[(select_PDM & tbl.df['cellular_enabled'])])
            pdm_dual = len(tbl.df[(select_PDM & tbl.df['dual_enabled'])])
            bsm_dsrc = len(tbl.df[(select_BSM & tbl.df['DSRC_enabled'])])
            bsm_cell = len(tbl.df[(select_BSM & tbl.df['cellular_enabled'])])
            bsm_dual = len(tbl.df[(select_BSM & tbl.df['dual_enabled'])])
            dual_dsrc = len(tbl.df[(select_DualPDMBSM & tbl.df['DSRC_enabled'])])
            dual_cell = len(tbl.df[(select_DualPDMBSM & tbl.df['cellular_enabled'])])
            dual_dual = len(tbl.df[(select_DualPDMBSM & tbl.df['dual_enabled'])])
            total = pdm + bsm + dual
            typeCounts = {'PDM':pdm,'BSM':bsm,'DualPDMBSM':dual,'PDM-DSRC':pdm_dsrc,'PDM-Cellular':pdm_cell,'PDM-DualComm':pdm_dual,\
                'BSM-DSRC':bsm_dsrc,'BSM-Cellular':bsm_cell,'BSM-DualComm':bsm_dual,'Dual-DSRC':dual_dsrc,'Dual-Cellular':dual_cell,\
                'Dual-DualComm':dual_dual, 'total':total}

            with open('vehiclecounts.csv', 'wb') as counts_f:
                for key,value in sorted(typeCounts.items()):
                    counts_f.write('Number of %s vehicles:,%d\n' % (key,int(value)))

            if len(Algorithm.BSMs) > 0:
                df_BSMs = pd.DataFrame(Algorithm.BSMs)
                df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"], index=False,  mode='a')

            if len(Algorithm.PDMs) > 0:
                for ID in Algorithm.PDMBuffer.ActiveBuffers.keys():
                    Algorithm.PDMBuffer.ClearBuffer(ID, LastTP + 2, Algorithm.PDMs, 2, -1, -1)
                output.WriteSSList(Algorithm.PDMs, CF)

        timer.stop('Total Runtime')
        if timer.enabled:
            with open('timeit.csv', 'wb') as time_f:
                time_f.write(timer.header())
                time_f.write(timer.write())

    except BaseException, e:
        print str (e)
        raise
        time.sleep(4000)
    except:
        time.sleep(4000)


#----------------------------------------------------------------------


if __name__ == "__main__":
    tca_v()