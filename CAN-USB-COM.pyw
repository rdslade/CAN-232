import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import IntVar, StringVar
from time import sleep
import serial
import sys
import time
import datetime
import threading
from multiprocessing import Queue, Process
import re
from tkinter.filedialog import askopenfilename

gridColor = "#20c0bb"
entryWidth = 8
num_coms = 1
master_transmit = slave_recieve = "221"
master_recieve = slave_transmit = "1A1"
baudrate = 115200
advanced = 1

### class which details the specifics of each individual station programming
### threaded such that multiple Station instances can run simultaneously
class Station():
    def __init__(self, parent, prog_com_, out_com_, can_com_, mode_, stat_num):
        self.thread = threading.Thread(target = self.process)
        self.station_num = stat_num
        self.parent = parent

        self.sernum = ""
        self.version = ""
        self.tempSerialTest = 1 #failure indicator for first part of com test
        self.tempCANTest = 1 #failure indicator for second part of com test

        self.prog_com = StringVar() #programming port
        self.prog_com.set(prog_com_)
        self.out_com = StringVar() #display port
        self.out_com.set(out_com_)

        self.main_mod = serial.Serial()
        self.main_mod.baudrate = baudrate
        self.main_mod.port = self.out_com.get()
        self.main_mod.timeout = .03

        self.can_com = can_com_
        self.mode = mode_
        self.deviceType = "GC-CAN-USB-COM"
        self.frame = tk.Frame(self.parent)
        self.initComponents()
        self.packObjects()

    ### Creates the components associated with a single Station instance
    def initComponents(self):
        self.setup = tk.Frame(self.frame)
        self.prog = tk.Frame(self.setup)
        self.out = tk.Frame(self.setup)

        self.prog_entry = tk.Entry(self.prog, width = entryWidth, textvariable = self.prog_com)
        self.out_entry = tk.Entry(self.out, width = entryWidth, textvariable = self.out_com)
        self.prog_label = tk.Label(self.prog, text = "Programming Port: ")
        self.out_label = tk.Label(self.out, text = "Display Port: ")

        self.station_label = tk.Label(self.setup, text = self.prog_com.get() + "\\" + self.out_com.get())

        self.statusSpace = tk.LabelFrame(self.frame, width = 200, height = 250)
        self.currentStatus = tk.Label(self.statusSpace, text = "", width = 25, pady = 10)
        self.progressBar = ttk.Progressbar(self.statusSpace, mode = 'determinate', length = 125)
        self.explanation = tk.Label(self.statusSpace, text = "", width = 25, pady = 10)
        self.barrier = ttk.Separator(self.statusSpace)
        self.program = IntVar()
        self.verify = IntVar()
        self.communicate = IntVar()
        self.chooseLabel = tk.Label(self.statusSpace, text = "Select desired functions", fg = gridColor, pady = 5)
        self.chooseProgramming = tk.Checkbutton(self.statusSpace, text = "Program Module", variable = self.program)
        self.chooseVerify = tk.Checkbutton(self.statusSpace, text = "Verify Device Version", variable = self.verify)
        self.chooseCommunicate = tk.Checkbutton(self.statusSpace, text = "Test Device Communication", variable = self.communicate)

    ### Changes all checkboxes states to parameter
    def changeAllComponents(self, state_):
        self.changeProgramming(state_, self.program.get())
        self.changeVerify(state_, self.verify.get())
        self.changeCommunicate(state_, self.communicate.get())

    ### Sets the state and value of the Stations programming boxes
    def changeProgramming(self, state_, value_):
        self.chooseProgramming.configure(state = state_)
        self.program.set(value_)

    ### Sets the state and value of the Stations verify boxes
    def changeVerify(self, state_, value_):
        self.chooseVerify.configure(state = state_)
        self.verify.set(value_)

    ### Sets the state and value of the Stations communicate boxes
    def changeCommunicate(self, state_, value_):
        self.chooseCommunicate.configure(state = state_)
        self.communicate.set(value_)

    ### Loads objects into correct places
    def packObjects(self):
        if advanced:
            self.prog_label.pack(side = tk.LEFT)
            self.prog_entry.pack(side = tk.LEFT)
            self.out_label.pack(side = tk.LEFT)
            self.out_entry.pack(side = tk.LEFT)
            self.prog.pack(pady = 5)
            self.out.pack()

        if not advanced:
            self.station_label.pack()

        self.setup.pack()
        self.statusSpace.pack()
        self.currentStatus.pack()
        self.progressBar.pack()
        self.explanation.pack()
        if advanced:
            self.barrier.pack(fill = "x", expand = True)
            self.chooseLabel.pack()
            self.chooseProgramming.pack()
            self.chooseVerify.pack()
            self.chooseCommunicate.pack()
            self.chooseProgramming.select()
            self.chooseVerify.select()
            self.chooseCommunicate.select()
        self.frame.pack(side = tk.LEFT, padx = 10)

    ### Configures command text file
    def configureTextFiles(self):
        self.currentStatus.configure(text = "Configuring executables")
        try:
            file_name = r'CANUSB_Config\CANUSB_CommandFile'+str(self.station_num)+'.txt'
            with open(file_name, 'r+', encoding = 'utf-8') as command:
                # Find where the port number is stored
                command.seek(4)
                prog_com_number = self.prog_com.get().split("COM")[1]
                if(len(prog_com_number) == 1):
                    prog_com_number = '0'+prog_com_number
                # Write in the new (actual) port to be programmed
                command.write(prog_com_number)
        except FileIO:
            messagebox.showinfo("IOError", "Cannot open CANUSB_CommandFile.txt")

    ## Get magic flash commands ready
    def runFlashCommand(self):
        self.currentStatus.configure(text = "Loading firmware")
        flash_magic_cmd = r"CANUSB_Flash\CANUSB_Flash"+str(self.station_num)+".bat"
        try:
            start_time = time.time()
            q = Queue();
            q.put(subprocess.check_output([flash_magic_cmd], shell=True, stderr=subprocess.STDOUT))
            addTextToLabel(self.explanation, "SUCCESSFUL UPLOAD")
            up_time = time.time() - start_time
            addTextToLabel(self.explanation, "\nUploaded in " + str(round(up_time, 2)) + " seconds")
            return 0

        except subprocess.CalledProcessError as e:
            if "Unable to communicate".encode() in e.output:
                self.explanation.configure(text = "\nCould not open " + self.prog_com.get())
            return 1

    ### Used to put the device at the parameter port in to bootloader mode
    def simulateButtonPress(self, port):
        time.sleep(1)
        port.write("!!!".encode())
        time.sleep(1)

    ### Check version number of firmware to make sure device was correctly programmed
    def performVerification(self):
        # Begin Verification
        self.currentStatus.configure(text = "Verification Stage")
        # Open serial port
        try:
            buttonSer = serial.Serial(self.out_com.get(), baudrate = baudrate, timeout = .1)
            addTextToLabel(self.explanation, "\n\nPress the button")
            #Check button push / boot mode
            checkMode = "start"
            while "#0#" not in checkMode:
                self.simulateButtonPress(buttonSer)
                buttonSer.write("\n\r".encode())
                checkMode = readSerialWord(buttonSer)

            addTextToLabel(self.explanation, "\nButton Pressed\nVerifying Firmware Version")
            #Confirm version
            buttonSer.write("get version\r".encode())
            self.version = readSerialWord(buttonSer).split(':')[1].split('>')[0]
            #Get Serial prog_com_number
            buttonSer.write("get sernum\r".encode())
            self.sernum = readSerialWord(buttonSer).split(':')[1].split('>')[0]
            #Exit boot mode
            buttonSer.write("exit\r".encode())
            #Clock Serial Port
            buttonSer.close()
            if "APP=2.00A" not in self.version:
                addTextToLabel(self.explanation, "\n\nWRONG FIRMWARE VERSION")
                return 1
            else:
                addTextToLabel(self.explanation, "\nSUCCESSFUL VERIFICATION")
                return 0
        except serial.SerialException as e:
            return getCOMProblem(e, self)

    ### Send messages from serial port to CAN
    def startCommunication(self):
        self.currentStatus.configure(text = "Testing Communication")
        try:
            if not self.main_mod.is_open:
                self.main_mod.open()
        except serial.SerialException as e:
            completeIndSend.set(completeIndSend.get() + 1)
            return getCOMProblem(e, self);

        self.main_mod.write("exit\r".encode()) #ensure this port is in correct mode for communication
        for i in range(0, num_coms):
            # Send initial serial message
            num_str = adjustStationNum(self.station_num)
            #self.main_mod.flushOutput()
            #self.main_mod.flushInput()
            self.main_mod.write(num_str.encode())
        self.main_mod.close()
        addTextToLabel(self.explanation, "\nWrote " + num_str + " to CAN")
        return 0

    ### Check CAN message and close serial port
    def finishCommunication(self):
        recieve = readSerialWord(self.main_mod)
        self.main_mod.close()
        if "1" in recieve:
            addTextToLabel(self.explanation, "\nRead CAN Message (Success)")
            return 0
        else:
            addTextToLabel(self.explanation, "\nRead CAN Message (Fail)")
            return 1

    ### Organize and log status of each Station instance
    def log_run(self, flash, verify, comm):
        # Only log is some sort of upload was attempted
        if not flash:
            full_date = str(datetime.datetime.now())
            log_str = full_date + " " + self.sernum + " " + self.version + " " + self.deviceType + " "
            # No Failures
            if(not flash and not verify and not comm):
                log_str += str(self.program.get()) + " " + str(self.verify.get()) + " " + str(self.communicate.get())
                log_filename = r"Log\success.txt"
            # Some form of failure
            else:
                log_str += "ERROR- "
                if flash:
                    log_str = "" #TODO
                if verify:
                    log_str += "Verification "
                if comm:
                    log_str += "Communication "
                log_filename = r"Log\fail.txt"
            log_str += "\n"
            with open(log_filename, 'a+',encoding='utf-8') as log:
                log.write(log_str)
                log.close()

    ### Stops and configures progress bar to correct style
    def stopProgressBar(self, fail):
        self.progressBar.stop()
        if not fail:
            self.progressBar.configure(value = 100, style = "green.Horizontal.TProgressbar")
        else:
            self.progressBar.configure(value = 100, style = "red.Horizontal.TProgressbar")

    ### Resets styles and progress of progress bar
    def restartProgressBar(self):
        self.progressBar.configure(value = 0, style = "Horizontal.TProgressbar")
        self.progressBar.start()

    ### Initiates each step of the entire programming process
    def process(self):
        self.restartProgressBar()
        self.explanation.configure(text = "")
        # Configre text files signifying programming ports
        self.configureTextFiles()
        self.flash_fail = self.verify_fail = self.test_fail = 0
        if self.program.get():
            # Run programming
            self.flash_fail = self.runFlashCommand()
        if self.verify.get():
            # Run version verification is successful
            if not self.flash_fail:
                self.verify_fail = self.performVerification()
        if self.communicate.get():
            # Run communication test if not failures
            if not self.flash_fail and not self.verify_fail:
                addTextToLabel(self.explanation, "\n\nWaiting")
                completeIndSend.set(completeIndSend.get() + 1)
        else:
            # Process is complete and must be reset
            completeIndSend.set(0)


    ### Restarts thread with new instantiation
    def createNewThread(self):
        self.thread = threading.Thread(target = self.process)
        self.thread.start()

