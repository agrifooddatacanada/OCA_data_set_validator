from zipfile import ZipFile
import json
from pathlib import Path

import pandas as pd

from datetime import datetime
import re

##############################################################################
# Author: Xingjian Xu from Agri-food Data Canada 
#                          (https://agrifooddatacanada.ca/)
# 
# Created with support by Agri-food Data Canada, funded by CFREF through the 
# Food from Thought grant held at the University of Gueph.
# We do not provide any warranty of any kind regarding the accuracy, security,
# completeness or reliability of this script or any of its parts.
# 
# You can redistribute and/or modify this script under the terms of the EUPL
# (European Union Public License), version 1.2, as published by the Human 
# Colossus Foundation (https://humancolossus.foundation/).
##############################################################################

# The version number of the OCA Technical Specification which this script is
# developed for. See https://oca.colossi.network/specification/
OCA_VERSION = "1.0"

# Names of OCA bundle dictionary keys.
# Do not change unless there are any key errors.
META_FILE = "meta.json"
CB_KEY = "capture_base"
ROOT_KEY = "root"
FILES_KEY = "files"
TYPE_KEY = "type"
ATTR_KEY = "attributes"
FORMAT_KEY = "format"
ATTR_FORMAT_KEY = "attribute_formats"
CONF_KEY = "conformance"
ATTR_CONF_KEY = "attribute_conformance"
EC_KEY = "entry_code"
ATTR_EC_KEY = "attribute_entry_codes"
FLAG_KEY = "flagged_attributes"

# The tab name in the Excel Data Entry File.
# Do not change unless there are any Excel parsing errors.
DATA_ENTRY_SHEET_KEY = "schema conformant data"

# Error messages. For text notices only.
MISSING_MSG = "Missing mandatory attribute."
NOT_A_LIST_MSG = "Valid array required."
FORMAT_ERR_MSG = "Format mismatch."
EC_ERR_MSG = "One of the entry codes required."


# The class represents an OCA Data Set to be validated.
class OCADataSet:
    
    # (Defaultly) Load an OCA data set from pandas Data Frame.
    def __init__(self, ds_pd: pd.DataFrame = pd.DataFrame()):
        self.data = ds_pd
    
    # Load an OCA data set from OCA Excel Data Entry File or csv file.
    @classmethod
    def from_path(cls, ds_path_str: str):
        ds_path = Path(ds_path_str)
        if ".xls" in ds_path.name:  # .xls or .xlsx
            return cls(pd.read_excel(ds_path, 
                                     sheet_name = DATA_ENTRY_SHEET_KEY))
        elif ".csv" in ds_path.name:
            return cls(pd.read_csv(ds_path))
        else:
            raise Exception("Not supported data set file type")
    

