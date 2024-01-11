// State reading variables
#include <cstring>
#include "Trigger"
#include "FTHandler"

const int num_chars = 256;
char state_chars[num_chars];
char _state_chars[num_chars];
bool new_state = false;
int state_index = 0;
int val_arr[1024]; // 204 points can be initialized 


// const int state_num_vals = 2;
const byte ft_frame_pin = 2; 
FTHandler ft_handler(ft_frame_pin);



//Bruker Triggers
struct {
    Trigger trig(3,10);
    bool is_scanning;
} bk_scan_trig;
bk_scan_trig.is_scanning = false;

Trigger bk_opto_trig(4,10);
Trigger pump_trig(5,10);


bool multiple_points = false;
int n_points;
int current_point;
int next_point_time;
int current_point_timestamp;

#define BKSERIAL Serial6 // update to current pin settings

void setup() {
  
  // FicTrac setup
  ft_handler.init(0x62, &Wire1, 0x63, &Wire1);
  // digital pins

  // Bruker setup
  bk_scan_trig.trig.init();
  bk_opto_trig.init();

  pump_trig.init();
  BKSERIAL.begin(115200);
  
}

void yield() {} // get rid of hidden arduino yield function

FASTRUN void loop() { // FASTRUN teensy keyword
    state_machine();
    ft_state();
    check_pins();
}



void state_machine() {
  static int state_cmd_len = -1000;
  static int cmd = 0;
  static int msg_timeout = 1000;
  int begin_msg_timestap = -1; 
  int curr_msg_timestamp;

  
  // static int val = 0;

  curr_msg_timestamp = recv_state_data();
  if (new_state) {
    strcpy(_state_chars,state_chars);
    if (state_index==0) { // first value is the length of the state machine message
      state_cmd_len = atoi(_state_chars);
      begin_msg_timestamp = millis();
    } 
    else if (state_index == 1) { // second value is the state to go to in state machine
      cmd = atoi(_state_chars);
    }
    else { // the remaining value are parameters specific to the state
      val_arr[state_index-2] = atoi(_state_chars);
    }
    
    state_index +=1; // update index
    if ((state_index-2) == state_cmd_len) { // if reached end of state machine message
      begin_msg_timestamp=-1;
      execute_state(cmd, state_cmd_len);
      state_index = 0;
    }
    new_state = false;
  }
  if ((curr_msg_timestamp-begin_msg_timestamp) & (begin_msg_timestamp>0)) { // if command isn't read before timeout
    //abort 
  }
  
}

int recv_state_data() { // receive USB1 data, ov
  static byte ndx = 0; // buffer index
  static char delimiter = ','; // column delimiter
  static char endline = '\n'; // endline character
  char rc; // current byte;
  int timestamp

  if (SerialUSB1.available() > 0){
    timestamp = millis();
    rc = SerialUSB1.read();
    if ((rc == endline) | (rc==delimiter)) { // end of frame or new column
      state_chars[ndx] = '\0'; // terminate string
      ndx = 0;
      new_state = true;
    } 
    else {
      state_chars[ndx] = rc;
      ndx++;
      if (ndx >= num_chars) {
        ndx = num_chars - 1;
      } 

    }
  }

  return timestamp
}

