import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from time import sleep
import serial
import sys
import time
import threading
from multiprocessing import Queue, Process


class Station():
    def __init__(self, parent, prog_com_, out_com_, stat_num):
        self.thread = threading.Thread(target = self.run)
        self.station_num = stat_num
        self.parent = parent
        self.prog_com = prog_com_
        self.out_com = out_com_
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

    def verification(self):
        # Begin Verification
        self.currentStatus.configure(text = "Verification Stage")
        # Helper function for reading serial words
        def readSerialWord(ser_port):
            char = '0'
            response = ""
            while char != '':
                char = ser_port.read().decode()
                response += char
            return response
        # Open serial port
        try:
            with serial.Serial(self.out_com, baudrate = 115200, timeout = .1) as buttonSer:
                addTextToLabel(self.explanation, "\n\nPress the button")

                checkMode = "start"
                while checkMode[2:] != "#0#":
                    buttonSer.write("\n\r".encode())
                    checkMode = readSerialWord(buttonSer)

                addTextToLabel(self.explanation, "\nButton Pressed\nVerifying Firmware Version")

                buttonSer.write("get version\r".encode())
                version = readSerialWord(buttonSer)
                buttonSer.close()
                if "APP=2.01A" not in version:
                    addTextToLabel(self.explanation, "\n\nWRONG FIRMWARE VERSION")
                    self.currentStatus.configure(text = "FAIL")
                    return 1
                else:
                    addTextToLabel(self.explanation, "\nSUCCESSFUL VERIFICATION")
                    self.currentStatus.configure(text = "SUCCESS")
                    return 0
        except SerialException as e:
            addTextToLabel(self.explanation, "\n\nCould not open serial port(s)")

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
        fail = self.runFlashCommand()
        if not fail:
            self.stopProgressBar(self.verification())

    def createNewThread(self):
        self.thread = threading.Thread(target = self.run)
        self.thread.start()
def addTextToLabel(label, textToAdd):
    label.configure(text = label.cget("text") + textToAdd);
def getCOMPorts():
    try:
        with open("config.txt", 'r',encoding='utf-8' ) as mp:
            mp.readline()
            devices = []
            for line in mp.readlines():
                ports = []
                for p in line.split():
                    if "COM" in p:
                        ports.append(p)
                devices.append(ports)
        return devices
    except IOError:
        messagebox.showinfo("IOError", "Missing config.txt file")

class Application:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("CAN-232 Programmer")
        self.parent.geometry("600x400")
        self.stations = []
        self.frame = tk.Frame(self.parent)
        self.titleLabel = tk.Label(self.frame, text = 'Details/Instructions', font = ("Times", 16))
        self.instructions = tk.Label(self.frame, text = '- Programming stations \
are labelled with both COM ports listed in config.txt\n \
            - Click START to begin the upload and verification')
        self.start = tk.Button(self.frame, text = "START", width = 10, height = 2, command = self.startUpload);
        self.packObjects()
        devices = getCOMPorts()
        i = 0
        for d in devices:
            self.stations.append(Station(root, d[0], d[1], i))
            i += 1

    def packObjects(self):
        self.titleLabel.pack()
        self.instructions.pack()
        self.frame.pack()
        self.start.pack()

    def startUpload(self):
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
