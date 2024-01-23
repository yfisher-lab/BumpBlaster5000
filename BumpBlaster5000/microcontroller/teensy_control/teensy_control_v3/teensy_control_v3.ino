// State reading variables
#include <cstring>
#include "Trigger.h"
#include "FTHandler.H"
#include <Wire.h>
#include <Adafruit_MCP4725.h>


#define BKSERIAL Serial6 // update to current pin settings


//Bruker Triggers
struct {
    Trigger trig;
    bool is_scanning;
} bk_scan;

Trigger opto_trig;
Trigger pump_trig;



static int curr_time = 0;

namespace state_ns {
    static char chars[num_chars];
    static bool new_state = false;
    static int cmd_index = 0;
    int val_arr[1024]; // 204 points can be initialized

    static int cmd = 0;
    static int cmd_len = -1000;
    static bool new_cmd = false;

    static int data_rcvd_timestamp;


    void recv_data() { // receive USB1 data, ov
        static byte ndx = 0; // buffer index
        static char delimiter = ','; // column delimiter
        static char endline = '\n'; // endline character
        char curr_byte; // current byte;
        

        if (SerialUSB1.available() > 0){
            data_rcvd_timestamp = millis();
            curr_byte = SerialUSB1.read();
            if ((curr_byte == endline) | (curr_byte==delimiter)) { // end of frame or new column
                chars[ndx] = '\0'; // terminate string
                ndx = 0;
                new_state = true;
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

    void state_machine() {
        static int msg_timeout = 1000;
        static int begin_msg_timestamp = -1; 
//        static int curr_msg_timestamp;

  
  
        recv_data();
        if (new_state) {
            if (cmd_index==0) { // first value is the length of the state machine message
                cmd_len = atoi(chars);
                begin_msg_timestamp = millis();
            } 
            else if (cmd_index == 1) { // second value is the state to go to in state machine
                cmd = atoi(chars);
            }
            else { // the remaining value are parameters specific to the state
                val_arr[cmd_index-2] = atoi(chars);
            }
            
            cmd_index +=1; // update index
            if ((cmd_index-2) == cmd_len) { // if reached end of state machine message
                begin_msg_timestamp=-1;
//                execute_state(cmd, cmd_len);
                cmd_index = 0;
                new_cmd=true;
            }
            new_state = false;
        }

        if (((data_rcvd_timestamp-begin_msg_timestamp)>msg_timeout)
             & (begin_msg_timestamp>0)) { // if command isn't read before timeout
            //abort 
            cmd = 5; // return to closed loop
            cmd_len = 0;
            begin_msg_timestamp = -1;
            new_cmd=true;
        }        
    }
}

void setup() {
  // put your setup code here, to run once:

  bk_scan.is_scanning = false;
  bk_scan.trig.init(3, 10, false);

  opto_trig.init(4, 10, false);
  
  // Pump trigger setup
  pump_trig.init(5, 500, true);
  



  // FicTrac setup
  pinMode(ft::frame_pin,OUTPUT);
  digitalWrite(ft::frame_pin,LOW);
  

  // start DACs
  ft::heading_dac.begin(0x62,&Wire1);
  ft::index_dac.begin(0x63, &Wire1);


  BKSERIAL.begin(115200);
}


void yield() {} // get rid of hidden arduino yield function

FASTRUN void loop() { // FASTRUN teensy keyword
    state_ns::state_machine();
    if (state_ns::new_cmd) {
      execute_state();
    }
//    execute_state();
    ft::process_serial_data();
    ft::update_dacs();
    check_pins();
}





namespace vis_opto_ns {

//    static bool on_multi_point = false;
    static int n_points;
    static int curr_point = 0; 
    static int next_point_time;
    static int curr_point_time;

    int start_ind;
    bool pts_complete;


    const int pnt_len = 5;

    static int point_start_time = -1;

    void run_point() {
        static int _h;
        static int _i;
        static int _opto_bool;
        static int _opto_delay;
//        static int next_point_millis;
        
        start_ind = curr_point*pnt_len;
        _h = state_ns::val_arr[start_ind];
        _i = state_ns::val_arr[start_ind + 1];
        _opto_bool = state_ns::val_arr[start_ind + 2];
        _opto_delay = state_ns::val_arr[start_ind + 3];

        next_point_time = state_ns::val_arr[start_ind + 4];

        if (_opto_delay>=0) {
            ft::set_heading(_h);
            ft::set_index(_i);
            
            
            if (_opto_bool>0) {
                opto_trig.trigger_on_delay(_opto_delay);
            }
            
        } else {
            
            if (_opto_bool>0) {
                opto_trig.trigger();
            }
            
            ft::set_heading_on_delay(-1*_opto_delay, _h);
            ft::set_index_on_delay(-1*_opto_delay, _i);
        }
    }

    void start_points() {
        n_points = state_ns::cmd_len/pnt_len;
        pts_complete = false;

        if (n_points==0) {
            pts_complete = true;
        }
        point_start_time = millis();
        curr_point = 0;
        if (!pts_complete){
            run_point();  
        }
    }

    
    
    
    void check_for_next_point() {
        if (!pts_complete) {
            if (curr_time>(curr_point_time+next_point_time)) {
                curr_point++;
                if (curr_point == n_points) {
                    pts_complete=true;
                } else {
                    curr_point_time = curr_time;
                    run_point();
                }
            }
        }
    }

    void abort_points() {
        pts_complete = true;
    }

}


namespace pump_opto_ns {

//    static bool on_multi_point = false;
    static int n_points;
    static int curr_point = 0; 
    static int next_point_time;
    static int curr_point_time;

    int start_ind;
    bool pts_complete;


    const int pnt_len = 5;

    static int point_start_time = -1;

    void run_point() {
//        static int _h;
//        static int _i;
        static int _opto_bool;
        static int _opto_delay;
//        static int next_point_millis;
        
        start_ind = curr_point*pnt_len;
//        _h = state_ns::val_arr[start_ind];
//        _i = state_ns::val_arr[start_ind + 1];
        _opto_bool = state_ns::val_arr[start_ind + 2];
        _opto_delay = state_ns::val_arr[start_ind + 3];

        next_point_time = state_ns::val_arr[start_ind + 4];

        if (_opto_delay>=0) {
            trig_pump();
            
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
    
    void start_points() {
        n_points = state_ns::cmd_len/pnt_len;
        pts_complete = false;

        if (n_points==0) {
            pts_complete = true;
        }
        point_start_time = millis();
        curr_point = 0;
        if (!pts_complete){
            run_point();  
        }
    }

   
    
    void check_for_next_point() {
        if (!pts_complete) {
            if (curr_time>(curr_point_time+next_point_time)) {
                curr_point++;
                if (curr_point == n_points) {
                    pts_complete=true;
                } else {
                    curr_point_time = curr_time;
                    run_point();
                }
            }
        }
    }

    void abort_points() {
        pts_complete = true;
    }

}




void execute_state() {

  switch(state_ns::cmd){
    case 0: // do nothing
      break;
    case 1: // flip start scan trigger high
        if (!bk_scan.is_scanning) {
            bk_scan.trig.trigger();
            bk_scan.is_scanning = true;

            SerialUSB2.print("start, "); // start trigger falling edge Fictrac frame
            SerialUSB2.print(ft::current_frame);
            SerialUSB2.print('\n');
        }
        break;
    case 2: // kill scan
        if (bk_scan.is_scanning) {
            bk_scan.trig.trigger();
            bk_scan.is_scanning = false; 
            
            SerialUSB2.print("abort, "); // abort trigger rising edge Fictrac frame
            SerialUSB2.print(ft::current_frame);
            SerialUSB2.print('\n');
            // SerialUSB2.println("END QUEUE");

            // send kill scan signal to PrarieView API
            BKSERIAL.println("-Abort");
        }
        break;
    case 3: // flip opto scan trigger high
        trig_opto();
        break;

    case 4: // set heading pin to manual control (i.e. open loop)
        ft::closed_loop=false;
        break;
    
    case 5: // go back to closed loop 
        ft::closed_loop = true;
        break;

    case 6: // set heading_dac value
        ft::set_heading(state_ns::val_arr[0]);
        break;

    case 7: // set index_dac value
        ft::set_index(state_ns::val_arr[0]); 
        break;

    case 8: // set heading and index dac
        ft::set_heading(state_ns::val_arr[0]);
        ft::set_index(state_ns::val_arr[1]);
        break;

    case 9: // set heading and index dac, trigger opto with specified delay
      // heading, index, opto_bool, opto_delay
        vis_opto_ns::start_points();
        break;

    case 10: // run list of points
        // each point: heading, index, opto_bool, opto_delay, combined_dur
        vis_opto_ns::start_points();
        break;

    case 11: // kill list of points
        vis_opto_ns::abort_points();
        break;

    case 12: // trig pump
        trig_pump();
        break;

    case 13: // trig pump and opto with specified delay
        // opto_bool, opto_delay
        pump_opto_ns::start_points();
        break;
  }
}


void trig_opto() {
  opto_trig.trigger();

  SerialUSB2.print("opto, "); // opto trigger rising edge Fictrac frame
  SerialUSB2.print(ft::current_frame);
  SerialUSB2.print('\n');
}

void trig_pump() {
  pump_trig.trigger();

  SerialUSB2.print("pump, ");
  SerialUSB2.print(ft::current_frame);
  SerialUSB2.print('\n');
}


void check_pins() {
  
  // flip start down
  curr_time = millis();
  if (bk_scan.trig.pin_state() & ((curr_time - bk_scan.trig.get_timestamp()) > bk_scan.trig.get_timeout())) {
    if (bk_scan.is_scanning) { // if this is a start scan trigger
      SerialUSB2.print("start_trig_falling_edge, "); // start trigger falling edge Fictrac frame
      SerialUSB2.print(ft::current_frame);
      SerialUSB2.print('\n');
    }
    
    bk_scan.trig.check(curr_time);
  }

  // flip opto trigger down
  opto_trig.check(curr_time);

  // flip opto trigger down
  pump_trig.check(curr_time);
  

  // flip opto up after specified delay
  vis_opto_ns::check_for_next_point();
  pump_opto_ns::check_for_next_point();

}








// col 1 frame counter
// col 2-4 delta rotation vector (x,y,z) cam coords
// col 5 delta rotation error
// col 6-8 delta rotation in lab coordinates
// col 9-11 abs. rot. vector cam coords
// col 12-14 abs. rot. vector lab coords
// col 15-16 integrated x/y lab coords
// col 17 integrated heading lab coords
// col 18 movement direction lab coords (add col 17 to get world centric direction)
// col 19 running speed. scale by sphere radius to get true speed
// col 20-21 integrated x/y neglecting heading
// col 22 timestamp either position in video file or frame capture time
// col 23 sequence counter - usually frame counter but can reset is tracking resets
// col 24 delta timestep since last frame
// col 25 alt timestamp - frame capture time (ms since midnight)
