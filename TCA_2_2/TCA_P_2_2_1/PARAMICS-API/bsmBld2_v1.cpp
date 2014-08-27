/* -----------------------------------------------------------------------
 * Paramics Programmer API    (paramics-support@quadstone.com)
 * Quadstone Ltd.             Tel: +44 131 220 4491
 * 16 Chester Street          Fax: +44 131 220 4492
 * Edinburgh, EH3 7RA, UK     WWW: http://www.paramics-online.com
 * ----------------------------------------------------------------------- */  

#include <iostream>
#include <cstdlib>
#include <string>
#include <new>
#include <cmath>
#ifdef __cplusplus
extern "C" {
#endif

#include <stdio.h>
//#include <string.h>
#include <math.h>
#include "programmer.h"
#include "bsmBld1.h"
#include <io.h>
#include <time.h>

#ifdef __cplusplus
} // closing brace for extern "C"
#endif

#include <python.h>
#include <boost/python.hpp>

using namespace std;
using namespace boost::python;

static char		*networkPath;
FILE *g_LogFile = NULL;
int wholeSecond =0;

typedef struct vehicleInfo_s vehicleInfo; 
struct vehicleInfo_s
{
	int vehicleID;
	double speed;
	double accel;
	double time;
	double locX;
	double locY;
	char linkName[10];
	long color;
	int vehType;
};
//vehicleInfo* g_vI;
vehicleInfo g_vI[1000];
int* g_vehIDs  = NULL;
static int numVehicles;
int cumuVehCount;
int vehCount;
//char* pyPath;
static char pyPath[50];
int numVehInNet = 0;
short int simStarting = 1;

PyObject *pVehInfo, *pVehNumList;
PyObject *pSuperTuple;

PyObject *pySys;
PyObject *pyOut;
FILE *fErrOut;
object sys ;
list path ;
object moduTest;
object name_space;
list vehList;
list vehColorList;
PyObject *pValue;

clock_t g_init, g_final;

int errLn = 0;
// decode a Python exception into a string
std::string handle_pyerror2(int ln)
{

    std::ostringstream os;
    os << "@ ln %d Python error:\n  " << ln << std::flush;

    PyObject *type = 0, *val = 0, *tb = 0;
    PyErr_Fetch(&type, &val, &tb);
    handle<> e_val(val), e_type(type), e_tb(allow_null(tb));

    try {
        object t = extract<object>(e_type.get());
        object t_name = t.attr("__name__");
        std::string typestr = extract<std::string>(t_name);

        os << typestr << std::flush;
    } catch (error_already_set const &) {
        os << "Internal error getting error type:\n";
        PyErr_Print();
    }

    os << ": ";

    try {
        object v = extract<object>(e_val.get());
        std::string valuestr = extract<std::string>(v.attr("__str__")());
        os  << valuestr << std::flush;
    } catch (error_already_set const &) {
        os << "Internal error getting value type:\n";
        PyErr_Print();
    }

    if (tb) {
        try {
            object tb_list = import("traceback").attr("format_tb")(e_tb);
            object tb_str = str("").attr("join")(tb_list);
            std::string str = extract<std::string>(tb_str);

            os << "\nTraceback (recent call last):\n" << str;
        } catch (error_already_set const &) {
            os << "Internal error getting traceback:\n";
            PyErr_Print();
        }
    } else {
        os << std::endl;
    }

	//qps_GUI_printf("msg %s\n",os.str().c_str());

    return os.str();
}

