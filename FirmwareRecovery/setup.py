import sys
import os
from cx_Freeze import setup, Executable
from pathlib import Path

# Dependencies are automatically detected, but it might need fine tuning.
os.chdir("Firmware")
initial = os.listdir()
includefiles = []
folder = Path("Firmware")
for file in initial:
    fullFile = folder / file
    twotup = (fullFile,) + (fullFile,)
    includefiles.append(twotup)
print(includefiles)
os.chdir("..")
build_exe_options = {"packages": ["os", "serial", "time", "xmodem", "logging", "re"], "excludes": ["tkinter"], "include_files" : includefiles}
# GUI applications require a different base on Windows (the default is for a
# console application).

setup(  name = "recover",
        description = "My GUI application!",
        options = {"build_exe": build_exe_options},
        executables = [Executable("recover.py", base=None)])
