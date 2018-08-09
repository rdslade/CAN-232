# CAN-232
Multistage programming and testing for Grid Connect RS232 CAN Converter

[Link](https://github.com/rdslade/CAN-232/blob/master/howto.md) to details on code organization and important Python features.

## Installation
### Using git clone
```
$ git clone https://github.com/rdslade/CAN-232
$ cd CAN-232
```
### Using downloads
1. Download CAN-232.zip
2. Unzip or open the file in the desired location

## How to use
The majority of the functionality of this program is written in the `CAN-USB-COM.pyw` file. 
This part of the program can be run in multiple 'modes' determined by the user at runtime and through certain files in the `Config/` directory.

### Layout of the Config directory
`can_config.txt`: Single line consisting of the COM port where the command CAN signal is located

`permissions.txt`: Determines the mode (production vs advanced) in which the program runs
  **NOTE: currently issues with production mode*
  
 `ports_config[n].txt`: *Each text file includes the following*-
 
 1. An instructions line detailing the order in which the ports are labeled
 2. A line for each station with it's ports listed in order
    * A programming port through which the USB232 is plugged in
    * A serial port through which the main serial communcation port of the device being programmed is plugged in
    
## How to run
The CAN-USB-COM.pyw is called with a command line argument specifying which ports_config text file to use when initializing the graphics window. Each command line call to start the program opens a single window. 

### With command line arguments

```
py CAN-USB-COM.pyw 2
```
Starts the program with the configuration listed in `Config/ports_config2.txt`

### Without command line arguments
If the command line argument is omitted, the config file defaults to `Config/ports_config1.txt`
```
py CAN-USB-COM.pyw
```
Starts the program with the configuration listed in `Config/ports_config1.txt`

### Production
For production, a seperate script `main.py` has been written to instatiate multiple windows to match the layout of the programming fixture.

```
py main.py
```
Starts the program with two different windows calling the commands listed above to instantiate different configurations.

