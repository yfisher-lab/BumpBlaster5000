#ifndef FTHANDLER_H
#define FTHANDLER_H

#include "Arduino.h"
#include <Wire.h>
#include <Adafruit_MCP4725.h>
#include <Adafruit_I2CDevice.h>
#include <Wire.h>
#include <math.h>


class FTHandler {

    Adafruit_MCP4725 heading_dac;
    Adafruit_MCP4725 index_dac;

    const int max_dac_val = 4095;
    const int num_cols = 26;

    int frame_pin

    bool closed_loop;

    int num_chars = 256;
    char chars[256];
    char _chars[256];
    int col;
    bool new_data;

    int buffer_ndx = 0;
    static char delimeter = ',';
    static char endline = '\n'
    char curr_byte;
    
    int current_frame;
    
    double ft_heading;
    double ft_heading_offset;
    
    double heading;

    int index;

    bool heading_on_delay = false;
    int heading_delay = 0;
    int heading_delay_timestamp = 0;
    double delayed_heading_val;

    bool index_on_delay = true;
    int index_delay = 0;
    int index_delay_timestamp = 0;
    int delayed_index_val;


    public:
        FTHandler(int f_pin);
        
        void init(uint8_t h_dac_addr, TwoWire *h_dac_wire, int i_dac_addr, TwoWire *i_dac_wire);

        void receive_srl_data();
        void update_col();
        
        void update_dacs();
        void execute_col();

        int get_heading();
        void set_heading();
        void set_heading_offset();
        void rotate_scene();

        int get_index();
        void set_index();

        void set_heading_on_delay();
        void set_index_on_delay();
}

