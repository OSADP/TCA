#standard
import time
import sys
from datetime import datetime as dt

#external
import c2x
import pandas as pd

#TCA
from TCACore import report_errors, ControlVars
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCADataStore import DataStorage
from TCAAlgorithm import TCA_Algorithm
from TCAOutput import TCA_Output

#============================================================================
# TEST CHANGE TEXT
class C2X_tca (c2x.ApplicationBase):
    def __init__ (self, Debugger):
        """Constructor, needs to call the base-class constructor explicitely,
        otherwise c2x.run() will complain about non-matching signature."""

        c2x.ApplicationBase.__init__ (self)
        print "\nc2x initialized"
        if Debugger >= 1:
            self.OutputFile = "code\\" + "VissimTcaOutputInfo.csv"
            self.ClearoldData()



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

                with open(self.OutputFile,"a") as f:

                    tp = c2x.getCurrentTime()

                    vehicles = c2x.getVehicles()

                    if len (vehicles) == 0:
                        LastTP = tp
                        return

                    if (tp % 1.0 != 0.0):
                        vehicle_list = []
                        for vehicle in vehicles:
                            Cellular = False

                            for id in CF.Control['BSMVehicleTypes']:
                                if id == vehicle.TypeID:
                                    Cellular = CF.Strategy['BSMCellularFlag'] 

                                    vehicle_list.append({
                                        'vehicle_ID':vehicle.ID,
                                        'time' : tp,
                                        'speed' : vehicle.Speed * 2.23694, #convert m/s to mph
                                        'location_x' : vehicle.Position.X,
                                        'location_y' : vehicle.Position.Y,
                                        'PDM_equipped' : False,
                                        'BSM_equipped' : True,
                                        'cellular_enabled' : Cellular
                                    })

                        if len(vehicle_list) == 0:
                            return
                        df = pd.DataFrame(vehicle_list)

                        if timeit:
                            start = dt.now()


                        tbl.update(tp, df,RandomGen,True)                          
                        if timeit:
                            timeval['Update Table'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds * 0.000001)

                        timeStep = 1
                        if tp - LastTP > 1 and LastTP != 0:
                            timeStep = tp - LastTP

                        if timeit:
                            start = dt.now()

                        Algorithm.CheckSnapshot(tbl.df, timeStep, tp, CF)

                        if timeit:
                            timeval['CheckSnapshot'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds * 0.000001)

                        if timeit:
                            start = dt.now()

                        #Check for cellular communication option. Else, transmit via RSEs
                        if CF.Strategy['BSMCellularFlag']:
                            if timeit:
                                start = dt.now()
                            Algorithm.CheckCellular(tbl.df, CF, RandomGen)
                            if timeit:
                                timeval['CheckCellular'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds * 0.000001)
                        if not CF.Strategy['BSMCellularFlag']:
                            if timeit:
                                start = dt.now()
                            Algorithm.ChkRSERange(tbl.df, CF)
                            if timeit:
                                timeval['ChkRSERange'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds * 0.000001)
                    else: 
                        vehicle_list = []
                        for vehicle in vehicles:
                            PDM = False
                            Cellular = False
                            BSM = False

                            for id in CF.Control['PDMVehicleTypes']:
                                if id == vehicle.TypeID:
                                    PDM = True
                                    Cellular = CF.Strategy['PDMCellularFlag']

                            for id in CF.Control['BSMVehicleTypes']:
                                if id == vehicle.TypeID:
                                    BSM = True
                                    Cellular = CF.Strategy['BSMCellularFlag'] 

                            vehicle_list.append({
                                'vehicle_ID':vehicle.ID,
                                'time' : tp,
                                'speed' : vehicle.Speed * 2.23694, #convert m/s to mph
                                'location_x' : vehicle.Position.X,
                                'location_y' : vehicle.Position.Y,
                                'PDM_equipped' : PDM,
                                'BSM_equipped' : BSM,
                                'cellular_enabled' : Cellular
                            })
                        df = pd.DataFrame(vehicle_list)

                        if timeit:
                            start = dt.now()


                        tbl.update(tp, df,RandomGen,True)                          
                        if timeit:
                            timeval['Update Table'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds * 0.000001)

                        timeStep = 1
                        if tp - LastTP > 1 and LastTP != 0:
                            timeStep = tp - LastTP

                        if timeit:
                            start = dt.now()

                        Algorithm.CheckSnapshot(tbl.df, timeStep, tp, CF)

                        if timeit:
                            timeval['CheckSnapshot'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds * 0.000001)

                        if timeit:
                            start = dt.now()

                        #Check for cellular communication option. Else, transmit via RSEs
                        if CF.Strategy['PDMCellularFlag'] or CF.Strategy['BSMCellularFlag']:
                            if timeit:
                                start = dt.now()
                            Algorithm.CheckCellular(tbl.df, CF, RandomGen)
                            if timeit:
                                timeval['CheckCellular'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds  * 0.000001)
                        if not CF.Strategy['PDMCellularFlag'] or not CF.Strategy['BSMCellularFlag']:
                            if timeit:
                                start = dt.now()
                            Algorithm.ChkRSERange(tbl.df, CF)
                            if timeit:
                                timeval['ChkRSERange'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds  * 0.000001)

                        if timeit: 
                            start = dt.now() 
                        Algorithm.PSNCheck(tbl.df, tp, RandomGen, CF)
                        if timeit: 
                            timeval['PSNCheck'] += (dt.now() - start).seconds + ((dt.now() - start).microseconds * 0.000001)

                        #Go through vehicles and change the color if a snapshot is generated
                        if changecolor:                          
                            color_display_time = CF.Control['ColorDisplayDuration']

                            for vehicle in vehicles:                                
                                select = (tbl.df['vehicle_ID'] == vehicle.ID)

                                diff_time = tbl.df['time_of_start_snapshot'][select] - tp + color_display_time     

                                if (tbl.df['BSM_equipped'][select]):
                                    vehicle.setColor(0,0,255)   #Change BSM vehicles to blue

                                elif (tbl.df['time_of_start_snapshot'][select] - tp + color_display_time > 0):
                                    vehicle.setColor(50,205,50)   #Change color to green

                                elif (tbl.df['time_of_last_stop'][select] - tp + color_display_time + 3 > 0):
                                    vehicle.setColor(255,69,0)   #Change color to orange

                                elif (tbl.df['PDM_equipped'][select] and tbl.df['time_of_last_transmit'][select] - tp + color_display_time > 0):
                                    vehicle.setColor(0,0,0) #Change to black

                                elif (tbl.df['time_of_periodic_snapshot'][select] - tp + color_display_time > 0):
                                    vehicle.setColor(138,43,226)    #Change color to purple

                                else :
                                    vehicle.setColor(224,255,255) #Change color to white

                        LastTP = tp

        except:
            raise
            time.sleep(10)