### Helper function for reading serial words
def readSerialWord(ser_port):
    char = '0'
    response = ""
    # Continue reading word until not more chars
    while char != '':
        char = ser_port.read().decode()
        response += char
    return response

### Reconfigures parameter label to append input text
def addTextToLabel(label, textToAdd):
    label.configure(text = label.cget("text") + textToAdd);

### Read COM ports from config file and returned organized lists of ports
def getCOMPorts():
    devices = []
    with open("Config\can_config.txt", 'r+', encoding = 'utf-8') as common:
        devices.append(common.readline().split()[0]) #first device is the common port
    with open("Config\ports_config.txt", 'r+',encoding='utf-8' ) as mp:
        mp.readline() #first line is instructions
        for line in mp.readlines():
            ports = []
            for p in line.split():
                # Add all COM ports associated with one device
                if "COM" in p:
                    ports.append(p)
            devices.append(ports)
    return devices

### Reads counter file and returns value in the file
def getNumDevicesLoaded():
    try:
        with open("device_counter.txt", 'r+', encoding = 'utf-8') as dev:
            ret = int(dev.readline())
            dev.close()
            return ret
    except IOError:
        with open("device_counter.txt", "w", encoding = 'utf-8') as file:
            file.write('0')
            file.close()
            return 0

### Resets device counter
def clearDevCounter():
    with open("device_counter.txt", 'w+', encoding = 'utf-8') as dev:
        dev.write('0')
        dev.close()
    loaded.set(0)

