#ifdef __cplusplus
extern "C" {
#endif
#include "python.h"
static PyObject *color_sendVehicleInfo(PyObject *);
void trialColorVeh();
void callPyFunc(VEHICLE* vehicle);
void callPyFunc4AllVeh(PyObject , int );
void sendInfoToPy(int vID, double simTime, double vehSpeed, double locX, double locY, char* linkName);
int binary_search(int array[],int first,int last, int search_key);

#ifdef __cplusplus
} // closing brace for extern "C"
#endif