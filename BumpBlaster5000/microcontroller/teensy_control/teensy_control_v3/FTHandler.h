#ifndef FTHANDLER_H
#define FTHANDLER_H

#include "Arduino.h"

#include "LTC1661.h"
#include <SPI.h>
#include <math.h>
#include <cstring>
#include <algorithm>
using namespace std;

const int num_chars = 256;

struct dac_countdown { // struct for storing info about when to set dac
    bool on_delay = false;
    int delay;
    int timestamp;
    double val;
};

class FTHandler { 
//    bool closed_loop = true; 
    char chars[num_chars]; 
    bool new_data = false;

    double heading;
    bool new_heading;
    dac_countdown heading_countdown;
    double ft_heading;
    int index;
    bool new_index;
    dac_countdown index_countdown;

    double heading_offset=0;

    
    int frame_pin;

    int max_dac_val = 1023; // LTC1661 is 10-bit
    int num_cols = 26; 

    int col=0;
    int curr_time;

    Stream& srl;  

    // Single LTC1661 dual-channel 10-bit SPI DAC.
    // Channel 0 (DAC A) = heading, Channel 1 (DAC B) = index.
    LTC1661 dac;


    void recv_data();
    void update_col();
    void execute_col();

    public:

        int current_frame = 0;
        bool closed_loop = true;

        FTHandler(Stream& srl_ref);
        void init(int f_pin, int cs_pin, SPIClass& spi_port = SPI);
        
        void process_srl_data();
        void update_dacs();

        void set_heading(double h);

        void set_index(int i);

        void set_heading_offset(double o);

        void rotate_scene(double r);
        int get_index(); 

        void set_heading_on_delay(int t, double h);

        void set_index_on_delay(int t, int i );


};




#endif
