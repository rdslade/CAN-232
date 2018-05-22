import subprocess
import tkinter as tk
from tkinter import messagebox
from time import sleep
import serial

class Port:
    def __init__(self, parent, prog_com_, out_com_):
        self.parent = parent
        self.prog_com = prog_com_
        self.out_com = out_com_
        self.frame = tk.Frame(self.parent)
        self.initTitle()
        self.packObjects()

    def initTitle(self):
        self.instructions = tk.Label(self.frame, text = self.prog_com + "\\" + self.out_com)
        self.statusSpace = tk.LabelFrame(self.frame, width = 200, height = 250)

    def packObjects(self):
        self.instructions.pack()
        self.statusSpace.pack()
        self.frame.pack(side = tk.LEFT, padx = 10)

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
        self.frame = tk.Frame(self.parent)
        self.titleLabel = tk.Label(self.frame, text = 'Details/Instructions', font = ("Times", 16))
        self.instructions = tk.Label(self.frame, text = '- Programming stations \
are labelled with both COM ports listed in config.txt\n \
            - Click START to begin the upload and verification')
        self.start = tk.Button(self.frame, text = "START", width = 10, height = 2);
        self.packObjects()
        devices = getCOMPorts()
        for d in devices:
            Port(root, d[0], d[1])
    def packObjects(self):
        self.titleLabel.pack()
        self.instructions.pack()
        self.frame.pack()
        self.start.pack()

if __name__ == "__main__":
    root = tk.Tk()
    a1 = Application(root)
    root.mainloop()
