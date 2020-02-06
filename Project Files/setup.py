application_title = "Lost Ship" #what you want to application to be called
main_python_file = "lost_ship.py" #the name of the python file you use to run the program

import sys
from cx_Freeze import setup, Executable

base = None
if sys.platform == "win32":
    base = "Win32GUI"

includes = ["atexit","re"]

setup(
name = application_title,
version = "0.1",
description = "A PyGame game",
options = {"build_exe" : {"includes" : includes }},
executables = [Executable(main_python_file, base = base)])