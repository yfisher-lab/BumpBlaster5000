#ifndef POINTRUNNER_H
#define POINTRUNNER_H


#include "Arduino.h"
#include "Trigger.h"
#include "FTHandler.h"
#include "StateSerial.h"



class VisOptoPointRunner {
    bool on_multi_point = false;
    int n_points;
    int curr_point = 0;
    int next_point_time; 
    int curr_point_time;

    int start_ind;
    bool pts_complete;

    int pnt_len = 5;

    int point_start_time = -1;

    Trigger& opto_trig;
    FTHandler& ft;
    StateSerial& ss;

    public:
        VisOptoPointRunner(Trigger& _o_trig, FTHandler& _ft, StateSerial& _ss);
        void run_point();
        void start_points();
        void check_for_next_point(int curr_time);
        void abort_points();

}

class PumpOptoPointRunner {
    bool on_multi_point = false;
    int n_points; 

    int curr_point = 0;
    int next_point_time; 
    int curr_point_time;

    int start_ind;
    bool pts_complete;

    int pnt_len = 5;

    int point_start_time = -1;

    Trigger& opto_trig;
    Trigger& pump_trig;
    StateSerial& ss;

    public:
        PumpOptoPointRunner(Trigger& _o_trig, Trigger& _p_trig, StateSerial& _ss);
        void run_point();
        void start_points();
        void check_for_next_point(int curr_time);
        void abort_points();
}








#endif POINTRUNNER_H