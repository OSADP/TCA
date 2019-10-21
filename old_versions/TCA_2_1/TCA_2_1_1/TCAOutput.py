#standard
from string import split,join
from operator import itemgetter
import unittest


class TCA_Output:

    def __init__(self, CV):
        self.SSoutfile = CV.Control["PDMTransFile"]
        self.Alloutfile = CV.Control["PDMAllFile"]
        self.BSMoutfile = CV.Control["BSMTransFile"]
        self.AllBSMoutfile = CV.Control["BSMExtendedFile"] 
        self.RSEFlag = CV.Strategy["RSEFlag"]
        self.ClearoldData
        self.counter = 0
        self.BSMcounter = 0
        self.ClearoldData()
#----------------------------------------------------------------------
    def WriteBSMList(self, BSMList, CV):
        if CV.Control["OutputLevel"] >= 2:
            print 'Writing',len(BSMList),'snapshots to the output file: %s' % (self.BSMoutfile)

        with open(self.BSMoutfile, "a") as f_out:
            with open(self.AllBSMoutfile, "a") as f_outall:
                for BSM in sorted(BSMList, key=itemgetter('localtime', 'num','VID')):
                    self.BSMcounter = self.BSMcounter + 1
                    if self.RSEFlag:
                        if CV.Control["BSMExtendedFlag"] and int(BSM["delreason"]) == 0:
                            f_outall.write("%s,%d,%s,%.2f,%.0f,%.0f,%.2f,%s,%d,%s,%s,%s,%d\n" % (BSM["Tnum"], int(BSM["num"]),
                                BSM["localtime"], float(BSM["spd"]),float(BSM["x"]),float(BSM["y"]), float(BSM["avg_accel"]),
                                BSM["lastRSE"],int(BSM["type"]), BSM["transtime"], BSM["transRSE"], BSM["deltime"], int(BSM["delreason"])))
                    else:
                        if CV.Control["BSMExtendedFlag"] and int(BSM["delreason"]) == 0:
                            f_outall.write("%s,%d,%s,%.2f,%.0f,%.0f,%.2f,%d,%s,%s,%s,%d\n" % (BSM["Tnum"], int(BSM["num"]),
                                BSM["localtime"], float(BSM["spd"]),float(BSM["x"]),float(BSM["y"]), float(BSM["avg_accel"]), 
                                int(BSM["type"]), BSM["transtime"], BSM["transRSE"], BSM["deltime"], int(BSM["delreason"])))
                    if int(BSM["delreason"]) == 0:
                        f_out.write("%s,%d,%d,%d,%s,%.2f,%.2f,%.2f,%.2f,\n" % (BSM["Tnum"], int(BSM["num"]),
                            int(BSM["msg_num"]), int(BSM["ss_num"]), BSM["localtime"], float(BSM["x"]),
                            float(BSM["y"]), float(BSM["spd"]), float(BSM["avg_accel"])))

#----------------------------------------------------------------------
    def WriteSSList(self, SSList, CV):
        if CV.Control["OutputLevel"] >= 2:
            print 'Writing',len(SSList),'snapshots to the output files: %s %s' % (self.SSoutfile,self.Alloutfile)

        with open(self.SSoutfile, "a") as f_out:
            with open(self.Alloutfile, "a") as f_outall:

                for SS in sorted(SSList, key=itemgetter('localtime', 'num', 'VID')):
                    self.counter = self.counter + 1
                    if self.RSEFlag:
                        f_outall.write("%s,%d,%s,%d,%.2f,%.0f,%.0f,%s,%d,%s,%s,%s,%d\n" % (SS["Tnum"], int(SS["num"]),
                            SS["localtime"], int(SS["VID"]), float(SS["spd"]),float(SS["x"]),float(SS["y"]),SS["lastRSE"],
                            int(SS["type"]), SS["transtime"], SS["transRSE"], SS["deltime"], int(SS["delreason"])))
                    else:
                        f_outall.write("%s,%d,%s,%d,%.2f,%.0f,%.0f,%d,%s,%s,%s,%d\n" % (SS["Tnum"], int(SS["num"]),
                            SS["localtime"], int(SS["VID"]), float(SS["spd"]),float(SS["x"]),float(SS["y"]),
                            int(SS["type"]), SS["transtime"], SS["transRSE"], SS["deltime"], int(SS["delreason"])))
                    if int(SS["delreason"])==0 and SS["transtime"] != -1:
                        f_out.write("%s,%d,%.2f,%.0f,%.0f,%s,%s,%d,%d,%d\n" % (SS["localtime"], int(SS["VID"]),
                        float(SS["spd"]),float(SS["x"]), float(SS["y"]), SS["transRSE"], SS["transtime"],
                        SS["msg_num"], SS["ss_num"], int(SS['transmission_received_time'])))


