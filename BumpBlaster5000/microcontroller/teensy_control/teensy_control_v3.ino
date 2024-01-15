// State reading variables
#include <cstring>
#include "Trigger/Trigger.h"
#include <Wire.h>
#include <Adafruit_MCP4725.h>


#define BKSERIAL Serial6 // update to current pin settings

void setup() {
  // put your setup code here, to run once:

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
    execute_state();
    ft::process_serial_data();
    ft::update_dacs();
    check_pins();
}


//Bruker Triggers
struct {
    Trigger trig(3,10);
    static bool is_scanning;
} bk_scan;
bk_scan.is_scanning = false;

Trigger bk_opto_trig(4,10);
Trigger pump_trig(5,10);


const int num_chars = 256;
namespace state_ns {
    static char chars[num_chars];
    static bool new_state = false;
    static int cmd_index = 0;
    int val_arr[1024]; // 204 points can be initialized

    static cmd = 0;
    static int cmd_len = -1000;

    static int data_rcvd_timestamp;


    void recv_data() { // receive USB1 data, ov
        static byte ndx = 0; // buffer index
        static char delimiter = ','; // column delimiter
        static char endline = '\n'; // endline character
        char curr_byte; // current byte;
        

        if (SerialUSB1.available() > 0){
            timestamp = millis();
            curr_byte = SerialUSB1.read();
            if ((rc == endline) | (rc==delimiter)) { // end of frame or new column
                chars[ndx] = '\0'; // terminate string
                ndx = 0;
                new_state = true;
            } 
            else {
                chars[ndx] = rc;
                ndx++;
                if (ndx >= num_chars) {
                    ndx = num_chars - 1;
                } 
            }
        }
    }

    void state_machine() {
        static int msg_timeout = 1000;
        static int begin_msg_timestap = -1; 
        static int curr_msg_timestamp;

  
  
        recv_data();
        if (new_state) {
            if (cmd_index==0) { // first value is the length of the state machine message
                cmd_len = atoi(chars);
                begin_msg_timestamp = millis();
            } 
            else if (index == 1) { // second value is the state to go to in state machine
                cmd = atoi(chars);
            }
            else { // the remaining value are parameters specific to the state
                val_arr[cmd_index-2] = atoi(chars);
            }
            
            cmd_index +=1; // update index
            if ((cmd_index-2) == cmd_len) { // if reached end of state machine message
                begin_msg_timestamp=-1;
                execute_state(cmd, cmd_len);
                cmd_index = 0;
            }
            new_state = false;
        }

        if (((data_rcvd_timestamp-begin_msg_timestamp)>msg_timeout)
             & (begin_msg_timestamp>0)) { // if command isn't read before timeout
            //abort 
            cmd = 5; // return to closed loop
            cmd_len = 0;
            begin_msg_timestamp = -1;
        }        
    }
}



namespace ft {
    static bool closed_loop = false;
    static char chars[num_chars]; 
    static bool new_data = false;
    static int buff_ndx=0;
    static double heading;

    static double heading_offset;

    static int current_frame = 0;
    const int frame_pin = 2; 

    const int max_dac_val = 4095;
    const int num_cols = 26; 

    static int col;
    static int curr_time;

    Adafruit_MCP4725 heading_dac;
    Adafruit_MCP4725 index_dac;
    namespace dac_countdown {
        namespace heading {
            static bool on_delay = true;
            static int delay = 100;
            static int timestamp;
            static double heading;
        }

        namespace index {
            static bool on_delay = true;
            static int delay = 100;
            static int timestamp;
            static double index;
        }
    }
    
    void process_serial_data(){
        execute_col();
        if (closed_loop) {
            heading = fmod(ft_heading + heading_offset, 2*PI);
        } 
    }

    void update_dacs() {
        // check on delay timers
        curr_time = millis();
        if (dac_countdown::heading::on_delay ) {
            if (curr_time > (dac_countdown::heading::timestamp + dac_countdown::heading::delay)) {
                heading = dac_countdown::heading::heading
                dac_countdown::heading::on_delay = false;
            }
        }

        if (dac_countdown::index::on_delay) {
            if (curr_time > (dac_countdown::index::timestamp + dac_countdown::index::delay)) {
                index = dac_countdown::index::index;
                dac_countdown::index::on_delay = false;
            }
        }

        //  set dac vals
        heading_dac.setVoltage(int(max_dac_val * heading/2/PI ), false);
        index_dac.setVoltage(int(index), false);
    }


    void execute_col() {
        recv_data(); 
        if (ft_new_data == true) {
            update_col();
            col = (col+1) % num_cols; // keep track of columns in fictrack  
            new_data = false;
        }
    }

    void recv_data() { // receive Fictrac data
    
        static byte ndx = 0; // buffer index
        static char delimiter = ','; // column delimiter
        static char endline = '\n'; // endline character
        static char curr_byte; // current byte

        static _col_tmp;

        if (Serial.available() > 0) { // cannot use while(Serial.available()) because Teensy will read all 
            curr_byte = Serial.read(); 
            if ((curr_byte == endline)|(curr_byte==delimiter)) { // end of frame or new column      
                chars[ndx] = '\0'; // terminate the string
                ndx = 0; // restart buffer index
                new_data = true;   // cue new data

                if (curr_byte == endline) { // checks that columns are being counted correctly
                    int _col_tmp = col + 1;
                    if (_col_tmp != (num_cols)) {
                        col_ndx = num_cols-1;
                    }
                }
            }
            else {
                chars[ndx] = rc;
                ndx++;
                if (ndx >= num_chars) {
                    ndx = num_chars - 1;
                } 
            }
        }
    }

