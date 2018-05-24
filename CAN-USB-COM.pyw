import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter import IntVar
from time import sleep
import serial
import sys
import time
import datetime
import threading
from multiprocessing import Queue, Process

class Station():
    def __init__(self, parent, prog_com_, out_com_, can_com_, stat_num):
        self.thread = threading.Thread(target = self.run)
        self.station_num = stat_num
        self.parent = parent
        self.prog_com = prog_com_
        self.out_com = out_com_
        self.can_com = can_com_
        self.deviceType = "GC-CAN-USB-COM"
        self.frame = tk.Frame(self.parent)
        self.initComponents()
        self.packObjects()

    def initComponents(self):
        self.instructions = tk.Label(self.frame, text = self.prog_com + "\\" + self.out_com)
        self.statusSpace = tk.LabelFrame(self.frame, width = 200, height = 250)
        self.currentStatus = tk.Label(self.statusSpace, text = "", width = 25, pady = 10)
        self.progressBar = ttk.Progressbar(self.statusSpace, mode = 'determinate', length = 125)
        self.explanation = tk.Label(self.statusSpace, text = "", width = 25, pady = 10)

    def packObjects(self):
        self.instructions.pack()
        self.statusSpace.pack()
        self.currentStatus.pack()
        self.progressBar.pack()
        self.explanation.pack()
        self.frame.pack(side = tk.LEFT, padx = 10)

    def configureTextFiles(self):
        ## Configure command text file
        self.currentStatus.configure(text = "Configuring executables")
        try:
            file_name = r'CANUSB_Config\CANUSB_CommandFile'+str(self.station_num)+'.txt'
            with open(file_name, 'r+', encoding = 'utf-8') as command:
                command.seek(4)
                prog_com_number = self.prog_com.split("COM")[1]
                if(len(prog_com_number) == 1):
                    prog_com_number = '0'+prog_com_number
                command.write(prog_com_number)
        except FileIO:
            messagebox.showinfo("IOError", "Cannot open CANUSB_CommandFile.txt")

    def runFlashCommand(self):
        ## Get magic flash commands ready
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
            self.stopProgressBar(1)
            self.currentStatus.configure(text = "FAIL")
            self.explanation.configure(text = "Could not open serial port(s)")
            return 1

    def verify(self):
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
            addTextToLabel(self.explanation, "\n\nCould not open serial port(s)")
            return 1

    def testMessages(self):
        self.currentStatus.configure(text = "Testing Communication")
        addTextToLabel(self.explanation, "\n")
        try:
            num_loops = 50
            main_mod = serial.Serial(self.out_com, baudrate = 115200, timeout = .03)
            main_mod.write("exit\r".encode()) #ensure this port is in correct mode for communication
            CAN = serial.Serial(self.can_com, baudrate = 115200, timeout = .03)
            successes = 0
            for i in range(0, num_loops):
                main_mod.write(":S123N00ABCD00;".encode())
                CAN_recieve = readSerialWord(CAN)
                if(";" in CAN_recieve):
                    CAN.write(":S123N00ABCD00;".encode())
                    successes += 1
            CAN.close()
            main_mod.close()
            addTextToLabel(self.explanation, "\n"+str(successes)+"/"+str(num_loops)+" successes")
            if successes == num_loops:
                addTextToLabel(self.explanation, "\nSUCCESSFUL COMMUNICATION")
                self.currentStatus.configure(text = "SUCCESS")
                return 0
            else:
                addTextToLabel(self.explanation, "\nFAILED COMMUNICATION")
                self.currentStatus.configure(text = "FAIL")
                return 1

        except serial.SerialException as e:
            addTextToLabel(self.explanation, "\n\nCould not open serial port(s)")
            return 1

    def log_run(self, flash, verify, comm):
        full_date = str(datetime.datetime.now())
        log_str = full_date + " "
        if(not flash and not verify and not comm):
            log_str += self.sernum + " " + self.version + " " + self.deviceType + "SUCCESS"
            log_filename = r"Log\success.txt"
        else:
            log_str += "ERROR- "
            if flash:
                log_str += "Loading firmware"
            if verify:
                log_str += "Verification"
            if comm:
                log_str += "Communication"
            log_filename = r"Log\fail.txt"
            log_str += "\n"
        with open(log_filename, 'a+',encoding='utf-8') as log:
            log.write(log_str)
            log.close()

    def stopProgressBar(self, fail):
        self.progressBar.stop()
        if not fail:
            self.progressBar.configure(value = 100, style = "green.Horizontal.TProgressbar")
        else:
            self.progressBar.configure(value = 100, style = "red.Horizontal.TProgressbar")

    def restartProgressBar(self):
        self.progressBar.configure(value = 0, style = "Horizontal.TProgressbar")
        self.progressBar.start()

    def run(self):
        self.restartProgressBar()
        self.explanation.configure(text = "")
        self.configureTextFiles()
        flash_fail = verify_fail = test_fail = 0
        flash_fail = self.runFlashCommand()
        if not flash_fail:
            verify_fail = self.verify()
        if not flash_fail and not verify_fail:
            test_fail = self.testMessages()
        self.log_run(flash_fail, verify_fail, test_fail)
        overallFail = flash_fail + flash_fail + test_fail
        self.stopProgressBar(overallFail)
        if not overallFail:
            loaded.set(loaded.get() + 1)

    def createNewThread(self):
        self.thread = threading.Thread(target = self.run)
        self.thread.start()

