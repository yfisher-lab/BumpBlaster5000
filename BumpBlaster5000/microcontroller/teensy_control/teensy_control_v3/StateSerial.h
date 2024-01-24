#ifndef STATESERIAL_H
#define STATESERIAL_H


#include "Arduino.h"

class StateSerial {
    char chars[256];
    bool new_data = false;
    int cmd_index = 0;
    
    int data_rcvd_timestamp;

    Stream& srl;

    public:
        double val_arr[1024]; //204 points
        int cmd = 0;
        int cmd_len = 0;
        bool new_cmd = false;

        int data_rcvd_timestamp = -1;

        StateSerial(Stream& srl_ref);
        void recv_data();
        void read_state();
}



#endif STATESERIAL_H