void execute_state(int cmd, int cmd_len) {

  switch(cmd){
    case 0: // do nothing
      break;
    case 1: // flip start scan trigger high
      if (!bk_isscanning) {
        bk_scan_trig.trig.trigger();
        bk_scan_trig.is_scanning = true;

        SerialUSB2.print("start, "); // start trigger falling edge Fictrac frame
        SerialUSB2.print(ft_handler.current_frame);
        SerialUSB2.print('\n');
      }
      break;
    case 2: // kill scan
      if (bk_scan_trig.is_scanning) {
        bk_scan_trig.trig.trigger();
        bk_scan_trig.is_scanning = false;

        SerialUSB2.print("abort, "); // abort trigger rising edge Fictrac frame
        SerialUSB2.print(ft_handler.current_frame);
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
      ft_handler.closed_loop=false;
      break;
    
    case 5: // go back to closed loop 
      ft_handler.closed_loop = true;
      break;

    case 6: // set heading_dac value
      ft_handler.set_heading(val_arr[0]);
      break;

    case 7: // set index_dac value 
      ft_handler.set_index(var_arr[1]);
      break;

    case 8: // set heading and index dac
      ft_handler.set_heading(val_arr[0]);
      ft_handler.set_index(var_arr[1]);
      break;

    case 9: // set heading and index dac, trigger opto with specified delay
      // heading, index, opto_bool, opto_delay
      run_point(val_arr[0], val_arr[1], val_arr[2], val_arr[3]);
      break;

    case 10: // run list of points
     // each point: heading, index, opto_bool, opto_delay, combined_dur
      multiple_points = true;
      n_points = cmd_len/5;     
      current_point = 0;
      
      run_point(val_arr[0], val_arr[1], val_arr[2], val_arr[3]);
      
      next_point_time = val_arr[4];
      current_point_timestamp = millis();
      break;

    case 11: // kill list of points
      multiple_points=false;
      break;

    case 12: // trig pump
      trig_pump();
      break;

    case 13: // trig pump and opto with specified delay
      // opto_bool, opto_delay
      run_pump_point(val_arr[0], val_arr[1]);
      break;
  }
  


}


// heading, index, opto_bool, opto_delay
void run_point(int _heading, int _index, int _opto_bool, int _opto_delay) {
  if (_opto_delay>=0) {
        ft_handler.set_heading(_heading);
        ft_handler.set_index(_index);
        
        
        if (_opto_bool>0) {
          opto_trig.trigger_on_delay(_opto_delay);
        }
        
      } else {

        if (_opto_bool>0) {
          trig_opto();
        }

        ft_handler.set_heading_on_delay(_-1*_opto_delay);
        ft_handler.set_index_on_delay(-1*_opto_delay);


      }
}

// opto_bool opto_delay
void run_pump_point(int _opto_bool, int _opto_delay) {
  if (_opto_delay>=0) {

        trig_pump();
        if (_opto_bool>0) {
          opto_trig.trigger_on_delay(_opto_delay);
        }
        
      } else {

        
        trig_opto();
        
        pump_trig.trigger_on_delay(-1*_opto_delay)

      }
}

void trig_opto() {

  bk_opto_trig.trigger();
  
  SerialUSB2.print("opto, "); // opto trigger rising edge Fictrac frame
  SerialUSB2.print(ft_handler.current_frame);
  SerialUSB2.print('\n');
}

void trig_pump() {

  pump_trig.trigger();

  SerialUSB2.print("pump, ");
  SerialUSB2.print(ft_handler.current_frame);
  SerialUSB2.print('\n')
}


void check_trig_pins() {
  static int va_index=0;

  // flip start down
  int curr_timestamp = millis();
  if (bk_scan_trig.trig.pin_state & ((curr_timestamp - bk_scan_trig.trig.get_timestamp()) > 10)) {
    if (bk_scan_trig.is_scanning) { // if this is a start scan trigger
      SerialUSB2.print("start_trig_falling_edge, "); // start trigger falling edge Fictrac frame
      SerialUSB2.print(ft_handler.current_frame);
      SerialUSB2.print('\n');
    }
    bk_scan_trig.trig.check(curr_timestamp);
  }

  // flip opto trigger down
  bk_opto_trig.check(curr_timestamp);
  
  // flip opto trigger down
  pump_trig.check(curr_timestamp);
  



  // deal with multiple points
  if (multiple_points) {
    if (current_point < n_points-1){
      if ((curr_timestamp-current_point_timestamp)>next_point_time) {
        
        
        va_index = (current_point + 1) * 5;

        
        run_point(val_arr[va_index], val_arr[va_index+1], val_arr[va_index+2], val_arr[va_index+3]);
        next_point_time = val_arr[va_index+4];
        current_point_timestamp = millis();
        current_point++;
      }
    } else {
      multiple_points = false;
    }
  }

}


void ft_state() {
    ft_handler.process_serial_data();
    ft_handler.update_dacs();
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
