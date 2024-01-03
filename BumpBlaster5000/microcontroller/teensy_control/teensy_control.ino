// State reading variables
#include <cstring>

const int num_chars = 256;
char state_chars[num_chars];
char _state_chars[num_chars];
bool new_state = false;
int state_index = 0;
int val_arr[1024]; // 204 points can be initialized 


int val_arr[80]; 


int val_arr[80]; 


// const int state_num_vals = 2;

bool closed_loop = true;

// FicTrac reading variables
char ft_chars[num_chars];
char _ft_chars[num_chars];
boolean ft_new_data = false;
int ft_index=0;
double ft_heading;
float ft_x;
float ft_y;
int ft_current_frame = 0;
const byte ft_frame_pin = 2; 


#include <Wire.h>
#include <Adafruit_MCP4725.h>
Adafruit_MCP4725 heading_dac;
//Adafruit_MCP4725 x_dac;
//Adafruit_MCP4725 y_dac;
Adafruit_MCP4725 index_dac;
const int max_dac_val = 4095; // 4096 - 12-bit resolution
const byte ft_num_cols = 26; 
const byte ft_dropped_frame_pin = 5; 

//Bruker Triggers
const byte bk_scan_trig_pin = 3; 
bool bk_scan_trig_state = false;
bool bk_isscanning = false;
int bk_scan_trig_timestamp;

const byte bk_opto_trig_pin = 4; 
bool bk_opto_trig_state = false;
int bk_opto_trig_timestamp;
const int bk_trig_timeout = 10;

bool opto_countdown_bool = false;
int opto_countdown_delay = 100;
int opto_countdown_timestamp;

bool dac_countdown_bool = false;
int dac_countdown_delay = 100;
int dac_countdown_timestamp;
int dac_countdown_heading;
int dac_countdown_index;

bool multiple_points = false;
int n_points;
int current_point;
int next_point_time;
int current_point_timestamp;

#define BKSERIAL Serial6 // update to current pin settings

void setup() {
  // put your setup code here, to run once:

  // FicTrac setup
  // digital pins
  pinMode(ft_frame_pin,OUTPUT);
  digitalWrite(ft_frame_pin,LOW);
  pinMode(ft_dropped_frame_pin, OUTPUT); 
  digitalWriteFast(ft_dropped_frame_pin, LOW);


  // start DACs
  heading_dac.begin(0x62,&Wire1);
//  x_dac.begin(0x63,&Wire);
//  y_dac.begin(0x62,&Wire1);
//  4th dac available for additional output
  index_dac.begin(0x63, &Wire1);

  // Bruker setup
  pinMode(bk_scan_trig_pin, OUTPUT);
  digitalWriteFast(bk_scan_trig_pin, LOW);
  bk_scan_trig_timestamp = millis();

  pinMode(bk_opto_trig_pin, OUTPUT);
  digitalWriteFast(bk_opto_trig_pin, LOW);
  bk_opto_trig_timestamp = millis();

  // opto_countdown_timestamp = millis();

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
  
  
  // static int val = 0;

  recv_state_data();
  if (new_state) {
    strcpy(_state_chars,state_chars);
    if (state_index==0) { // first value is the length of the state machine message
      state_cmd_len = atoi(_state_chars);
//      int val_arr[state_cmd_len];
//      int val_arr[state_cmd_len];
    } 
    else if (state_index == 1) { // second value is the state to go to in state machine
      cmd = atoi(_state_chars);
    }
    else { // the remaining value are parameters specific to the state
      val_arr[state_index-2] = atoi(_state_chars);
    }
    
    state_index +=1; // update index
    if ((state_index-2) == state_cmd_len) { // if reached end of state machine message
      execute_state(cmd, state_cmd_len);
      state_index = 0;
    }
    new_state = false;
  }
  
}