#----------------------------------------------------------------------
    def ClearoldData(self):
        #clears old data in output files
        with open(self.OutputFile, 'w') as f:
            f.write("VISSIM Output\n")
#----------------------------------------------------------------------

def tca_v(inputf = 'code/TCAinput.xml'):

    global timeit
    global timeval
    global vissimtimeit
    global changecolor

    timeit = True
    vissimtimeit = False #True: time VISSIM without the TCA running.
    changecolor = True

    total_list = []

    if timeit:
        timeval = {
            'Update Table' : 0,
            'CheckSnapshot' : 0,
            'CheckCellular' : 0,
            'ChkRSERange' : 0,
            'PSNCheck' : 0,}
    try:

        global tbl
        global LastTP
        global CF
        global RandomGen
        global Algorithm
        global output


        LastTP = 0
        if len(sys.argv) == 2:
            inputf = sys.argv[1]
        CF = ControlFiles(inputf, TCA_version = 'vissim')
        CF.Load_files()

        output = TCA_Output(CF)

        RandomGen = Random_generator(CF.Control['Seed'])
        RandomGen.add_generator_range('GapDistance', CF.Strategy["GapMinDistance"], CF.Strategy["GapMaxDistance"])
        RandomGen.add_generator_range('GapTimeout', CF.Strategy["GapMinTime"], CF.Strategy["GapMaxTime"])
        RandomGen.add_generator_range('psn', 0, 32767)  #range based on J2735
        RandomGen.add_generator_range('LossPercent', 1, 100)

        Algorithm = TCA_Algorithm(CF)

        tbl = DataStorage(list(xrange(10000)), [], [])

        app = C2X_tca(CF.Control["OutputLevel"])
        totaltimestart = dt.now()
        app.run()
                    
        if not vissimtimeit:
            
            for ID in Algorithm.BSMBuffer.ActiveBuffers.keys():
                Algorithm.BSMBuffer.ClearBuffer(ID, LastTP + 2, Algorithm.BSMs, 2, -1, -1)
            output.WriteBSMList(Algorithm.BSMs, CF)

            for ID in Algorithm.SSBuffer.ActiveBuffers.keys():
                Algorithm.SSBuffer.ClearBuffer(ID, LastTP + 2, Algorithm.Snapshots, 2, -1, -1)
            output.WriteSSList(Algorithm.Snapshots, CF)
        
        totaltime = ((dt.now() - totaltimestart).seconds) + ((dt.now() - totaltimestart).microseconds * 0.000001)
        if timeit:
            with open('timeit.csv', 'wb') as time_f:
                for k, v in timeval.iteritems():
                    time_f.write(k +  "," +  str(v) + '\n')
                time_f.write('Total Runtime (seconds):,' + str(totaltime))

        if vissimtimeit:
            with open('vissimtimeit.csv', 'wb') as time_f:
                time_f.write('Total Run time (seconds):,' + str(totaltime))


    except BaseException, e:
        print str (e)
        raise
        time.sleep(4)
    except:
        time.sleep(4)


#----------------------------------------------------------------------


if __name__ == "__main__":
    tca_v()