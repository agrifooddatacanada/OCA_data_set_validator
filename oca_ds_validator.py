from zipfile import ZipFile
import json
from pathlib import Path

import pandas as pd

from datetime import datetime
import re


META_FILE = "meta.json"
CB_NAME = "capture_base"
CB_KEY = "root"
FILES_KEY = "files"
ATTR_NAME = "attributes"
FORMAT_NAME = "format"
ATTR_FORMAT_NAME = "attribute_formats"
EC_NAME = "entry_code"
ATTR_EC_NAME = "attribute_entry_codes"

DATA_ENTRY_SHEET_NAME = "schema conformant data"


class OCADataSet:
    
    def __init__(self, ds_pd: pd.DataFrame = pd.DataFrame()):
        self.data = ds_pd
    
    @classmethod
    def from_path(cls, ds_path_str: str):
        ds_path = Path(ds_path_str)
        if ".xls" in ds_path.name:
            return cls(pd.read_excel(ds_path, sheet_name = DATA_ENTRY_SHEET_NAME))
        elif ".csv" in ds_path.name:
            return cls(pd.read_csv(ds_path))
        else:
            raise Exception("Not supported data set file type")
    

# A loaded OCA bundle from OCA zip files. 
class OCABundle:

    # Load an OCA bundle.
    # path_str: String. File path to the OCA bundle zip file. 
    #           Both kinds of slash works. 
    def __init__(self, bundle_path_str):
        
        self.meta = {}
        self.files = {}
        self.files_dict = {}
        
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
        bundle_path = Path(bundle_path_str)
        
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
    
    def get_attributes(self):
        return self.get_file(CB_NAME)[ATTR_NAME]

    def get_attribute_type(self, attribute_name):
        return self.get_attributes()[attribute_name]
    
    def get_attribute_format(self, attribute_name):
        return self.get_file(FORMAT_NAME)[ATTR_FORMAT_NAME][attribute_name]

    def get_entry_codes(self):
        return self.get_file(EC_NAME)[ATTR_EC_NAME]

    def validate_format(self, data_set: OCADataSet):
        for attr in self.get_attributes():
            attr_type = self.get_attribute_type(attr)
            attr_format = self.get_attribute_format(attr)
            for data_entry in data_set.data[attr]:
                if pd.isna(data_entry):
                    pass 
                elif attr_type == "DateTime":
                    if not match_datetime(attr_format, data_entry):
                        print("Not matching on column", attr, "with data", data_entry)
                elif attr_type == "Numeric" or attr_type == "Text":
                    if not match_regex(attr_format, str(data_entry)):
                        print("Not matching on column", attr, "with data", data_entry)
                elif attr_type == "Boolean":
                    if not match_boolean(data_entry):
                        print("Not matching on column", attr, "with data", data_entry)
                else:
                    pass
    
    def validate_entry_code(self, data_set: OCADataSet):
        attr_entry_codes = self.get_entry_codes()
        for attr in attr_entry_codes:
            for data_entry in data_set.data[attr]:
                if str(data_entry) not in attr_entry_codes[attr]:
                    print(data_entry, "on column", attr, "is not a entry code")

    def flagged_alarm(self, data_set: OCADataSet):
        if "flagged_attributes" in self.get_file(CB_NAME):
            for attr in self.get_file(CB_NAME)["flagged_attributes"]:
                print("Contains flagged data. Check", attr)

    def validate(self, data_set: OCADataSet):
        print(data_set.data)
        self.flagged_alarm(data_set)
        set_valid = True
        if not self.validate_format(data_set):
            set_valid = False
        if not self.validate_entry_code(data_set):
            set_valid = False
        return set_valid


def match_datetime(pattern, data_str):

    def iso2py(iso_str):
        iso_conv = {
            "YYYY": "%Y", "MM": "%m", 
            "DDD": "%j", "DD": "%d", "D": "%w", "ww": "%W",
            "+hh:mm": "%z", "-hh:mm": "%z", "+hhmm": "%z", "-hhmm": "%z",
            "Z": "%z", 
            "hh": "%H", "mm": "%M", "sss": "%f", "ss": "%S"
        }
        py_str = iso_str
        for i in iso_conv:
            py_str = py_str.replace(i, iso_conv[i])
        return py_str
    # to do: duration 
    pattern = iso2py(pattern)
    try:
        datetime.strptime(data_str, pattern)
    except:
        return False
    return True

def match_regex(pattern, data_str):
    return bool(re.search(pattern, data_str))

def match_boolean(data_str):
    return data_str in ["True",  "true",  "T", "t", "1", "y", "yes", 
                        "False", "false", "F", "f", "0", "n", "no"]


xls_path = "../OCA_test_sets/Example_data_bee/test_data_set.xlsx"
csv_path = "../OCA_test_sets/Example_data_bee/test_data_set.csv"
bundle_path = "../OCA_test_sets/Example_data_bee/test_bundle.zip"

bd1 = "../"
bd2 = "../"

csv1 = "../"
csv2 = "../"


if __name__ == "__main__":
    test_bd = OCABundle(bundle_path)
    # test_bd.validate(OCADataSet.from_path(xls_path))
    test_bd.validate(OCADataSet.from_path(csv_path))
    # test_bd.validate(OCADataSet(pd.read_csv(csv_path)))

    py_bd1 = OCABundle(bd1)
    py_bd2 = OCABundle(bd2)

    py_csv1 = OCADataSet.from_path(csv1) 
    py_csv2 = OCADataSet.from_path(csv2) 

    py_bd1.validate(py_csv1)
    py_bd2.validate(py_csv2)