void recv_state_data() { // receive USB1 data, ov
  static byte ndx = 0; // buffer index
  static char delimiter = ','; // column delimiter
  static char endline = '\n'; // endline character
  char rc; // current byte;

  if (SerialUSB1.available() > 0){
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
}

void execute_state(int cmd, int cmd_len) {

  switch(cmd){
    case 0: // do nothing
      break;
    case 1: // flip start scan trigger high
      if (!bk_isscanning) {
        digitalWriteFast(bk_scan_trig_pin, HIGH);
        bk_scan_trig_state = true;
        bk_scan_trig_timestamp = millis();
        bk_isscanning = true;

        SerialUSB2.print("start, "); // start trigger falling edge Fictrac frame
        SerialUSB2.print(ft_current_frame);
        SerialUSB2.print('\n');
      }
      break;
    case 2: // kill scan
      if (bk_isscanning) {
        digitalWriteFast(bk_scan_trig_pin, HIGH);
        bk_scan_trig_state = true;
        bk_scan_trig_timestamp = millis();

        SerialUSB2.print("abort, "); // abort trigger rising edge Fictrac frame
        SerialUSB2.print(ft_current_frame);
        SerialUSB2.print('\n');
        // SerialUSB2.println("END QUEUE");

        // send kill scan signal to PrarieView API
        BKSERIAL.println("-Abort");

        bk_isscanning = false;
      }
      break;
    case 3: // flip opto scan trigger high
      trig_opto();
      break;

    case 4: // set heading pin to manual control (i.e. open loop)
      closed_loop=false;
      break;
    
    case 5: // go back to closed loop 
      closed_loop = true;
      break;

    case 6: // set heading_dac value
      heading_dac.setVoltage(val_arr[0], false);
      break;

    case 7: // set index_dac value 
      index_dac.setVoltage(val_arr[0],false);
      break;

    case 8: // set heading and index dac
      heading_dac.setVoltage(val_arr[0], false);
      index_dac.setVoltage(val_arr[1], false);
      break;

    case 9: // set heading and index dac, trigger opto with specified delay
      // heading, index, opto_bool, opto_delay
      run_point(val_arr[0], val_arr[1], val_arr[2], val_arr[3]);
      break;

    case 10: // run list of points
     // each point: heading, index, opto_bool, opto_delay, combined_dur
      multiple_points = true;
      n_points = cmd_len/5;
//      SerialUSB2.print('\t');
      
      current_point = 0;
      
      run_point(val_arr[0], val_arr[1], val_arr[2], val_arr[3]);
      
      next_point_time = val_arr[4];
      current_point_timestamp = millis();
      break;

    case 11: // kill list of points
      multiple_points=false;
      break;
  }
  


}


// heading, index, opto_bool, opto_delay
void run_point(int _heading, int _index, int _opto_bool, int _opto_delay) {
  if (_opto_delay>=0) {
        heading_dac.setVoltage(_heading, false);
        index_dac.setVoltage(_index,false);

        if (_opto_bool>0) {
          opto_countdown_bool = true;
          opto_countdown_delay = _opto_delay;
          opto_countdown_timestamp = millis();
        }
        
      } else {

        if (_opto_bool>0) {
          trig_opto();
        }

        if (_opto_bool>0) {
          trig_opto();
        }

        dac_countdown_bool = true;
        dac_countdown_delay = -1*_opto_delay;
        dac_countdown_timestamp = millis();

        dac_countdown_heading = _heading;
        dac_countdown_index = _index;
        

      }
}

void trig_opto() {

  digitalWriteFast(bk_opto_trig_pin, HIGH);
  bk_opto_trig_state = true;
  bk_opto_trig_timestamp = millis();


  SerialUSB2.print("opto, "); // opto trigger rising edge Fictrac frame
  SerialUSB2.print(ft_current_frame);
  SerialUSB2.print('\n');
}


void check_pins() {
  static int va_index=0;
//  char curr_str[15] = "current_point";
//  char val_arr_str[15] = "val_arr";
  // flip start down
  int curr_timestamp = millis();
  if (bk_scan_trig_state & ((curr_timestamp - bk_scan_trig_timestamp) > bk_trig_timeout)) {
    if (bk_isscanning) { // if this is a start scan trigger
      SerialUSB2.print("start_trig_falling_edge, "); // start trigger falling edge Fictrac frame
      SerialUSB2.print(ft_current_frame);
      SerialUSB2.print('\n');
    }
    
    digitalWriteFast(bk_scan_trig_pin,LOW);
    bk_scan_trig_state=false;

  }

  // flip opto trigger down
  if (bk_opto_trig_state & ((curr_timestamp - bk_opto_trig_timestamp) > bk_trig_timeout)) {
    digitalWriteFast(bk_opto_trig_pin,LOW);
    bk_opto_trig_state=false;
  }

  // flip opto up after specified delay
  if (opto_countdown_bool) {
    if ((curr_timestamp-opto_countdown_timestamp)>opto_countdown_delay) {
      trig_opto();
      opto_countdown_bool = false;

    }
  }

  // set dac values after specified delay
  if (dac_countdown_bool) {
    if ((curr_timestamp-dac_countdown_timestamp) > dac_countdown_delay) {
      
      heading_dac.setVoltage(dac_countdown_heading, false);
      index_dac.setVoltage(dac_countdown_index, false);
      dac_countdown_bool = false;
    }
  }


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
  recv_ft_data(); 
  if (ft_new_data == true) {

    strcpy(_ft_chars, ft_chars); // prevent overwriting
    ft_state_machine();
    ft_index = (ft_index+1) % ft_num_cols; // keep track of columns in fictrack  
    ft_new_data = false;
  }
  
}

void recv_ft_data() { // receive Fictrac data
    
    static byte ndx = 0; // buffer index
    static char delimiter = ','; // column delimiter
    static char endline = '\n'; // endline character
    char rc; // current byte

    if (Serial.available() > 0) { // cannot use while(Serial.available()) because Teensy will read all 
        rc = Serial.read(); 
        if ((rc == endline)|(rc==delimiter)) { // end of frame or new column      
          ft_chars[ndx] = '\0'; // terminate the string
          ndx = 0; // restart buffer index
          ft_new_data = true;   // cue new data

          if (rc == endline) { // checks that columns are being counted correctly
            int _ft_index = ft_index + 1;
            if (_ft_index != (ft_num_cols )) {
              
              digitalToggle(ft_dropped_frame_pin);
              ft_index = ft_num_cols-1;
            }
          }
          
        }
        else {
          ft_chars[ndx] = rc;
          ndx++;
          if (ndx >= num_chars) {
              ndx = num_chars - 1;
          } 
        }
    }
}

void ft_state_machine() {

  // switch case statement for variables of interest
  switch (ft_index) {
    
    case 0: // new FicTrac frame
      // flip ft pin high
      digitalWriteFast(ft_frame_pin,HIGH);
      break;

    case 1: // frame counter
      ft_current_frame = atoi(_ft_chars);
      break;

    case 17: // heading 
      // flip ft pin low 
      digitalWriteFast(ft_frame_pin,LOW);

      // update heading pin
      if (closed_loop) {
        heading_dac.setVoltage(int(max_dac_val * atof(_ft_chars) / (2 * PI)),false);
      }
      break;
    
    case 12: // x
//      x_dac.setVoltage(int(max_dac_val * (atof(_ft_chars) + PI) / (2 * PI)),false);
      break;

    case 13: // y
//      y_dac.setVoltage(int(max_dac_val * (atof(_ft_chars) + PI) / (2 * PI)),false);
      break;

  }
  
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