// Called once after the network is loaded.
void qpx_NET_postOpen(void)
{
	char fullFileName[200];
//	PyObject *pySys;
//	PyObject *pyOut;
//	FILE *fErrOut;

	qps_GUI_printf("\nParamics Programmer API: Python runtime embedding\n");


	networkPath = qpg_NET_dataPath();

	//pyPath = (char*)calloc(50,sizeof(char));


	//pyPath = qpg_NET_dataPath();
	//	qps_GUI_printf("paths b4 @ %s %s\n",pyPath, networkPath);
	//strcpy(pyPath, networkPath);
	//strcat(pyPath, "/code/TCA2_test/");

		qps_GUI_printf("paths @ %s %s\n",pyPath, networkPath);

	strcpy(fullFileName, networkPath);
	strcat(fullFileName, "/");
	strcat(fullFileName, "LogFile");
	strcat(fullFileName,".txt");
	qps_GUI_printf("\nLog File 1:%s\n", fullFileName);
	g_LogFile = fopen(fullFileName, "w");

	numVehicles = 1000;

	qps_GUI_printf("mem alloc\n");
	//if(g_vI != NULL) delete[] g_vI;
	//g_vI = NULL;
	//g_vI = (vehicleInfo*)calloc(numVehicles,sizeof(vehicleInfo));
	//g_vI = new vehicleInfo[numVehicles];
	qps_GUI_printf("mem alloc1\n");
	if(g_vI == NULL) qps_GUI_printf("mem alloc1.25\n");

	cumuVehCount = 0;
	vehCount = 0;
	simStarting = 5;

	if(g_vehIDs != NULL) delete[] g_vehIDs;
	g_vehIDs = NULL;
	try{
	//g_vehIDs = (int*)malloc(numVehicles);
	qps_GUI_printf("mem alloc1.5\n");
	g_vehIDs = (int*)calloc(numVehicles,sizeof(int));
	//g_vehIDs = new int[1];
	if(g_vehIDs == NULL) qps_GUI_printf("mem alloc1.75\n");

	//		g_vehIDs = new int[10001];//,sizeof(int));
	}
	catch (std::bad_alloc& ba)
	{
		qps_GUI_printf("bad mem\n");//("bad_alloc caught:%s \n",ba.what.c_str());
	//std::cerr << "bad_alloc caught: " << ba.what() << '\n';
	}

//	g_vehIDs = (int*)malloc(numVehicles);//,sizeof(int));
	qps_GUI_printf("mem alloc2\n");
		qps_GUI_printf("numV %d\n",numVehicles);
	numVehicles = 1000;
	for(int i = 0; i < numVehicles; i++){
		g_vehIDs[i] = numVehicles;
		//qps_GUI_printf("1-%i\n",i);
		g_vI[i].vehicleID = 1000;
		//qps_GUI_printf("2-%d %d\n",i,g_vI[i].vehicleID);
	}

	qps_GUI_printf("before Py\n");
//	for(int i = 0; i < numVehicles; i++){
//		qps_GUI_printf("%d g_vI %d g_vehID %d\n",i,g_vI[i].vehicleID,g_vehIDs[i]);
//	}

	
	try
	{
		Py_Initialize();
	//pSuperTuple = PyTuple_New(1);
		qps_GUI_printf("Start Py interp\n");

		// Setup sys.path
	//    object sys = import("sys");
		sys = import("sys");
	//    list path = extract<list>(sys.attr("path"));
		path = extract<list>(sys.attr("path"));
		//sys.path.append("C:/Users/Public/paramics/data/BSM/colorTrial");
		path.append(";");
		//sys.path.append(";");
		//sys.path.append(pyPath);
		strcpy(pyPath, networkPath);
		strcat(pyPath, "/code/");
		path.append(string(pyPath));

		//std::string pathChar = extract<std::string >(path[1]);
		qps_GUI_printf("paths @ %s \n",pyPath);//,pathChar.c_str());
		//path.append("C:/Users/Public/paramics/data/BSM/colorDemo/code/TCA2_test");

		qps_GUI_printf("Start netw path\n");

		/*
		pySys = PyImport_ImportModule("sys");
		pyOut = PyFile_FromString("C:/Users/Public/paramics/data/BSM/colorTrial/errLog.txt", "w+");
		PyObject_SetAttrString(pySys, "stderr", pyOut);
		fErrOut = PyFile_AsFile(pyOut);*/

		// Import mytest
		moduTest = import("tcaP_b2");
		qps_GUI_printf("import pandas module\n");

		name_space = moduTest.attr("__dict__");
		qps_GUI_printf("get dict\n");

		vehList = list();
		vehColorList = list();

	}
    catch (error_already_set) 
    {
		std::string msg;
		if (PyErr_Occurred()) {
            msg = handle_pyerror2(errLn); 
			qps_GUI_printf("%s\n",msg.c_str());
        }
		boost::python::handle_exception();
        PyErr_Clear();
    }

	numVehicles = 1000;
		qps_GUI_printf("CPS %f numV %d\n",(double)CLOCKS_PER_SEC,numVehicles);
	for(int i = 0; i < numVehicles; i++){
		g_vehIDs[i] = numVehicles;
		g_vI[i].vehicleID = 1000;
		//qps_GUI_printf("2-%d %d\n",i,g_vI[i].vehicleID);
	}
	
    //exec_file("testPandas.py", name_space, name_space);
	//qps_GUI_printf("exec_file\n");

    //object MyFunc = name_space["vehTestPandas"];
	//qps_GUI_printf("get fn\n");
    //object result = MyFunc();


}

