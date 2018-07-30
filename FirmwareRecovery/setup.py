import sys
import os
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
os.chdir("Firmware")
initial = os.listdir()
fileTup = ()
for file in initial:
    fileTup = fileTup + (r"Firmware\\" + file,)
includefiles = [fileTup, fileTup]
print(includefiles)
os.chdir("..")
build_exe_options = {"packages": ["os", "serial", "time", "xmodem", "logging"], "excludes": ["tkinter"], "include_files" : includefiles}
# GUI applications require a different base on Windows (the default is for a
# console application).

setup(  name = "recover",
        description = "My GUI application!",
        options = {"build_exe": build_exe_options},
        executables = [Executable("recover.py", base=None)])
