# oca2py.py

from zipfile import ZipFile
import json
from pathlib import PurePath, PurePosixPath


# A loaded OCA bundle from OCA zip files. 
class OCABundle:

    meta = {}
    files = {}
    files_dict = {}

    # Load an OCA bundle.
    # path_str: String. File path to the OCA bundle zip file. 
    #           Both kinds of slash works. 
    def __init__(self, path_str):

        ######################################################################
        # if FILE_EXPLORER_SELECTION:
        #     # Choose zip file in file explorer.
        #     import tkinter
        #     from tkinter import filedialog
        #     tkinter.Tk().withdraw() # ignore empty tkinter window
        #     path_str = filedialog.askopenfilename(
        #         title = "Select OCA Bundle", 
        #         filetypes = (("compressed zip file","*.zip"), 
        #                      ("all files","*.*")))
        ######################################################################

        # Slash auto correction based on current system.
        bundle_path = PurePath(path_str)
        
        # The OCA bundle file name without extension.
        bundle_name = bundle_path.name.rsplit(".", 1)[0]    
        
        meta_path = bundle_name + "/JSON/meta.json"
        files_path = bundle_name + "/JSON/"

        with ZipFile(bundle_path, "r") as bundle:
            # Loads meta file.
            with bundle.open(meta_path) as meta_json:
                self.meta = json.load(meta_json)

            # Loads all other files, including capture base and overlays.
            self.files_dict = self.meta["files"][self.meta["root"]]
            for file_name in self.files_dict.values():
                with bundle.open(files_path + file_name + ".json") as file:
                    self.files[file_name] = json.load(file)

    def get_file(self, file_name):
        if file_name == "meta":
            return self.meta
        elif file_name in self.files_dict:
            return self.files[self.files_dict[file_name]]            
        else:
            # error
            pass


if __name__ == "__main__":

    bee_example_path = "../OCA test sets/Example_data_bee.zip"
    oca_bee_example = OCABundle(bee_example_path)
    while True:
        print(oca_bee_example.get_file(input()))