#----------------------------------------------------------------------
    def ClearoldData(self):
        #clears old data in output files
        if self.RSEFlag:
            with open(self.Alloutfile, 'w') as f:
                f.write("Veh_ID,SS_Num,Time_Taken,PSN,Speed,X,Y,Last_Transmitted_To,Type,Transmit_Time,"
                    "Transmit_To,Delete_Time,Delete_Reason\n")
            with open(self.AllBSMoutfile, 'w') as f:
                f.write("Veh_ID,SS_Num,Time_Taken,Speed,X,Y,Average_Accel,Last_Transmitted_To,Type,Transmit_Time,"
                    "Transmit_To,Delete_Time, Delete_Reason\n")

        else:
            with open(self.Alloutfile, 'w') as f:
                f.write("Veh_ID,SS_Num,Time_Taken,PSN,Speed,X,Y,Type,Transmit_Time,"
                    "Transmit_To,Delete_Time,Delete_Reason\n")
            with open(self.AllBSMoutfile, 'w') as f:
                f.write("Veh_ID,SS_Num,Time_Taken,Speed,X,Y,Average_Accel,Type,Transmit_Time,"
                    "Transmit_To,Delete_Time, Delete_Reason\n")


        with open(self.SSoutfile, 'w') as f:
            f.write("Time_Taken,PSN,Speed,X,Y,Transmit_To,Transmit_Time,Message #,Snapshot #,Received_Time\n")

        with open(self.BSMoutfile, 'w') as f:
            f.write("Veh_ID,SS_Num,Message #,Snapshot #,Time_Taken,X,Y,Speed,Average_Accel\n")

        



class TCA_Output_Test(unittest.TestCase):

    def setUp(self):
        from TCACore import  ControlVars
        self.CV = ControlVars()
        self.CV.Control["Trans_SS_Output_File"] = 'test_delete_me_trans.csv'
        self.CV.Control["SS_Output_File"] = 'test_delete_me_all.csv'
        self.CV.Control["Trans_BSM_Output_File"] = 'test_delete_me_trans_BSM.csv'
        self.CV.Strategy["BSMExtendedFlag"] = 0
        self.CV.Debugger = 1

    def test_write_all(self):

        out = TCA_Output(self.CV)

        SSlist = []

        for x in range(30):

            transtime = -1

            SSlist.append({
                "Tnum" : x,
                "num" : x,
                "time" : 5,
                "localtime" : 5400,
                "VID" : 3453,
                "spd" : 34.2,
                "x" : 0.0,
                "y" : 1.0,
                "lastRSE" : 0,
                "type" :1,
                "transtime" : transtime,
                "transRSE" : -1,
                "deltime": 0,
                "delreason": 0,
                "msg_num" : 3,
                "ss_num" : 3,
                "transmission_received_time" : 1,
            })


        out.WriteSSList(SSlist, self.CV)
        with open('test_delete_me_all.csv') as tst_all:
            c = 1
            for line in tst_all.readlines():
                c +=1
        assert c == 32 # with header and final /n


    def test_write_trans(self):

        out = TCA_Output(self.CV)

        SSlist = []

        for x in range(30):

            transtime = -1

            if x % 2 == 0:
                transtime = 20

            SSlist.append({
                "Tnum" : x,
                "num" : x,
                "time" : 5,
                "localtime" : 5400,
                "VID" : 3453,
                "spd" : 34.2,
                "x" : 0.0,
                "y" : 1.0,
                "lastRSE" : 0,
                "type" :1,
                "transtime" : transtime,
                "transRSE" : -1,
                "deltime": 0,
                "delreason": 0,
                "msg_num" : 3,
                "ss_num" : 3,
                "transmission_received_time" : 1,
            })

        out.WriteSSList(SSlist, self.CV)
        with open('test_delete_me_trans.csv') as tst_all:
            c = 1
            for line in tst_all.readlines():
                c +=1
        assert c == 17 # half 30 plus with header and final /n


    def test_write_trans_BSM(self):

        out = TCA_Output(self.CV)

        BSMlist = []

        for x in range(30):

            BSMlist.append({
                "Tnum" : x,
                "VID" : 3453,
                "num" : x,
                "localtime" : 5400,
                "spd" : 34.2,
                "x" : 0.0,
                "y" : 1.0,
                "lastRSE" : 0,
                "type" : 4,
                "deltime": 0,
                "delreason": 0,
                "msg_num" : 3,
                "ss_num" : 3,
                "avg_accel" : 4.3,
                "heading" : 4.33,
            })

        out.WriteBSMList(BSMlist, self.CV)
        with open('test_delete_me_trans_BSM.csv') as tst_BSM_trans:
            c = 1
            for line in tst_BSM_trans.readlines():
                c += 1
        assert c == 32



    def tearDown(self):
        import os
        os.remove('test_delete_me_trans.csv')
        os.remove('test_delete_me_all.csv')
        os.remove('test_delete_me_trans_BSM.csv')


if __name__ == '__main__':
    unittest.main()