# Helper function for reading serial words
def readSerialWord(ser_port):
    char = '0'
    response = ""
    while char != '':
        char = ser_port.read().decode()
        response += char
    return response

def addTextToLabel(label, textToAdd):
    label.configure(text = label.cget("text") + textToAdd);

def getCOMPorts():
    try:
        with open("config.txt", 'r',encoding='utf-8' ) as mp:
            mp.readline()
            devices = []
            devices.append(mp.readline().split()[0])
            for line in mp.readlines():
                ports = []
                for p in line.split():
                    if "COM" in p:
                        ports.append(p)
                devices.append(ports)
        return devices
    except IOError:
        messagebox.showinfo("IOError", "Missing config.txt file")

def getNumDevicesLoaded():
    try:
        with open("device_counter.txt", 'r+', encoding = 'utf-8') as dev:
            return int(dev.readline())
    except IOError as e:
        with open("device_counter.txt", "w", encoding = 'utf-8') as file:
            file.write('0')
            return 0

def updateDevicesLoaded(*args):
    devicesLoaded.configure(text = ("Devices Loaded: " + str(loaded.get())).ljust(long_len))
    with open("device_counter.txt", 'w+', encoding = 'utf-8') as dev:
        dev.write(str(loaded.get()) + "\n")

class Application:
    def __init__(self, parent):
        global loaded, devicesLoaded, long_len
        loaded = IntVar()
        loaded.set(getNumDevicesLoaded())
        loaded.trace("w", updateDevicesLoaded)
        self.parent = parent
        self.parent.title("CAN-232 Programmer")
        self.parent.geometry("600x400")
        self.stations = []
        self.frame = tk.Frame(self.parent)
        self.titleLabel = tk.Label(self.frame, text = 'Details/Instructions', font = 10)
        self.instructions = tk.Label(self.frame, text = '- Programming stations \
are labelled with both COM ports listed in config.txt\n \
            - Click START to begin the upload and verification', pady = 10)
        devices = getCOMPorts()
        can_com = devices[0]
        self.can_label = tk.Label(self.frame, text = "Shared CAN port: " + can_com)
        long_len = len(self.can_label.cget("text"))
        devicesLoaded = tk.Label(self.frame, text = ("Devices Loaded: " + str(loaded.get())).ljust(long_len), pady = 10)
        self.start = tk.Button(self.frame, text = "START", width = long_len, bg = "#20c0bb", height = 3, command = self.startUpload)
        self.packObjects()
        for d in range(1, len(devices)):
            self.stations.append(Station(root, devices[d][0], devices[d][1], can_com, d))

    def packObjects(self):
        self.frame.pack(side = tk.TOP)
        self.titleLabel.pack()
        self.instructions.pack()
        self.start.pack()
        self.can_label.pack(side = tk.LEFT)
        devicesLoaded.pack(side = tk.RIGHT)

    def startUpload(self):
        loaded.set(loaded.get() + 1)
        for stat in self.stations:
            if not stat.thread.is_alive():
                stat.createNewThread()


if __name__ == "__main__":
    root = tk.Tk()
    a1 = Application(root)
    s = ttk.Style()
    s.theme_use('default')
    s.configure("red.Horizontal.TProgressbar", foreground='red', background='red')
    s.configure("green.Horizontal.TProgressbar", foreground='green', background='green')
    root.mainloop()
