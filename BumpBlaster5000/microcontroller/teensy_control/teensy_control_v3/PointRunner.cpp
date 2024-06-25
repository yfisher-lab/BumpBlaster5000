#include "PointRunner.h"

VisOptoPointRunner::VisOptoPointRunner(Trigger& _o_trig,
                                        FTHandler& _ft,
                                        StateSerial& _ss) : 
                                        opto_trig(_o_trig),
                                        ft(_ft),
                                        ss(_ss) { }

void VisOptoPointRunner::run_point() {

    static double _h;
    static int _i;
    static int _opto_bool;
    static int _opto_delay;

    curr_point_time = millis();
    start_ind = curr_point*pnt_len;
    _h = ss.val_arr[start_ind];
    _i = ss.val_arr[start_ind + 1];
    _opto_bool = ss.val_arr[start_ind + 2];
    _opto_delay = ss.val_arr[start_ind + 3];

    next_point_time = ss.val_arr[start_ind + 4];

    if (_opto_delay>=0) {
        ft.set_heading(_h);
        ft.set_index(_i);
        
        
        if (_opto_bool>0) {
            opto_trig.trigger_on_delay(_opto_delay);
        }
        
    } else {
        
        if (_opto_bool>0) {
            opto_trig.trigger();
        }
        
        ft.set_heading_on_delay(-1*_opto_delay, _h);
        ft.set_index_on_delay(-1*_opto_delay, _i);
    }
}


void VisOptoPointRunner::start_points() {
    n_points = ss.cmd_len/pnt_len;
    pts_complete = false;

    if (n_points==0) {
        pts_complete = true;
    }
    point_start_time = millis();
    curr_point = 0;
    if (!pts_complete){
        VisOptoPointRunner::run_point();  
    }
}


void VisOptoPointRunner::check_for_next_point(int curr_time) {
    if (!pts_complete) {
        if (curr_time>(curr_point_time+next_point_time)) {
            curr_point++;
            if (curr_point == n_points) {
                pts_complete=true;
            } else {
                curr_point_time = curr_time;
                VisOptoPointRunner::run_point();
            }
        }
    }
}


void VisOptoPointRunner::abort_points() {
    pts_complete = true;
}


PumpOptoPointRunner::PumpOptoPointRunner(Trigger& _o_trig,
                                        Trigger& _p_trig,
                                        StateSerial& _ss) : 
                                        opto_trig(_o_trig),
                                        pump_trig(_p_trig),
                                        ss(_ss) {   

}

void PumpOptoPointRunner::run_point() {
    static int _opto_bool;
    static int _opto_delay;

    curr_point_time=millis();

    start_ind = curr_point*pnt_len;
   
    _opto_bool = ss.val_arr[start_ind + 2];
    _opto_delay = ss.val_arr[start_ind + 3];

    next_point_time = ss.val_arr[start_ind + 4];

    if (_opto_delay>=0) {
        pump_trig.trigger();
        
        if (_opto_bool>0) {
            opto_trig.trigger_on_delay(_opto_delay);
        }
        
    } else {
        
        if (_opto_bool>0) {
            opto_trig.trigger();
        }
        pump_trig.trigger_on_delay(-1*_opto_delay);
    }

}


void PumpOptoPointRunner::start_points() {
    n_points = ss.cmd_len/pnt_len;
       pts_complete = false;

       if (n_points==0) {
           pts_complete = true;
       }
       point_start_time = millis();
       curr_point = 0;
       if (!pts_complete){
           PumpOptoPointRunner::run_point();  
       }
}

void PumpOptoPointRunner::check_for_next_point(int curr_time) {
    if (!pts_complete) {
        if (curr_time>(curr_point_time+next_point_time)) {
            curr_point++;
            if (curr_point == n_points) {
                pts_complete=true;
            } else {
                curr_point_time = curr_time;
                PumpOptoPointRunner::run_point();
            }
        }
    }
}
