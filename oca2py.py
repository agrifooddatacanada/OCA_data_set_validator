import json
from zipfile import ZipFile
import tkinter
from tkinter import filedialog
from pathlib import PurePath, PurePosixPath


tkinter.Tk().withdraw() # ignore empty tkinter window
bundle_path = PurePath(filedialog.askopenfilename(title = "Select OCA Bundle", filetypes = (("Compressed zip file","*.zip"), ("all files","*.*"))))
bundle_name = bundle_path.name.split('.')[0]

print(bundle_path)
with ZipFile(bundle_path, 'r') as bundle:
    with bundle.open(bundle_name + '/JSON/meta.json') as meta:
        print("meta found")
    # print(bundle.namelist()) 
    
