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

gridColor = "#20c0bb"
### class which details the specifics of each individual station programming
### threaded such that multiple Station instances can run simultaneously
class Station():
    def __init__(self, parent, prog_com_, out_com_, can_com_, stat_num):
        self.thread = threading.Thread(target = self.process)
        self.station_num = stat_num
        self.parent = parent
        self.prog_com = prog_com_
        self.out_com = out_com_
        self.can_com = can_com_
        self.deviceType = "GC-CAN-USB-COM"
        self.frame = tk.Frame(self.parent)
        self.initComponents()
        self.packObjects()

    ### Creates the components associated with a single Station instance
    def initComponents(self):
        self.instructions = tk.Label(self.frame, text = self.prog_com + "\\" + self.out_com)
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
    def changeAllCheckboxes(self, state_):
        self.chooseProgramming.configure(state = state_)
        self.chooseVerify.configure(state = state_)
        self.chooseCommunicate.configure(state = state_)

    ### Loads objects into correct places
    def packObjects(self):
        self.instructions.pack()
        self.statusSpace.pack()
        self.currentStatus.pack()
        self.progressBar.pack()
        self.explanation.pack()
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
                prog_com_number = self.prog_com.split("COM")[1]
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
                self.explanation.configure(text = "\nCould not open " + self.prog_com)
            return 1

    ### Check version number of firmware to make sure device was correctly programmed
    def performVerification(self):
        # Begin Verification
        self.currentStatus.configure(text = "Verification Stage")
        # Open serial port
        try:
            with serial.Serial(self.out_com, baudrate = 115200, timeout = .1) as buttonSer:
                addTextToLabel(self.explanation, "\n\nPress the button")
                #Check button push / boot mode
                checkMode = "start"
                while checkMode[2:] != "#0#":
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
                if "APP=2.01A" not in self.version:
                    addTextToLabel(self.explanation, "\n\nWRONG FIRMWARE VERSION")
                    return 1
                else:
                    addTextToLabel(self.explanation, "\nSUCCESSFUL VERIFICATION")
                    return 0
        except serial.SerialException as e:
            com_problem = re.findall(r'(?<=\').*?(?=\')', str(e))[0]
            addTextToLabel(self.explanation, "\nCould not open " + com_problem)
            return 1

    ### Test round trip communications (Serial -> CAN -> Serial)
    def testMessages(self):
        self.currentStatus.configure(text = "Testing Communication")
        try:
            num_loops = 50
            main_mod = serial.Serial(self.out_com, baudrate = 115200, timeout = .03)
            main_mod.write("exit\r".encode()) #ensure this port is in correct mode for communication
            CAN = serial.Serial(self.can_com, baudrate = 115200, timeout = .03)
            successes = 0
            for i in range(0, num_loops):
                # Send initial serial message
                main_mod.write(":S123N00ABCD00;".encode())
                # Recieve and verify incoming messages on other end
                CAN_recieve = readSerialWord(CAN)
                if(";" in CAN_recieve):
                    # If successful, write command back to original end
                    CAN.write(":S123N00ABCD00;".encode())
                    Ser_recieve = readSerialWord(main_mod)
                    if(";" in Ser_recieve):
                        # If recieved and verified, communication was successful
                        successes += 1
            CAN.close()
            main_mod.close()
            addTextToLabel(self.explanation, "\n\n"+str(successes)+"/"+str(num_loops)+" successes")
            # All communications must be successful
            if successes == num_loops:
                addTextToLabel(self.explanation, "\nSUCCESSFUL COMMUNICATION")
                return 0
            else:
                addTextToLabel(self.explanation, "\nFAILED COMMUNICATION")
                return 1

        except serial.SerialException as e:
            com_problem = re.findall(r'(?<=\').*?(?=\')', str(e))[0]
            addTextToLabel(self.explanation, "Could not open " + com_problem)
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
        flash_fail = verify_fail = test_fail = 0
        if self.program.get():
            # Run programming
            flash_fail = self.runFlashCommand()
        if self.verify.get():
            # Run version verification is successful
            if not flash_fail:
                verify_fail = self.performVerification()
        if self.communicate.get():
            # Run communication test if not failures
            if not flash_fail and not verify_fail:
                test_fail = self.testMessages()
        if self.program.get() or self.verify.get():
            # Log results
            self.log_run(flash_fail, verify_fail, test_fail)
        overallFail = flash_fail + verify_fail + test_fail
        self.stopProgressBar(overallFail)
        # Update successful iterations
        if not overallFail:
            if self.program.get():
                loaded.set(loaded.get() + 1)
            self.currentStatus.configure(text = "SUCCESS")
        else:
            self.currentStatus.configure(text = "FAIL")
        self.changeAllCheckboxes(tk.NORMAL)

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
    try:
        with open("config.txt", 'r+',encoding='utf-8' ) as mp:
            mp.readline() #first line is instructions
            devices = []
            devices.append(mp.readline().split()[0]) #first device is the common port
            for line in mp.readlines():
                ports = []
                for p in line.split():
                    # Add all COM ports associated with one device
                    if "COM" in p:
                        ports.append(p)
                devices.append(ports)
        return devices
    except IOError:
        messagebox.showinfo("IOError", "Missing config.txt file")
        with open("config.txt", "w+", encoding="utf-8") as file:
            file.write("COM1\nCOM2 COM3")

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
### high level applications which includes all relevant pieces and instances of
### Station class and other widgets
class Application:
    def __init__(self, parent):
        global loaded, devicesLoaded, long_len
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
        root_width = max(410, (len(devices) - 1) * 205)
        self.parent.geometry(str(root_width) + "x700")
        self.can_com_text = StringVar()
        self.can_com_text.set(devices[0])
        self.can_entry = tk.Entry(self.frame, width = 10, textvariable = self.can_com_text)
        self.can_label = tk.Label(self.frame, text = "Shared CAN port: ")
        long_len = len(self.can_entry.get()) + len(self.can_label.cget("text"))
        devicesLoaded = tk.Label(self.frame, text = ("Devices Loaded: " + str(loaded.get())).ljust(long_len), pady = 10)
        self.clearCounter = tk.Button(self.frame, text = "Clear Counter", width = int(long_len / 2), bg = gridColor, height = 2, command = clearDevCounter)
        self.start = tk.Button(self.frame, text = "START", width = long_len, bg = gridColor, height = 3, command = self.startUpload)
        self.packObjects()
        # d[0] is common port; begin Station initalization at 1, passing in unique station id
        for d in range(1, len(devices)):
            self.stations.append(Station(root, devices[d][0], devices[d][1], self.can_com_text.get(), d))

    ### Places objects on screen in correct format
    def packObjects(self):
        self.frame.pack(side = tk.TOP)
        self.titleLabel.pack()
        self.instructions.pack()
        self.clearCounter.pack(pady = 5)
        self.start.pack()
        self.can_label.pack(side = tk.LEFT)
        self.can_entry.pack(side = tk.LEFT)
        devicesLoaded.pack(side = tk.RIGHT)

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

    ### Trigger function for START button which begins/continues each Station thread
    def startUpload(self):
        for stat in self.stations:
            if not stat.thread.is_alive():
                stat.createNewThread()
                stat.changeAllCheckboxes(tk.DISABLED)

### Instantiate the root window and start the Application
if __name__ == "__main__":
    root = tk.Tk()
    a1 = Application(root)
    root.mainloop()