void qpx_NET_start()
{
	g_init = clock();
}

int binary_search(int array[],int first,int last, int search_key)
{
	int index;

	if (first > last)
		index = -1;

	else
	{
		int mid = (first + last)/2;

		if (search_key == array[mid])
			index = mid;
		else

		if (search_key < array[mid])
			index = binary_search(array,first, mid-1, search_key);
		else
			index = binary_search(array, mid+1, last, search_key);

	} // end if
	return index;
 }// end binarySearch
int compare (const void * a, const void * b)
{
  return ( *(int*)a - *(int*)b );
}

void qpx_VHC_timeStep(VEHICLE* vehicle)
{
	char fullFileName[200];
	int color=0, retVal = 0;
//	vehicleInfo vI;
	int* testPtr = NULL;

	int i, j, arrSize, n, vID, vIDIndex;
	float x1, y1, z1, b, g, locX, locY, simTime;

	clock_t init, final;
	//qps_GUI_printf("start pycall\n");


//	if(qpg_VHC_uniqueID(vehicle)%10 == 0)
//	if(wholeSecond == 1)
	simTime = qpg_CFG_simulationTime();
	//if(fmod(simTime,1) == 0)
	{
		init = clock();

		//qps_GUI_printf("pre tuple build\n");
		
		qpg_POS_vehicle(vehicle,qpg_VHC_link(vehicle),&x1,&y1,&z1,&b,&g);

		// Initialize vehicleInfo 
		if(cumuVehCount <= numVehicles)
		{
			errLn = 1;

			vID = qpg_VHC_uniqueID(vehicle);
			if (g_vI == NULL) qps_GUI_printf("g_vI null!\n");
			qsort(g_vehIDs,numVehicles,sizeof(int),compare);
			//qps_GUI_printf("2)g_vI %d-%d\n",g_vI[0].vehicleID,g_vI[1].vehicleID);
			qsort(g_vI,numVehicles,sizeof(vehicleInfo),compare);
			vIDIndex = binary_search(g_vehIDs,0,numVehicles-1,vID);

			//qps_GUI_printf("vIDIndex = %d for veh %d\n",vIDIndex,vID);
			if(vIDIndex < 0) i = cumuVehCount;
			else i = vIDIndex;

			g_vI[i].vehicleID = qpg_VHC_uniqueID(vehicle);
			g_vI[i].time = floor(100*(double)(qpg_CFG_simulationTime()-qpg_CFG_startTime()))/100;
			double histSpeed = g_vI[i].speed;

			if(g_vI[i].time > qpg_CFG_timeStep())
			{
				g_vI[i].accel = (qpg_VHC_speed(vehicle)-histSpeed)/qpg_CFG_timeStep();
				//qps_GUI_printf("SPD %f %f A %f\n",qpg_VHC_speed(vehicle),histSpeed,g_vI[i].accel);
			}
			else
				g_vI[i].accel = qpg_VHC_speed(vehicle)/qpg_CFG_timeStep();
			//qps_GUI_printf("ACC %f\n",g_vI[i].accel);

			g_vI[i].speed = qpg_VHC_speed(vehicle);
			g_vI[i].locX = -(x1 - fmod((double)x1, 0.01));
			g_vI[i].locY = y1 - fmod((double)y1, 0.01);
			//qps_GUI_printf("%d: x1 %.2f, %.2f\tloc %.2f, %.2f\n",g_vI[i].vehicleID,x1, y1, 
			//	g_vI[i].locX,g_vI[i].locY);
			strcpy(g_vI[i].linkName, qpg_LNK_name(qpg_VHC_link(vehicle)));

			g_vI[i].vehType = qpg_VHC_type(vehicle);

			g_vehIDs[i] = qpg_VHC_uniqueID(vehicle);

			//qps_GUI_printf("1)g_vI %d-%d of %d\n",g_vI[0].vehicleID,g_vI[1].vehicleID,numVehicles);

			if(vIDIndex < 0) {
				cumuVehCount++;
				vehCount++;
			}

			//qps_GUI_printf("assign veh info to struct\n\n");

			vID = qpg_VHC_uniqueID(vehicle);
			locX = x1 - fmod((double)x1, 0.01);
			locY = y1 - fmod((double)y1, 0.01);



		}


		wholeSecond = 0;

		final = clock() - init;
//		qps_GUI_printf("ts: %d\n",(int)(qpg_CFG_simulationTime()-qpg_CFG_startTime()));
//		qps_GUI_printf("dt VHC_tS: %f,%d\n", (double)final,(int)(qpg_CFG_simulationTime()-qpg_CFG_startTime()));

	}

}

