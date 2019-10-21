#standard
import os

from string import split,join
from operator import itemgetter
import unittest


class TCA_Output:

    def __init__(self, CF, Event_titles):
        self.SSoutfile = CF.Control["PDMTransFile"]
        self.Alloutfile = CF.Control["PDMAllFile"]
        self.BSMoutfile = CF.Control["BSMTransFile"]
        self.Event_titles = Event_titles
        self.ClearoldData()
        self.counter = 0
        self.BSMcounter = 0



#----------------------------------------------------------------------
    def WriteSSList(self, SSList, CV):
        if CV.Control["OutputLevel"] >= 2:
            print 'Writing',len(SSList),'snapshots to the output files: %s %s' % (self.SSoutfile,self.Alloutfile)

        with open(self.SSoutfile, "a") as f_out:
            with open(self.Alloutfile, "a") as f_outall:

                for SS in sorted(SSList, key=itemgetter('localtime', 'num', 'VID')):
                    self.counter = self.counter + 1
                    f_outall.write("%s,%d,%s,%d,%.2f,%.0f,%.0f,%s,%d,%s,%s,%s,%d\n" % (SS["VID"], int(SS["num"]),
                        SS["localtime"], int(SS["PSN"]), float(SS["spd"]),float(SS["x"]),float(SS["y"]),SS["lastRSE"],
                        int(SS["type"]), SS["transtime"], SS["transTo"], SS["deltime"], int(SS["delreason"])))
                    if int(SS["delreason"])==0 and SS["transtime"] != -1:
                        f_out.write("%s,%d,%.2f,%.0f,%.0f,%s,%s,%d,%d,%d\n" % (SS["localtime"], int(SS["PSN"]),
                        float(SS["spd"]),float(SS["x"]), float(SS["y"]), SS["transTo"], SS["transtime"],
                        SS["msg_num"], SS["ss_num"], int(SS['transmission_received_time'])))


#----------------------------------------------------------------------
    def ClearoldData(self):
        try:
            os.remove(self.BSMoutfile)
        except:
            pass

        #clears old data in output files
        with open(self.Alloutfile, 'w') as f:
            f.write("Veh_ID,SS_Num,Time_Taken,PSN,Speed,X,Y,Last_RSE,Type,Transmit_Time,"
                "Transmit_To,Delete_Time,Delete_Reason\n")

        with open(self.SSoutfile, 'w') as f:
            f.write("Time_Taken,PSN,Speed,X,Y,Transmit_To,Transmit_Time,Message #,Snapshot #,Received_Time\n")

#----------------------------------------------------------------------

class TCA_Output_Test(unittest.TestCase):

    def setUp(self):
        from TCALoadControl import ControlFiles
        self.CV = ControlFiles()
        self.CV.map_dictionary()
        self.CV.Control["PDMTransFile"] = 'test_delete_me_trans.csv'
        self.CV.Control["PDMAllFile"] = 'test_delete_me_all.csv'
        self.CV.Control["AccelColumn"] = None
        self.CV.Control["OutputLevel"] = 1

    def test_write_all(self):

        out = TCA_Output(self.CV, None)

        SSlist = []

        for x in range(30):

            transtime = -1

            SSlist.append({
                "Tnum" : x,
                "PSN" : '1234',
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
                "transTo" : -1,
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

        out = TCA_Output(self.CV, None)

        SSlist = []

        for x in range(30):

            transtime = -1

            if x % 2 == 0:
                transtime = 20

            SSlist.append({
                "Tnum" : x,
                "PSN" : '1234',
                "num" : x,
                "time" : 5,
                "localtime" : 5400,
                "VID" : 3453,
                "spd" : 34.2,
                "x" : 0.0,
                "y" : 1.0,
                "TransTolast" : 0,
                "type" :1,
                "transtime" : transtime,
                "transTo" : -1,
                "deltime": 0,
                "delreason": 0,
                "msg_num" : 3,
                "ss_num" : 3,
                "lastRSE" : 2,
                "transmission_received_time" : 1,
            })

        out.WriteSSList(SSlist, self.CV)
        with open('test_delete_me_trans.csv') as tst_all:
            c = 1
            for line in tst_all.readlines():
                c +=1
        assert c == 17 # half 30 plus with header and final /n



    def tearDown(self):
        import os
        os.remove('test_delete_me_trans.csv')
        os.remove('test_delete_me_all.csv')


if __name__ == '__main__':
    unittest.main()