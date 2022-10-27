// FicTrac reading variables
const int num_chars = 256;
char ft_chars[num_chars];
char _ft_chars[num_chars];
boolean ft_new_data = false;
int ft_index=0;
double ft_heading;
float ft_x;
float ft_y;

const byte ft_frame_pin = 2; // update pin value

int ft_current_frame = 0;

#include <Wire.h>
#include <Adafruit_MCP4725.h>
Adafruit_MCP4725 heading_dac;
Adafruit_MCP4725 x_dac;
Adafruit_MCP4725 y_dac;
Adafruit_MCP4725 index_dac;
const int max_dac_val = 4095; // 4096 - 12-bit resolution
const byte ft_num_cols = 26; 
const byte ft_dropped_frame_pin = 5; // update pin value

//Bruker Triggers
const byte bk_scan_trig_pin = 3; // update pin value
bool bk_scan_trig_state = false;
bool bk_isscanning = false;
int bk_scan_trig_timestamp;

const byte bk_opto_trig_pin = 4; // update pin value
bool bk_opto_trig_state = false;
int bk_opto_trig_timestamp;
const int bk_trig_timeout = 10;

#define BKSERIAL Serial6 // update to current pin settings


//const byte cam_trig_pin = 41; // update pin value - may not be used
//int cam_pin_val;


void setup() {
  // put your setup code here, to run once:

  // FicTrac setup
  // digital pins
  pinMode(ft_frame_pin,OUTPUT);
  digitalWrite(ft_frame_pin,LOW);
  pinMode(ft_dropped_frame_pin, OUTPUT); 
  digitalWriteFast(ft_dropped_frame_pin, LOW);


  // start DACs
  heading_dac.begin(0x62,&Wire);
  x_dac.begin(0x63,&Wire);
  y_dac.begin(0x62,&Wire1);
//  4th dac available for additional output
  index_dac.begin(0x63, &Wire1);

  // Bruker setup
  pinMode(bk_scan_trig_pin, OUTPUT);
  digitalWriteFast(bk_scan_trig_pin, LOW);
  bk_scan_trig_timestamp = millis();

  pinMode(bk_opto_trig_pin, OUTPUT);
  digitalWriteFast(bk_opto_trig_pin, LOW);
  bk_opto_trig_timestamp = millis();

  // camera trig
//  pinMode(cam_trig_pin,INPUT);

  BKSERIAL.begin(115200);
  
  
  
}


void yield() {} // get rid of hidden arduino yield function

FASTRUN void loop() { // FASTRUN teensy keyword

    ft_state();
    bk_state();
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

void recv_ft_data() { // receive Fictrack data
    
    static byte ndx = 0; // buffer index
    char delimiter = ','; // column delimiter
    char endline = '\n'; // endline character
    char rc; // current byte

    if (Serial.available() > 0) { // cannot use while(Serial.available()) because Teensy will read all 
        rc = Serial.read(); 
        if ((rc == endline)|(rc==delimiter)) { // end of frame or new column      
          ft_chars[ndx] = '\0'; // terminate the string
          ndx = 0; // restart buffer index
          ft_new_data = true;   // cue new data

          if (rc == endline) { // check to make sure this works, checks that columns are being counted correctly
            int _ft_index = ft_index + 1;
            if (_ft_index != (ft_num_cols )) {
              
//              digitalToggle(ft_dropped_frame_pin);
//            ft_index = ft_num_cols-1;
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

//      SerialUSB2.print("z \t");
//      SerialUSB2.print(_ft_chars);
//      SerialUSB2.print("\n");
//      
      // update heading pin
      heading_dac.setVoltage(int(max_dac_val * atof(_ft_chars) / (2 * PI)),false);
      break;
    
    case 12: // x
      x_dac.setVoltage(int(max_dac_val * (atof(_ft_chars) + PI) / (2 * PI)),false);
      break;

    case 13: // y
      y_dac.setVoltage(int(max_dac_val * (atof(_ft_chars) + PI) / (2 * PI)),false);
      break;

//    case 20: // x
//      // debugging print x cumm
//      SerialUSB2.print("x \t");
//      SerialUSB2.print(_ft_chars);
//      SerialUSB2.print("\t");
//
//      break;
//
//    case 21: // y
//      // debugging print y cumm
//      SerialUSB2.print("y \t");
//      SerialUSB2.print(_ft_chars);
//      SerialUSB2.print("\t");
//      
      
//      break;
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


void bk_state() {
  int _cmd = 0;
  int _val = 0;
  if (SerialUSB1.available() >0) {
    _cmd = SerialUSB1.parseInt();
    _val = SerialUSB1.parseInt();
  }
  bk_state_machine(_cmd, _val);
    
}

void bk_state_machine(int cmd, int val) {

  
  
  switch(cmd){
    case 0: // do nothing
      break;
    case 1: // flip start scan trigger high
      if (!bk_isscanning) {
        digitalWriteFast(bk_scan_trig_pin, HIGH);
        bk_scan_trig_state = true;
        bk_scan_trig_timestamp = millis();
        bk_isscanning = true;
      }
      break;
    case 2: // flip kill scan trigger high
//      digitalWriteFast(bk_kill_scan_pin, HIGH);
      if (bk_isscanning) {
        digitalWriteFast(bk_scan_trig_pin, HIGH);
        bk_scan_trig_state = true;
        bk_scan_trig_timestamp = millis();

        SerialUSB2.print("abort, "); // abort trigger rising edge Fictrac frame
        SerialUSB2.print(ft_current_frame);
        SerialUSB2.print('\n');
        SerialUSB2.println("END QUEUE");

        // send kill scan signal to PrarieView API
        BKSERIAL.println("-Abort");

        bk_isscanning = false;
      }
      break;
    case 3: // flip opto scan trigger high
      digitalWriteFast(bk_opto_trig_pin, HIGH);
      bk_opto_trig_state = true;
      bk_opto_trig_timestamp = millis();


      SerialUSB2.print("opto, "); // opto trigger rising edge Fictrac frame
      SerialUSB2.print(ft_current_frame);
      SerialUSB2.print('\n');
      break;

    case 4: // set index_dac value 
      index_dac.setVoltage(val,false);


  }
  bk_check_pins();
  

}


void bk_check_pins() {
// flip triggers down
  int curr_timestamp = millis();
  if (bk_scan_trig_state & ((curr_timestamp - bk_scan_trig_timestamp) > bk_trig_timeout)) {
    if (bk_isscanning) { // if this is a start scan trigger
      SerialUSB2.print("start, "); // start trigger falling edge Fictrac frame
      SerialUSB2.print(ft_current_frame);
      SerialUSB2.print('\n');
    }
    
    digitalWriteFast(bk_scan_trig_pin,LOW);
    bk_scan_trig_state=false;

  }

  if (bk_opto_trig_state & ((curr_timestamp - bk_opto_trig_timestamp) > bk_trig_timeout)) {
    digitalWriteFast(bk_opto_trig_pin,LOW);
    bk_opto_trig_state=false;
  }
}