### Callback for updating IntVar variable represeting successful device programmings
def updateDevicesLoaded(*args):
    devicesLoaded.configure(text = ("Devices Loaded: " + str(loaded.get())).ljust(long_len))
    with open("device_counter.txt", 'w+', encoding = 'utf-8') as dev:
        dev.write(str(loaded.get()))
        dev.close()

### Adjusts one digit number to have appended beginning '0'
def adjustStationNum(num):
    if len(str(num)) == 1:
        return "0" + str(num)
    else:
        return str(num)

### Read the issue COM port and display status of that port
def getCOMProblem(e, stat):
    com_problem = re.findall(r'(?<=\').*?(?=\')', str(e))[0]
    addTextToLabel(stat.explanation, "\nCould not open " + com_problem)
    return 1

### high level applications which includes all relevant pieces and instances of
### Station class and other widgets
class Application:
    def __init__(self, parent):
        global loaded, devicesLoaded, long_len, completeIndSend

        self.communicationThread = threading.Thread(target = self.testMessages)
        completeIndSend = IntVar()
        completeIndSend.set(0)
        completeIndSend.trace('w', self.updateComVar)

        loaded = IntVar()
        loaded.set(getNumDevicesLoaded())
        loaded.trace("w", updateDevicesLoaded)
        s = ttk.Style()
        s.theme_use('default')
        s.configure("red.Horizontal.TProgressbar", foreground='red', background='red')
        s.configure("green.Horizontal.TProgressbar", foreground='green', background='green')
        self.parent = parent
        self.parent.title("CAN-232 Programmer")
        self.stations = []
        self.frame = tk.Frame(self.parent)
        self.configureMenu()
        self.titleLabel = tk.Label(self.frame, text = 'Details/Instructions', font = 10)
        self.instructions = tk.Label(self.frame, text = '- Programming stations \
are labelled with both COM ports listed in config.txt\n \
            - Click START to begin the upload and verification', pady = 5)
        devices = getCOMPorts()
        # Size of window based on how many stations are present
        root_width = max(700, (len(devices) - 1) * 205)
        self.parent.geometry(str(root_width) + "x900+20+20")
        self.can_com_text = StringVar()
        self.can_com_text.set(devices[0])
        self.can_com_text.trace("w", self.updateCommonPort)
        self.can_entry = tk.Entry(self.frame, width = entryWidth, textvariable = self.can_com_text)
        self.can_label = tk.Label(self.frame, text = "Shared CAN port: ")
        if not advanced:
            addTextToLabel(self.can_label, self.can_com_text.get())
        long_len = len(self.can_entry.get()) + len(self.can_label.cget("text"))
        devicesLoaded = tk.Label(self.frame, text = ("Devices Loaded: " + str(loaded.get())).ljust(long_len), pady = 10)
        self.buttonFrame = tk.Frame(self.frame)
        self.clearCounter = tk.Button(self.buttonFrame, text = "Clear Counter", width = int(long_len / 2), bg = gridColor, height = 2, command = clearDevCounter)
        self.start = tk.Button(self.buttonFrame, text = "START", width = long_len, bg = gridColor, height = 3, command = self.startUpload)
        self.configureModeOptions()
        self.configureDeviceOptions()
        self.packObjects()
        # d[0] is common port; begin Station initalization at 1, passing in unique station id
        for d in range(1, len(devices)):
            self.stations.append(Station(root, devices[d][0], devices[d][1], self.can_com_text, self.mode, d))

    ### Places objects on screen in correct format
    def packObjects(self):
        self.frame.pack(side = tk.TOP)
        self.titleLabel.pack()
        self.instructions.pack()
        self.can_label.pack(side = tk.LEFT)
        if advanced:
            self.can_entry.pack(side = tk.LEFT)
        self.deviceFrame.pack(side = tk.LEFT, padx = 10)
        self.clearCounter.pack(pady = 5)
        self.start.pack()
        self.buttonFrame.pack(side = tk.LEFT, padx = 20)
        devicesLoaded.pack(side = tk.RIGHT)
        self.modeFrame.pack(padx =10)


    ### Callback for updating IntVar variable represeting successful device programmings
    def updateCommonPort(self, *args):
        with open("Config\can_config.txt", 'w+', encoding = 'utf-8') as dev:
            dev.write(str(self.can_com_text.get()))
            dev.close()

    ### Create and "pack" menu for main root window
    def configureMenu(self):
        menubar = tk.Menu(self.parent)

        filemenu = tk.Menu(menubar, tearoff = 0)
        filemenu.add_command(label = "Open")
        filemenu.add_command(label = "Print")

        editmenu = tk.Menu(menubar, tearoff = 0)
        editmenu.add_command(label = "Undo")
        editmenu.add_command(label = "Redo")

        menubar.add_cascade(label = "File", menu = filemenu)
        menubar.add_cascade(label = "Edit", menu = editmenu)
        self.parent.configure(menu = menubar)

    ### Create mode options and pack into a frame
    def configureModeOptions(self):
        self.modeFrame = tk.Frame(self.frame)
        MODES = [
            ("Communicate All", "com"),
            ("Verify All", "v"),
            ("Program All", "p"),
            ("Custom", "c")
        ]
        self.mode = StringVar()
        self.mode.set("c")
        self.mode.trace("w", self.changeMode)
        for text, mode in MODES:
            b = tk.Radiobutton(self.modeFrame, text = text, value = mode, variable = self.mode)
            b.pack()

    ### Create device types options and pack into frame
    def configureDeviceOptions(self):
        self.deviceFrame = tk.Frame(self.frame)
        CONFIGS = [
            ("Normal", "normal"),
            ("Master", "master"),
            ("Slave", "slave")
        ]
        self.deviceType = StringVar()
        self.deviceType.set("normal")
        self.deviceType.trace("w", self.changeBaudRate)
        for text, devType in CONFIGS:
            b = tk.Radiobutton(self.deviceFrame, text = text, value = devType, variable = self.deviceType)
            b.pack()

    ### Changes global baud rate depending on device type
    def changeBaudRate(self, *args):
        global baudrate
        type = self.deviceType.get()
        if(type == "master" or type == "slave"):
            baudrate = 19200
        else:
            baudrate = 115200
        for stat in self.stations:
            stat.main_mod.baudrate = baudrate

    ### Trigger function for START button which begins/continues each Station thread
    def startUpload(self):
        for stat in self.stations:
            if not stat.thread.is_alive():
                stat.createNewThread()
                stat.changeAllComponents(tk.DISABLED)
                stat.tempCANTest = 1
                stat.tempSerialTest = 1

    ### Set the state and value of options given the current Mode
    def changeMode(self, *args):
        mo = self.mode.get() #The current mode (default vs custom)
        for stat in self.stations:
            if mo == "c":
                # Make editable if custom
                stat.changeAllComponents(tk.NORMAL)
            else:
                # Make uneditable if default
                dis = tk.DISABLED
                p = v = c = 1
                if mo == "com":
                    p = 0
                    v = 0
                elif mo == "v":
                    p = 0
                stat.changeProgramming(tk.DISABLED, p)
                stat.changeVerify(tk.DISABLED, v)
                stat.changeCommunicate(tk.DISABLED, c)

    ### Repeatable procedure to begin the communication test
    def testSerialToCAN(self):
        self.CAN = serial.Serial(self.can_com_text.get(), baudrate = baudrate, timeout = .1)
        localFail = 0
        for stat in self.stations:
            # Only perform the initial com test if the device has not already passed
            if stat.tempSerialTest:
                localFail += stat.startCommunication()
        message = readSerialWord(self.CAN)
        self.CAN.close()
        for stat in self.stations:
            # Only check if the CAN read is successful if device has not already passed
            if stat.tempSerialTest:
                num_str = adjustStationNum(stat.station_num)
                # Hex string representing each char from the station id
                firstChar = str(hex(ord(num_str[0])))
                secondChar = str(hex(ord(num_str[1])))
                # Check to see if each station id appears in message sent
                if firstChar[-2:] in message and secondChar[-2:] in message:
                    # Device DID NOT fail if successful CAN read
                    stat.tempSerialTest = 0
                    addTextToLabel(stat.explanation, " (Success)")
                else:
                    stat.tempSerialTest = 1
                    localFail += 1
                    addTextToLabel(stat.explanation, " (Fail)")
        # Returns if this individual CAN test failed
        return localFail

    ### Repeatable procedure to end communication test
    def testCANToSerial(self):
        self.CAN = serial.Serial(self.can_com_text.get(), baudrate = baudrate, timeout = .1)
        localFail = 0
        CANWrite = ":S"
        # Must specify what kind of CAN write should be done since
        # applicable devices may be of specific type
        if self.deviceType.get() == "master":
            CANWrite += master_recieve + "N31;"
        elif self.deviceType.get() == "slave":
            CANWrite += slave_recieve + "N31;"
        else:
            # Device is configured normally
            CANWrite += "123N00ABCD01;"
        for stat in self.stations:
            if stat.tempCANTest:
                # Open device port for reading if it has not passed the CAN write test
                stat.main_mod.open()
        self.CAN.write(CANWrite.encode())
        for stat in self.stations:
            # Perform the final verfication if device has not passed CAN test
            if stat.tempCANTest:
                stat.tempCANTest = stat.finishCommunication()
                stat.test_fail = stat.tempCANTest + stat.tempSerialTest
                if stat.test_fail:
                    localFail += 1
        self.CAN.close()
        return localFail


    ### Perform communication test e.g. round trip verifications between serial/CAN
    def testMessages(self):
        try:
            successes = []
            sleep(.2) #give ports time to leave boot mode
            failSerialToCAN = 1
            failCANToSerial = 1
            testCounter = 0
            # Perform each test up to 5 times, stopping if all devices pass that test
            while testCounter < 5 and failSerialToCAN != 0:
                failSerialToCAN = self.testSerialToCAN()
                testCounter += 1
            testCounter = 0
            while testCounter < 5 and failCANToSerial != 0:
                failCANToSerial = self.testCANToSerial()
                testCounter += 1
            for stat in self.stations:
                if not stat.test_fail:
                    addTextToLabel(stat.explanation, "\nSUCCESSFUL COMMUNICATION")
                else:
                    addTextToLabel(stat.explanation, "\nFAILED COMMUNICATION")
        except serial.SerialException as e:
            for stat in self.stations:
                getCOMProblem(e, stat)
                stat.test_fail = 1
        # Reset count of devices (triggers logging and resetting the device)
        completeIndSend.set(0)

    ### Checks how many devices have reached the point of a com test and acts accordingly
    def updateComVar(self, *args):
        complete = completeIndSend.get()
        if complete == len(self.stations):
            if not self.communicationThread.is_alive():
                self.communicationThread = threading.Thread(target = self.testMessages)
                self.communicationThread.start()
        elif complete == 0:
            # We have reset the variable and completed all testing
            # In this case, we must complete the cycle for each station
            for stat in self.stations:
                if stat.program.get() or stat.verify.get():
                    # Log results
                    stat.log_run(stat.flash_fail, stat.verify_fail, stat.test_fail)
                overallFail = stat.flash_fail + stat.verify_fail + stat.test_fail
                stat.stopProgressBar(overallFail)
                # Update successful iterations
                if not overallFail:
                    if stat.program.get():
                        loaded.set(loaded.get() + 1)
                    stat.currentStatus.configure(text = "SUCCESS")
                else:
                    stat.currentStatus.configure(text = "FAIL")
                if stat.mode.get() == "c":
                    stat.changeAllComponents(tk.NORMAL)

### Instantiate the root window and start the Application
if __name__ == "__main__":
    root = tk.Tk()
    a1 = Application(root)
    root.mainloop()
