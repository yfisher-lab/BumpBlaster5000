// State reading variables
#include <cstring>
#include "Trigger"
#include "FTHandler"



// const int state_num_vals = 2;
const byte ft_frame_pin = 2; 
FTHandler ft_handler(ft_frame_pin, &Serial);



//Bruker Triggers
struct {
    Trigger trig(3,10);
    bool is_scanning;
} bk_scan_trig;
bk_scan_trig.is_scanning = false;

Trigger bk_opto_trig(4,10);
Trigger pump_trig(5,10);

// command serial handler
StateSerialHandler state_serial_handler(&SerialUSB1);

// class for running visual and optogenetic stimulation
RunVisOptoPoints vis_opto_pointrunner(&state_serial_handler.cmd,
                                      &state_serial_handler.cmd_array)


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
  state_serial_handler.process_srl_data();
  execute_state();
  
  ft_handler.process_serial_data();
  ft_handler.update_dacs();
  
  check_timers();
}

void execute_state() {

  switch(state_serial_handler.cmd){
    case 0: // do nothing
      break;
    case 1: // flip start scan trigger high
      if (!bk_scan_trig.is_scanning) {
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
      ft_handler.set_heading(state_serial_handler.cmd_arr[0]);
      break;

    case 7: // set index_dac value 
      ft_handler.set_index(state_serial_handler.cmd_arr[0]);
      break;

    case 8: // set heading and index dac
      ft_handler.set_heading(state_serial_handler.cmd_arr[0]);
      ft_handler.set_index(state_serial_handler.cmd_arr[1]);
      break;

    case 9: // set heading and index dac, trigger opto with specified delay
      vis_opto_point_runner.start_points();
      break;

    case 10: // run list of points
      vis_opto_point_runner.start_points();
      break;

    case 11: // kill list of points
      vis_opto_point_runner.abort_points()
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



void check_timers() {
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
  vis_opto_point_runner.check_for_next_point(curr_timestamp);
}


class StateSerialHandler {
  
  Stream *Srl;

  int buffer_ndx = 0;
  char delimiter = ','; 
  char endline = '\n';
  char curr_byte;
  
  int data_rcvd_timestamp = -1;


  char chars[num_chars];
  char _chars[num_chars];
  bool new_data = false;
  
  int msg_timeout_len = 1000;
  int begin_msg_timestamp = -1;

  public:
    int cmd = 0;
    int cmd_len = -1;
    int cmd_index = 0;
    
    int cmd_arr[1024]; // 204 points can be initialized 

    StateSerialHandler(Stream *srl_port) {
      Srl = srl_port;
    }

    void receive_srl_data() {

      if (Srl.available() > 0){
        data_rcvd_timestamp = millis();
        curr_byte = Srl.read();
        if ((curr_byte == endline) | (curr_byte==delimiter)) { // end of frame or new column
          chars[buffer_ndx] = '\0'; // terminate string
          buffer_ndx = 0;
          new_data = true;
        } 
        else {
          chars[buffer_ndx] = curr_byte;
          buffer_ndx++;
          if (buffer_ndx >= num_chars) {
            buffer_ndx = num_chars - 1;
          } 
        new_data = false;
        }
      }
      new_data = false;
    }


    void process_srl_data() {
      // static int val = 0;

      receive_srl_data();
      if (new_data) {
        
        strcpy(_chars,chars);
        
        if (cmd_index==0) { // first value is the length of the state machine message
          cmd_len = atoi(_chars);
          begin_msg_timestamp = millis();
        } 
        else if (cmd_index == 1) { // second value is the state to go to in state machine
          cmd = atoi(_chars);
        }
        else { // the remaining value are parameters specific to the state
          cmd_arr[cmd_index-2] = atoi(_chars);
        }
        
        cmd_index++; // update index
        if ((cmd_index-2) == cmd_len) { // if reached end of state machine message
          begin_msg_timestamp=-1;
          cmd_index = 0;
        }
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


class RunVisOptoPoints {

  int *cmd_len;
  int *cmd_arr[1024];
  int n_points;
  
  const int pnt_len = 5;

  int point_start_time = -1;
  int curr_point;
  int start_ind;

  int next_point_time;
  bool pts_complete; 
  


  public: 
    RunVisOptoPoints(int *_cmd_len, int *_cmd_arr[1024]) {
      cmd_len = _cmd_len;
      cmd_arr = _cmd_arr;
      pts_complete= true;   
    }

    void start_points() {
      n_points = cmd_len/pnt_len;
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
      _h = cmd_arr[start_ind];
      _i = cmd_arr[start_ind + 1];
      _opto_bool = cmd_arr[start_ind + 2];
      _opto_del = cmd_arr[start_ind + 3];

      next_point_millis = cmd_arr[start_ind + 4];

      if (_opto_delay>=0) {
        ft_handler.set_heading(_h);
        ft_handler.set_index(_i);
        
        
        if (_opto_bool>0) {
          opto_trig.trigger_on_delay(_opto_delay);
        }
        
      } else {
        
        if (_opto_bool>0) {
          opto_trig.trigger();
        }
        
        ft_handler.set_heading_on_delay(_-1*_opto_delay);
        ft_handler.set_index_on_delay(-1*_opto_delay);
      }


    }

    void check_for_next_point(int curr_time) {
      if (!pts_complete) {
        if (curr_time>(point_start_time+next_point_time)) {
          curr_point++;
          if (curr_point == n_points) {
            pts_complete=true;
          } else {
            point_start_time = curr_time;
            run_point();
          }
        }
      }
    }

    void abort_points() {
      pts_complete = true;
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
  