void qpx_VHC_arrive(VEHICLE* vehicle, LINK* link, ZONE* zone)
{
	int i, vID, vIDIndex;

	vID = qpg_VHC_uniqueID(vehicle);

	qsort(g_vehIDs,numVehicles,sizeof(int),compare);
	qsort(g_vI,numVehicles,sizeof(vehicleInfo),compare);

	vIDIndex = binary_search(g_vehIDs,0,numVehicles-1,vID);

	if(vIDIndex < 0) i = cumuVehCount;
	else i = vIDIndex;

	g_vI[i].vehicleID = 0;
	g_vI[i].time = 0;
	g_vI[i].speed = 0;
	g_vI[i].accel = 0;
	g_vI[i].locX = 0;
	g_vI[i].locY = 0;
	strcpy(g_vI[i].linkName, "");
	g_vI[i].vehType = 0;

	g_vehIDs[i] = 0;

	if(vehCount > 0) vehCount--;
	//qps_GUI_printf("\nveehCount %d\n", vehCount);

}

void qpx_NET_timeStep()
{
	int i, j, arrSize, n;
	int *color;
	PyObject *netPath;// = PyImport_ImportModule("sys");
	PyObject *sysPath;// = PyObject_GetAttrString(sys, "path");

	int tempVID;
	VEHICLE *tempV;
	LINK *tempL;
	char fnArgs[25];
	char temp[10];
	PyObject *pySys;
	PyObject *pyOut;
	FILE *fErrOut;

	object moduTest;
	object name_space ;

	clock_t init, final;

	wholeSecond = 1;
	if(g_vI != NULL && cumuVehCount > 0)
	{
//		init = clock();

		vehList = list();


		try
		{
			// Import mytest
			moduTest = import("tcaP_b2");
			//qps_GUI_printf("import pandas module\n");

			name_space = moduTest.attr("__dict__");
			//qps_GUI_printf("get dict\n");

			errLn = 2;

		}
		catch (error_already_set) 
		{
			std::string msg;
			if (PyErr_Occurred()) {
				msg = handle_pyerror2(errLn); 
				qps_GUI_printf("%s\n",msg.c_str());
			}
			boost::python::handle_exception();
			PyErr_Clear();
		}

		if (moduTest != NULL)
		{
			//qps_GUI_printf("init module\n");

			name_space = moduTest.attr("__dict__");
			//qps_GUI_printf("get dict\n");

			//exec_file("testPandas.py", name_space, name_space);
			//qps_GUI_printf("exec_file\n");
			
			object startUpFn = name_space["start_up"];
			object vehColorFn = name_space["vehColorParseList"];
			object finishUpFn = name_space["finish_up"];
			//object finishUpFn = name_space["finish_up"];
			//qps_GUI_printf("get fn\n");
			//object result = MyFunc();

			if(startUpFn && vehColorFn && finishUpFn)
			{
				//qps_GUI_printf("fn exists \n");

				list oneVehList;
				try
				{
					for(i = 0; i < cumuVehCount; i++)
					{
						tempL = qpg_NET_link(g_vI[i].linkName);
						errLn = 3;

						if(tempL != NULL && g_vI[i].vehicleID > 0)
						{

							oneVehList = list();
							errLn = 4;
							//qps_GUI_printf("st list append\n");
							//qps_GUI_printf("veh ID to be appended %d to total %d veh\n",g_vI[i].vehicleID, vehCount);
							oneVehList.append((int)g_vI[i].vehicleID);
							//int dummyid = extract<int>((vehList)[0]);
							//qps_GUI_printf("list[0] %d\n",dummyid);
							oneVehList.append(g_vI[i].time);
							oneVehList.append(g_vI[i].speed);
							oneVehList.append(g_vI[i].accel);
							oneVehList.append(g_vI[i].locX);
							//qps_GUI_printf("list[1] %d \n",extract<int>((vehList)[1]));
							oneVehList.append(g_vI[i].locY);
							oneVehList.append(g_vI[i].linkName);
							oneVehList.append(g_vI[i].vehType);
							//qps_GUI_printf("en list append\n");
							vehList.append(oneVehList);
							
						}
					}

					final = clock() - init;
//					qps_GUI_printf("dt NET_sec list: %f,%d\n", (double)final,(int)(qpg_CFG_simulationTime()-qpg_CFG_startTime()));
					init = clock();
					
					//qps_GUI_printf("done list append for %d veh vehList len %d\n", vehCount,len(vehList));
				}
				catch (error_already_set) 
				{
					std::string msg;
					if (PyErr_Occurred()) {
						msg = handle_pyerror2(errLn); 
						qps_GUI_printf("ERR: %s\n",msg.c_str());
					}
					boost::python::handle_exception();					
				}

				//qps_GUI_printf("%s + %s = netwpath %s %s\n",string(networkPath).c_str(),string("/code").c_str(),(string(networkPath)+string("/code")).c_str(),string(pyPath).c_str());
				if(vehList)
				{
					try
					{
						if(simStarting){
							strcpy(pyPath, networkPath);
							strcat(pyPath, "/code/");
							//path.append(string(pyPath));
							//qps_GUI_printf("paths @ %s \n",pyPath);
							errLn = 5;
							startUpFn(string(pyPath).c_str());
							simStarting = 0;
							//qps_GUI_printf("aft startup\n");
						}
						//qps_GUI_printf("bef vehColorFn call\n");
						errLn = 6;/*
					for(i = 0; i < vehCount; i++)
					{
						oneVehList = extract<list>(vehList[i]); 
						errLn = 7;
						//std::string tempVListStr = extract<std::string > (oneVehList);
						qps_GUI_printf("one veh list len %d ",len(oneVehList));//,tempVListStr.c_str());
						for(j = 0; j < 8; j++){
							if(j < 1 ){ 
								int dummyid = extract<int>(oneVehList[j]);
								qps_GUI_printf("%d,",dummyid);
							}
							if(j == 1 || j == 2 || j == 4 || j == 5){ 
								float dummyac = extract<double>(oneVehList[j]);
								qps_GUI_printf(" %f,",dummyac);
							}
						}
						qps_GUI_printf("\n");
					}*/
						//if(qpg_NET_vehiclesSimulated()>0)
						{
						/// calling every ts
							errLn = 11;
							double tp = floor(100*(double)(qpg_CFG_simulationTime()-qpg_CFG_startTime()))/100;
							//qps_GUI_printf("2222222222 tp %f\n",tp);
							object ret = vehColorFn(vehList,tp);
							//qps_GUI_printf("aft fn call-1\n");
							vehColorList = extract<list>(ret);
							//qps_GUI_printf("aft fn call-2\n");
/*
							int numVehColored = len(vehColorList);
							
							for(i = 0; i < numVehColored; i++){

							int vehIDPy = extract<int> ((vehColorList)[i]);

							qps_GUI_printf("veh id py %d\n",vehIDPy);
							}
							*/
							

							
					final = clock() - init;
	//				qps_GUI_printf("dt NET_sec py ret: %f,%d\n", (double)final,(int)(qpg_CFG_simulationTime()-qpg_CFG_startTime()));
					init = clock();


							//list l(handle<>(borrowed(&ret)));
							//list_from_PyObject();
							//qps_GUI_printf("aft fn call\n");
							int vehColorID;
							std::string vehColorLinkChar, tempVListStr;
							int vehColor;
							int numItemsList = 4;
							int chkPDM;
							int numVehColored = len(vehColorList)/numItemsList;
							//qps_GUI_printf("numVehColored %d len(vehColorList) %d\n",numVehColored,len(vehColorList));

							//tempVListStr = extract<std::string > (vehColorList[0]);
							//qps_GUI_printf("tempvehColor %d\n",extract<int>((vehColorList)[0]));
							errLn = 12;
							for(i = 0; i < numVehColored; i++)
							{
								errLn = 13;
								for(j = 0; j < numItemsList; j++)
								{
									switch(j)
									{
										case 0:
											vehColorID = extract<int>((vehColorList)[numItemsList*i+j]);
											qps_GUI_printf("vID for veh %d from Py %d\n",i,vehColorID);
											break;
										case 1:
											vehColorLinkChar = extract<std::string > (vehColorList[numItemsList*i+j]);
											break;
										case 2:
											vehColor = extract<int> (vehColorList[numItemsList*i+j]);
											break;
										default:
											chkPDM = extract<int> (vehColorList[numItemsList*i+j]);
											//qps_GUI_printf("check PDM flag %d %f\n",chkPDM, tp);
									}
								}
								VEHICLE* vehColored = qpg_VHC_lookupV(qpg_NET_link((char*)vehColorLinkChar.c_str())
									, vehColorID);
								if(vehColored != NULL){ 
									switch(vehColor)
									{
										case 0:
											qps_DRW_vehicleColour(vehColored,API_BLUE);
											break;
										case 1:
											qps_DRW_vehicleColour(vehColored,API_GREEN);
											break;
										case 2:
											qps_DRW_vehicleColour(vehColored,API_ORANGE);
											break;
										case 3:
											qps_DRW_vehicleColour(vehColored,API_GREY1);
											break;
										case 4:
											qps_DRW_vehicleColour(vehColored,API_PURPLE);
											break;
										case 5:
											qps_DRW_vehicleColour(vehColored,API_WHITE);
											break;
										case 6:
											qps_DRW_vehicleColour(vehColored,API_LIGHTBLUE);
											break;
										case 7:
											qps_DRW_vehicleColour(vehColored,API_YELLOW);
											break;
										case 8:
											qps_DRW_vehicleColour(vehColored,API_DARKSEAGREEN);
											break;
										default:
											qps_DRW_vehicleColour(vehColored,API_WHITE);
									}
									qps_GUI_printf("@t=%f %f: vID %d color %d\n",qpg_CFG_simulationTime()-qpg_CFG_startTime(),tp,
										qpg_VHC_uniqueID(vehColored),vehColor);
								}
							}
	//								qps_GUI_printf("\n************\n\n");
							
						}
					}
					catch (error_already_set) 
					{
						std::string msg;
						if (PyErr_Occurred()) {
							msg = handle_pyerror2(errLn); 
							qps_GUI_printf("ERR: %s\n",msg.c_str());
						}
						boost::python::handle_exception();
						
					}
				}

				final = clock() - init;
//				qps_GUI_printf("dt NET_sec color: %f,%d\n", (double)final,(int)(qpg_CFG_simulationTime()-qpg_CFG_startTime()));
			
				/*
				if(qpg_CFG_duration() - qpg_CFG_simulationTime() <= qpg_CFG_timeStep())
				// last sec of simulation
				{
					qps_GUI_printf("bef finishup\n");
					// call finish_up from TCA-P module to clear the buffer for snapshots
					finishUpFn(qpg_CFG_simulationTime()-qpg_CFG_startTime());
					qps_GUI_printf("aft finishup\n");
				}*/
			}
			else
			{
				PyErr_Print();
				qps_GUI_printf("Cannot find Py fn!\n");
			}

			//fclose(fErrOut);
		}
		else
		{
			qps_GUI_printf("Module fail\n");
			fprintf(g_LogFile, "Py Module failed!\n");
			fflush(g_LogFile);
			//fclose(fErrOut);
		}

		//Py_Finalize();


	}
	//vehCount = 0;
}

void qpx_NET_complete()
{
	object moduTest;
	object name_space ;

	wholeSecond = 1;

	g_final = clock() - g_init;
	qps_GUI_printf("Total time taken: %f seconds for %d seconds of simulation\n", 
		(double)g_final/CLOCKS_PER_SEC,(int)(qpg_CFG_simulationTime()-qpg_CFG_startTime()));


}

void qpx_NET_close()
{
		try
		{
			// Import mytest
			moduTest = import("tcaP_b2");
			//qps_GUI_printf("import pandas module\n");

			name_space = moduTest.attr("__dict__");
			//qps_GUI_printf("get dict\n");

			object finishUpFn = name_space["finish_up"];
			errLn = 100;
			qps_GUI_printf("bef finishup\n");
			// call finish_up from TCA-P module to clear the buffer for snapshots
			finishUpFn(qpg_CFG_simulationTime()-qpg_CFG_startTime());
			qps_GUI_printf("aft finishup\n");
		}
		catch (error_already_set) 
		{
			std::string msg;
			if (PyErr_Occurred()) {
				msg = handle_pyerror2(errLn); 
				qps_GUI_printf("ERR: %s\n",msg.c_str());
			}
			boost::python::handle_exception();
		}
}

