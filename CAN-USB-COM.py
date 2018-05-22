import subprocess
import tkinter as tk
from tkinter import messagebox
from time import sleep
import serial

class Port:
    def __init__(self, parent, comin):
        self.parent = parent
        self.com = comin
        self.frame = tk.Frame(self.parent)
        self.initTitle()
        self.packObjects()

    def initTitle(self):
        self.instructions = tk.Label(self.frame, text = self.com)
        self.statusSpace = tk.LabelFrame(self.frame, text = 'START', width = 100, height = 200)

    def packObjects(self):
        self.instructions.pack()
        self.statusSpace.pack()
        self.frame.pack(side = tk.LEFT, padx = 10)

def getCOMPorts():
    try:
        with open("config.txt", 'r',encoding='utf-8' ) as mp:
            line = mp.readline()
            ports = []
            for p in line.split():
                if "COM" in p:
                    ports.append(p)
        return ports
    except IOError:
        messagebox.showinfo("IOError", "Missing config.txt file")

class Application:
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(self.parent)
        self.label = tk.Label(self.frame, text = "Instructions")
        self.label.pack()
        self.frame.pack()
        ports = getCOMPorts()
        for p in ports:
            Port(root, p)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("CAN-232 Programmer")
    root.geometry("600x300")
    a1 = Application(root)
    root.mainloop()
