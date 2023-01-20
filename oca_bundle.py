# oca_bundle.py

from zipfile import ZipFile
import json
from pathlib import Path


META_FILE = "meta.json"
CB_NAME = "capture_base"
CB_KEY = "root"
FILES_KEY = "files"


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
        bundle_path = Path(path_str)
        
        # The OCA bundle file name without extension.
        # This was for navigating in the zip file. Currently not used.
        bundle_name = bundle_path.name.rsplit(".", 1)[0]    

        with ZipFile(bundle_path, "r") as bundle:
            # Loads meta file.
            with bundle.open(META_FILE) as meta_json:
                self.meta = json.load(meta_json)

            # Loads all other files, including capture base and overlays.
            self.files_dict = self.meta[FILES_KEY][self.meta[CB_KEY]]
            self.files_dict[CB_NAME] = self.meta[CB_KEY]
            for file_name in self.files_dict.values():
                with bundle.open(file_name + ".json") as file:
                    self.files[file_name] = json.load(file)

    def get_file(self, file_name):
        if file_name == "meta":
            return self.meta
        elif file_name in self.files_dict:
            return self.files[self.files_dict[file_name]]            
        else:
            raise Exception("Wrong file name")


if __name__ == "__main__":

    example_path = "../OCA_test_sets/Example_data_1.zip"
    oca_example = OCABundle(example_path)
    while True:
        print(oca_example.get_file(input()))
