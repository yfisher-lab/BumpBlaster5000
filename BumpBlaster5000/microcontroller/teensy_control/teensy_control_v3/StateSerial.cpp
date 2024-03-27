#include "StateSerial.h"


StateSerial::StateSerial(Stream& srl_ref) : srl(srl_ref) {}

void StateSerial::recv_data() {
    static byte ndx = 0; // buffer index
    static char delimiter = ','; // column delimiter
    static char endline = '\n'; // endline character
    char curr_byte; // current byte;
    

    if (srl.available() > 0){
        data_rcvd_timestamp = millis();
        curr_byte = srl.read();
        if ((curr_byte == endline) | (curr_byte==delimiter)) { // end of frame or new column
            chars[ndx] = '\0'; // terminate string
            ndx = 0;
            new_data = true;
        } 
        else {
            chars[ndx] = curr_byte;
            ndx++;
            if (ndx >= num_chars) {
                ndx = num_chars - 1;
            } 
        }
    }
}

void StateSerial::read_state() {
    static int msg_timeout = 1000;
    static int begin_msg_timestamp = -1; 
 
    StateSerial::recv_data();
    if (new_data) {
//        SerialUSB2.println(cmd_index);
        if (cmd_index==0) { // first value is the length of the state machine message
            cmd_len = atoi(chars);
            begin_msg_timestamp = millis();
        } 
        else if (cmd_index == 1) { // second value is the state to go to in state machine
            cmd = atoi(chars);
        }
        else { // the remaining value are parameters specific to the state
            val_arr[cmd_index-2] = atof(chars);
        }
        
        cmd_index +=1; // update index
        if ((cmd_index-2) == cmd_len) { // if reached end of state machine message
            begin_msg_timestamp=-1;
//                execute_state(cmd, cmd_len);
            cmd_index = 0;
            new_cmd=true;
        }
        new_data = false;
    }

    if (((millis()-begin_msg_timestamp)>msg_timeout)
        & (begin_msg_timestamp>0)) { // if command isn't read before timeout
        //abort 
        cmd = 5; // return to closed loop
        cmd_len = 0;
        cmd_index = 0;
        begin_msg_timestamp = -1;
        SerialUSB2.println("Timeout");
        new_cmd=true;
    }        
}
