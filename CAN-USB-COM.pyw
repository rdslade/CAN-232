import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from time import sleep
import serial
import sys

class Station:
    def __init__(self, parent, prog_com_, out_com_):
        self.parent = parent
        self.prog_com = prog_com_
        self.out_com = out_com_
        self.frame = tk.Frame(self.parent)
        self.initComponents()
        self.packObjects()

    def initComponents(self):
        self.instructions = tk.Label(self.frame, text = self.prog_com + "\\" + self.out_com)
        self.statusSpace = tk.LabelFrame(self.frame, width = 200, height = 250)
        self.currentStatus = tk.Label(self.statusSpace, text = "Current Status", width = 25, pady = 10)
        self.progressBar = ttk.Progressbar(self.statusSpace, mode = 'determinate', length = 125)

    def packObjects(self):
        self.instructions.pack()
        self.statusSpace.pack()
        self.currentStatus.pack()
        self.progressBar.pack()
        self.frame.pack(side = tk.LEFT, padx = 10)

    def startUpload(self):
        self.currentStatus.configure(text = "Configuring executables")
        self.progressBar.start(100);
        ## Configure command text file
        with open('CANUSB_CommandFile.txt', 'r+', encoding = 'utf-8') as command:
            command.seek(4)
            prog_com_number = self.prog_com.split("COM")[1]
            if(len(prog_com_number) == 1):
                prog_com_number = '0'+prog_com_number
            command.write(prog_com_number)

        ## Get magic flash commands ready
        flash_magic_cmd = "CANUSB_Flash.bat"
        try:
            p = subprocess.check_output([flash_magic_cmd], shell=True, stderr=subprocess.STDOUT)
            p = p.decode("utf-8")
            #messagebox.showinfo("good", p)
        except subprocess.CalledProcessError as e:
            messagebox.showinfo("bad", e.output)
        self.currentStatus.configure(text = "Loading firmware")

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
        for d in devices:
            self.stations.append(Station(root, d[0], d[1]))

    def packObjects(self):
        self.titleLabel.pack()
        self.instructions.pack()
        self.frame.pack()
        self.start.pack()

    def startUpload(self):
        for stat in self.stations:
            stat.startUpload()
if __name__ == "__main__":
    root = tk.Tk()
    a1 = Application(root)
    root.mainloop()