    void update_col() {

        // switch case statement for variables of interest
        switch (col) {
            
            case 0: // new FicTrac frame
                // flip ft pin high
                digitalWriteFast(frame_pin,HIGH);
                break;

            case 1: // frame counter
                current_frame = atoi(chars);
                break;

            case 17: // heading 
                // flip ft pin low 
                digitalWriteFast(frame_pin,LOW);

                // update heading pin
                ft_heading = atof(chars) + PI;
                break;
        }
    }

    void set_heading(int h) {
        heading = h;
    }

    void set_index(int i) {
        index = i;
    }

    void set_heading_offset(double o) {
        heading_offset = o;
    }

    void rotate_scene(double r) {
        heading_offset = fmod(heading_offset + r, 2*PI);
    }

    int get_index() {
        return index;
    }

    void set_index(int i) {
        index = i;
        // index = min(max(index, 0), max_dac_val);
    }

    void set_heading_on_delay(int t, double h){
        dac_countdown::heading::on_delay = true;
        dac_countdown::heading::delay = t;
        dac_countdown::heading::timestamp = millis();
        dac_countdown::heading::heading = h;
    }

    void set_index_on_delay(int t, int i ) {
        dac_countdown::index::on_delay = true;
        dac_countdown::index::delay = t;
        dac_countdown::index::timestamp = millis();
        dac_countdown::index::index = i;
    }

}


namespace vis_opto_ns {

    static bool on_multi_point = false;
    static int n_points;
    static int curr_point = 0; 
    static int next_point_time;
    static int curr_point_time;

    int start_ind;
    bool pts_complete;


    const int pnt_len = 5;

    static int point_start_time = -1;

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

    void run_point() {
        const int _h;
        const int _i;
        const int _opto_bool;
        const int _opto_delay;
        
        start_ind = curr_point*pnt_len;
        _h = state_ns::val_arr[start_ind];
        _i = state_ns::val_arr[start_ind + 1];
        _opto_bool = state_ns::val_arr[start_ind + 2];
        _opto_del = state_ns::val_arr[start_ind + 3];

        next_point_millis = state_ns::val_arr[start_ind + 4];

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
            
            ft::set_heading_on_delay(_-1*_opto_delay);
            ft::set_index_on_delay(-1*_opto_delay);
        }
    }
    
    
    void check_for_next_point() {
        static int curr_time;
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

    static bool on_multi_point = false;
    static int n_points;
    static int curr_point = 0; 
    static int next_point_time;
    static int curr_point_time;

    int start_ind;
    bool pts_complete;


    const int pnt_len = 5;

    static int point_start_time = -1;

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

    void run_point() {
        const int _h;
        const int _i;
        const int _opto_bool;
        const int _opto_delay;
        
        start_ind = curr_point*pnt_len;
        _h = state_ns::val_arr[start_ind];
        _i = state_ns::val_arr[start_ind + 1];
        _opto_bool = state_ns::val_arr[start_ind + 2];
        _opto_del = state_ns::val_arr[start_ind + 3];

        next_point_millis = state_ns::val_arr[start_ind + 4];

        if (_opto_delay>=0) {
            trig_pump();
            
            if (_opto_bool>0) {
                opto_trig.trigger_on_delay(_opto_delay);
            }
            
        } else {
            
            if (_opto_bool>0) {
                opto_trig.trigger();
            }
            
            pump_trig::trigger_on_delay(-1*_opto_delay);
        }
    }
    
    
    void check_for_next_point(int curr_time) {
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
        ft::set_heading(ft::val_arr[0], false);
        break;

    case 7: // set index_dac value
        ft::set_index(ft::val_arr[0]); 
        break;

    case 8: // set heading and index dac
        ft::set_heading(val_arr[0]);
        ft::set_index(val_arr[1]);
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

  digitalWriteFast(bk_opto_trig_pin, HIGH);
  bk_opto_trig_state = true;
  bk_opto_trig_timestamp = millis();


  SerialUSB2.print("opto, "); // opto trigger rising edge Fictrac frame
  SerialUSB2.print(ft::current_frame);
  SerialUSB2.print('\n');
}

void trig_pump() {

  digitalWriteFast(pump_trig_pin, HIGH);
  pump_trig_state = true;
  pump_trig_timestamp = millis();

  SerialUSB2.print("pump, ");
  SerialUSB2.print(ft::current_frame);
  SerialUSB2.print('\n');
}


void check_pins() {
  
  // flip start down
  int curr_timestamp = millis();
  if (bk_scan.trig.state & ((curr_timestamp - bk_scan.trig.timestamp) > bk_scan.trig.timeout)) {
    if (bk_scan.is_scanning) { // if this is a start scan trigger
      SerialUSB2.print("start_trig_falling_edge, "); // start trigger falling edge Fictrac frame
      SerialUSB2.print(ft::current_frame);
      SerialUSB2.print('\n');
    }
    
    bk_scan.trig.check(curr_timestamp);
  }

  // flip opto trigger down
  bk_opto_trig.check(curr_timestamp);

  // flip opto trigger down
  pump_trig.check(curr_timestamp);
  

  // flip opto up after specified delay
  vis_opto_ns::check_for_next_point(curr_timestamp);
  pump_opto_ns::check_for_next_point(curr_timestamp);

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