# The class represents a result set for any kind of OCA Data Set Validation.
class OCADataSetErr:
    
    # Missing or misnamed attributes
    class AttributeErr:
        def __init__(self):
           self.errs = [] 
    # Attribute type or attribute format errors
    class FormatErr:
        def __init__(self):
           self.errs = {}  
    # Not matching any of the entry codes
    class EntryCodeErr:
        def __init__(self):
           self.errs = {} 

    def __init__(self):

        self.attr_err = OCADataSetErr.AttributeErr()
        self.format_err = OCADataSetErr.FormatErr()
        self.ecode_err = OCADataSetErr.EntryCodeErr() 

        self.err_cols = set()
        self.err_rows = set()

    # Minimal error information. Could be effective when there are only a few
    # errors in a few attributes.
    def overview(self):
        self.update_err()
        if ((not self.attr_err.errs) and
            (not self.err_cols) and
            (not self.err_rows)):
            print("No error was found.")
        if self.attr_err.errs:
            print("Attribute error. Check OCA bundle for", attr_err.errs, ".")
        if self.err_cols or self.err_rows:
            print("Found", len(self.err_rows), 
                  "problematic row(s) in the following column(s):", self.err_cols)  
        print()

    # Detailed error information about the first column with errors.
    def first_err_col(self):
        self.update_err()
        if not self.err_cols:
            print("No error was found.")
        else:
            first_col = sorted(list(self.err_cols))[0]
            print("The first problematic column is:", first_col)
            self.get_err_col(first_col)
        print()

    # Updates the problematic column and row information.
    def update_err(self):
        for ec in self.format_err.errs:
            for i in self.format_err.errs[ec]:
                self.err_rows.add(i)
            if self.format_err.errs[ec]:
                self.err_cols.add(ec)
        for ec in self.ecode_err.errs:
            for i in self.ecode_err.errs[ec]:
                self.err_rows.add(i)
            if self.ecode_err.errs[ec]:
                self.err_cols.add(ec)
    # Returns the error detail dictionary for format values.
    def get_format_err(self):
        return self.format_err.errs
    # Returns the error detail dictionary for entry codes.
    def get_ecode_err(self):
        return self.ecode_err.errs

    # Prints the error detail for a certain column.
    def get_err_col(self, attr_name):
        self.update_err()
        if not self.err_cols:
            print("No error was found.")
        else:
            if attr_name in self.get_format_err():
                print("Format error(s) would occur in the following rows:")
                for row in self.get_format_err()[attr_name]:
                    print("row", row, ":", self.get_format_err()[attr_name][row])
            else:
                print("No format error found in the column.")

            if attr_name in self.get_ecode_err():
                print("Entry code error(s) would occur in the following rows:")
                for row in self.get_ecode_err()[attr_name]:
                    print("row", row, ":", self.get_ecode_err()[attr_name][row])
            else:
                print("No entry code error found in the column.")

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

        # Slash auto correction based on the current system.
        bundle_path = Path(bundle_path_str)
        
        # The OCA bundle file name without extension.
        # This was for navigating in the zip file. Currently not used.
        bundle_name = bundle_path.name.rsplit(".", 1)[0]    

        with ZipFile(bundle_path, "r") as bundle:
            # Loads meta file.
            with bundle.open(META_FILE) as meta_json:
                self.meta = json.load(meta_json)

            # Loads all other files, including capture base and overlays.
            self.files_dict = self.meta[FILES_KEY][self.meta[ROOT_KEY]]
            self.files_dict[CB_KEY] = self.meta[ROOT_KEY]
            for file_name in self.files_dict.values():
                with bundle.open(file_name + ".json") as file:
                    self.files[file_name] = json.load(file)
    
    # Produces a dictionary of JSON file of file_name.
    def get_file(self, file_name):
        if file_name == "meta":
            return self.meta
        elif file_name in self.files_dict:
            return self.files[self.files_dict[file_name]]            
        else:
            raise Exception("Wrong file name")
    
    # Gets the OCA spec version number from overlay type.
    def get_file_version(self, file_name):
        file_keys = self.get_file(file_name)
        if TYPE_KEY in file_keys:
            return file_keys[TYPE_KEY].split("/")[-1]
        else:
            return None

    # Returns a dictionary of all attributes with their types as values.
    def get_attributes(self):
        return self.get_file(CB_KEY)[ATTR_KEY]

    # Returns the attribute type of a certain attribute.
    def get_attribute_type(self, attribute_name):
        return self.get_attributes()[attribute_name]
    
    # Returns the format value of a certain attribute.
    def get_attribute_format(self, attribute_name):
        try:
            formats = self.get_file(FORMAT_KEY)[ATTR_FORMAT_KEY]
            attr_format = formats[attribute_name]
        except (Exception, KeyError):
            return None
        else:
            return attr_format

    # Returns the Conformance Overlay value of a certain attribute.
    def get_attribute_conformance(self, attribute_name):
        try:
            conformance = self.get_file(CONF_KEY)[ATTR_CONF_KEY]
            attr_conformance = conformance[attribute_name]
        except (Exception, KeyError) as err:
            return False
        else:
            return attr_conformance == 'M'

    # Returns a dictionary of all attributes, with lists of entry codes as values.
    def get_entry_codes(self):
        try:
            ecodes = self.get_file(EC_KEY)[ATTR_EC_KEY]
        except Exception:
            return {}
        else:
            return ecodes

    # Validates the number and name of all attributes.
    # TODO: Allow either the data set or the schema bundle to have more attributes.
    #       Print warnings instead.
    def validate_attribute(self, data_set: OCADataSet) -> OCADataSetErr.AttributeErr:
        rslt = OCADataSetErr.AttributeErr()
        rslt.errs = [i for i in list(data_set.data) if i not in self.get_attributes()]
        return rslt

    # Validates all attributes for format values.
    # Also checks for any missing mandatory attributes.
    def validate_format(self, data_set: OCADataSet) -> OCADataSetErr.FormatErr:
        rslt = OCADataSetErr.FormatErr()
        for attr in self.get_attributes():
            rslt.errs[attr] = {}
            attr_type = self.get_attribute_type(attr)
            attr_format = self.get_attribute_format(attr)
            attr_conformance = self.get_attribute_conformance(attr)
            for i in range(len(data_set.data)):
                data_entry = data_set.data[attr][i]
                if not pd.isna(data_entry):
                    data_entry = str(data_entry)
                elif attr_conformance:
                    # A missing mandatory column.
                    rslt.errs[attr][i] = MISSING_MSG
                    continue
                else:
                    # An empty data entry.
                    data_entry = ""

                if "Array" in attr_type:
                    # Array Attrubutes
                    try:
                        data_arr = json.loads(data_entry)
                    except json.decoder.JSONDecodeError:
                        # Not a valid JSON format string.
                        rslt.errs[attr][i] = NOT_A_LIST_MSG
                        continue
                    if type(data_arr) != list:
                        # Not a valid JSON array.
                        rslt.errs[attr][i] = NOT_A_LIST_MSG
                        continue
                    for data_item in data_arr:
                        if not match_format(attr_type, attr_format, str(data_item)):
                            rslt.errs[attr][i] = FORMAT_ERR_MSG
                            break
                elif not match_format(attr_type, attr_format, data_entry):
                    # Non-array Attributes
                    rslt.errs[attr][i] = FORMAT_ERR_MSG
                else:
                    pass
        return rslt

    # Validates all attributes for the value of entry codes.
    def validate_entry_code(self, data_set: OCADataSet) -> OCADataSetErr.EntryCodeErr:
        rslt = OCADataSetErr.EntryCodeErr() 
        attr_entry_codes = self.get_entry_codes()
        for attr in attr_entry_codes:
            # Validates all attribute with entry codes.
            rslt.errs[attr] = {}
            for i in range(len(data_set.data)):
                data_entry = data_set.data[attr][i]
                if str(data_entry) not in attr_entry_codes[attr]:
                    # Not one of the entry codes.
                    rslt.errs[attr][i] = EC_ERR_MSG
        return rslt

    # Print warning messages for any flagged attributes.
    def flagged_alarm(self):
        if FLAG_KEY in self.get_file(CB_KEY):
            print("Contains flagged data. Please check the following attribute(s):")
            for attr in self.get_file(CB_KEY)[FLAG_KEY]:
                print(attr)
            print()

    # Prints warning messages for any overlays with a different version number.
    def version_alarm(self):
        for overlay_file in self.files_dict:
            file_ver = self.get_file_version(overlay_file)
            if file_ver and file_ver != OCA_VERSION:
                print("Warning: overlay", overlay_file, 
                      "has a different OCA specification version.")
        print()

    # Validates all attributes.
    def validate(self, data_set: OCADataSet,
                 show_data_preview = False, 
                 enable_flagged_alarm = True, 
                 enable_version_alarm = True) -> OCADataSetErr:
        if show_data_preview:
            print(data_set.data)
            print()
        if enable_flagged_alarm:
            self.flagged_alarm()
        if enable_version_alarm:
            self.version_alarm()
        
        # Generate OCADataSetErr result object.
        rslt = OCADataSetErr()
        rslt.attr_err = self.validate_attribute(data_set)
        rslt.format_err = self.validate_format(data_set)
        rslt.ecode_err = self.validate_entry_code(data_set)
        return rslt


def match_datetime(pattern, data_str):

    # Converts the ISO 8601 format into Python DateTime format.
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
    
    if not pattern:
        return True

    if "/" in pattern:
        # Time intervals: <start>/<end>, <start>/<duration>, or <duration>/<end>. 
        # Repeating intervals: R(n)/<interval>.
        # In both cases, validates two parts separately.
        if "/" not in data_str:
            return False
        else:
            return match_datetime(pattern.split("/")[0], data_str.split("/")[0]) and \
                   match_datetime(pattern.split("/")[1], data_str.split("/")[1])
    elif pattern[0] == "P" or pattern[0] == "R":
        # Durations or repeating interval heads. 
        # Match the string with n's replaced with actual numbers.
        return match_regex("^" + pattern.replace("n", "[0-9]+") + "$", data_str)
    else:
        pattern = iso2py(pattern)
        try:
            # Python DateTime format matching. 
            # If formats are not matched, an exception will be raised.
            datetime.strptime(data_str, pattern)
        except:
            return False
        return True

def match_regex(pattern, data_str):
    if not pattern:
        return True
    # Regular expression matching with re.
    return bool(re.search(pattern, data_str))

def match_boolean(data_str):
    # Idealy only "true" and "false" would pass.
    return data_str in ["True",  "true",  "TRUE",  "T", "1", "1.0", 
                        "False", "false", "FALSE", "F", "0", "0.0"]

def match_format(attr_type, pattern, data_str):
    if "DateTime" in attr_type:
        return match_datetime(pattern, data_str)
    elif "Numeric" in attr_type or "Text" in attr_type:
        return match_regex(pattern, data_str)
    elif "Boolean" in attr_type:
        return match_boolean(data_str)
    else:
        return True


if __name__ == "__main__":
    
    ds_path = "./data_entry.xlsx"
    bundle_path = "./bundle.zip"
    
    # test_bd = OCABundle(bundle_path)
    # test_ds = OCADataSet.from_path(ds_path)
    # test_rslt = test_bd.validate(test_ds)
    # test_rslt = test_bd.validate(test_ds, True, False, False)
    
    # test_rslt.overview()
    # test_rslt.first_err_col()
    # test_rslt.get_err_col("num_arr_attr")
    
    # print(test_rslt.get_format_err())
    # print(test_rslt.get_ecode_err())

