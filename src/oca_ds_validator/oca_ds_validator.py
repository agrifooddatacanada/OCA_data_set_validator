import json
from pathlib import Path
import pandas as pd
from datetime import datetime
import re

##############################################################################
# Authors: Xingjian Xu and Steven Mugisha Mizero from Agri-food Data Canada
#                          (https://agrifooddatacanada.ca/)
#
# Created with support by Agri-food Data Canada, funded by CFREF through the
# Food from Thought grant held at the University of Guelph.
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

# When more than ERR_THRESHOLD problematic attributes are found, show count
# number instead of attribute names.
ERR_THRESHOLD = 5

# Names of OCA bundle dictionary keys.
# Do not change unless there are any key errors.
CB_KEY = "capture_base"
TYPE_KEY = "type"
ATTR_KEY = "attributes"
FORMAT_KEY = "format"
ATTR_FORMAT_KEY = "attribute_formats"
CONF_KEY = "conformance"
ATTR_CONF_KEY = "attribute_conformance"
EC_KEY = "entry_code"
ATTR_EC_KEY = "attribute_entry_codes"
CHE_KEY = "character_encoding"
ATTR_CHE_KEY = "attribute_character_encoding"
DEFAULT_ATTR_CHE_KEY = "default_character_encoding"
DEFAULT_ENCODING = "utf-8"
FLAG_KEY = "flagged_attributes"
OVELAYS_KEY = "overlays"

# The tab name in the Excel Data Entry File.
# Do not change unless there are any Excel parsing errors.
DATA_ENTRY_SHEET_KEY = "Schema conformant data"

# Error messages. For text notices only.
ATTR_UNMATCH_MSG = "Unmatched attribute (attribute not found in the OCA Bundle)."
ATTR_MISSING_MSG = "Missing attribute (attribute not found in the data set)."
MISSING_MSG = "Missing mandatory attribute."
NOT_A_LIST_MSG = "Valid array required."
FORMAT_ERR_MSG = "Format mismatch."
EC_FORMAT_ERR_MSG = " Entry code format mismatch (manually fix the attribute format)."
EC_ERR_MSG = "One of the entry codes required."
CHE_ERR_MSG = "Character encoding mismatch."


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
            return cls(pd.read_excel(ds_path, sheet_name=DATA_ENTRY_SHEET_KEY))
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

    # Not matching character encoding
    class EncodingErr:
        def __init__(self):
            self.errs = {}

    def __init__(self):
        self.attr_err = OCADataSetErr.AttributeErr()
        self.format_err = OCADataSetErr.FormatErr()
        self.ecode_err = OCADataSetErr.EntryCodeErr()
        self.char_encode_err = OCADataSetErr.EncodingErr()

        self.missing_attr = set()
        self.unmatched_attr = set()

        self.err_cols = set()
        self.err_rows = set()

    # Minimal error information. Could be effective when there are only a few
    # errors in a few attributes.
    def overview(self):
        self.update_err()
        if (not self.attr_err.errs) and (not self.err_cols) and (not self.err_rows):
            print("No error was found.")
        if self.attr_err.errs:
            if len(self.missing_attr) > ERR_THRESHOLD:
                missing_attr_msg = str(len(self.missing_attr)) + " attributes"
            else:
                missing_attr_msg = str(self.missing_attr)
            if len(self.unmatched_attr) > ERR_THRESHOLD:
                unmatched_attr_msg = str(len(self.unmatched_attr)) + " attributes"
            else:
                unmatched_attr_msg = str(self.unmatched_attr)
            print(
                "Attribute error found.",
                missing_attr_msg,
                "found in the OCA Bundle but not in the data set;",
                unmatched_attr_msg,
                "found in the data set but not in the OCA Bundle.",
            )
        if self.err_cols or self.err_rows:
            if len(self.err_cols) > ERR_THRESHOLD:
                err_cols_msg = str(len(self.err_cols)) + " attributes"
            else:
                err_cols_msg = "the following attribute(s): " + str(self.err_cols)
            print("Found", len(self.err_rows), "problematic row(s) in", err_cols_msg)
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
        for i in self.attr_err.errs:
            if i[1] == ATTR_MISSING_MSG:
                self.missing_attr.add(i[0])
            elif i[1] == ATTR_UNMATCH_MSG:
                self.unmatched_attr.add(i[0])
        for i in self.format_err.errs:
            for j in self.format_err.errs[i]:
                self.err_rows.add(j)  # problematic data rows
            if self.format_err.errs[i]:
                self.err_cols.add(i)  # problematic attribute
        for i in self.ecode_err.errs:
            for j in self.ecode_err.errs[i]:
                self.err_rows.add(j)  # problematic data rows
            if self.ecode_err.errs[i]:
                self.err_cols.add(i)  # problematic attribute
        for i in self.char_encode_err.errs:
            for j in self.char_encode_err.errs[i]:
                self.err_rows.add(j)  # problematic data rows
            if self.char_encode_err.errs[i]:
                self.err_cols.add(i)  # problematic attribute

    # Returns the error detail list for missing or unmatched attributes.
    def get_attr_err(self):
        return self.attr_err.errs

    # Returns the error detail dictionary for format values.
    def get_format_err(self):
        return self.format_err.errs

    # Returns the error detail dictionary for entry codes.
    def get_ecode_err(self):
        return self.ecode_err.errs

    # Returns the error detail dictionary for character encoding.
    def get_char_encode_err(self):
        return self.char_encode_err.errs

    # Prints the error detail for a certain column.
    def get_err_col(self, attr_name):
        self.update_err()
        if not self.err_cols:
            print("No error was found.")
        else:
            if attr_name in self.get_format_err():
                print("Format error(s) would occur in the following row(s):")
                for row in self.get_format_err()[attr_name]:
                    print("row", row, ":", self.get_format_err()[attr_name][row])
            else:
                print("No format error found in the column.")

            if attr_name in self.get_ecode_err():
                print("Entry code error(s) would occur in the following rows:")
                for row in self.get_ecode_err()[attr_name]:
                    print("row", row, ":", self.get_ecode_err()[attr_name][row])
            # else:
            #     print("No entry code error found in the column.")
        print()


# A loaded .json OCA bundle.
class OCABundle:
    # Load an OCA bundle.
    # bundle_path_str: String. File path to the OCA bundle zip file.
    #                  Both kinds of slash works.
    def __init__(self, bundle_path_str):
        self.overlays = {}
        self.overlays_dict = {}

        # Slash auto correction based on the current system.
        bundle_path = Path(bundle_path_str)

        # The OCA bundle file name without extension.
        # This was for navigating in the .json file. Currently not used.
        # bundle_name = bundle_path.name.rsplit(".", 1)[0]

        # Load a .json OCA bundle.
        with open(bundle_path, "r") as bundle:
            self.oca_bundle = json.load(bundle)

        # Load all overlays and capture base.
        self.capture_base = self.oca_bundle[CB_KEY]
        self.overlays = self.oca_bundle[OVELAYS_KEY]
        self.overlays_dict[CB_KEY] = self.capture_base
        for overlay in self.overlays:
            self.overlays_dict[overlay] = self.overlays[overlay]

    def get_overlay(self, overlay_name):
        if overlay_name in self.overlays_dict:
            return self.overlays_dict[overlay_name]
        else:
            raise Exception("Wrong overlay name")

    # Gets the OCA spec version number from overlay type.
    def get_overlay_version(self, overlay_name):
        file_keys = self.get_overlay(overlay_name)
        if TYPE_KEY in file_keys:
            return file_keys[TYPE_KEY].split("/")[-1]
        else:
            return None

    # Returns a dictionary of all attributes with their types as values.
    def get_attributes(self):
        return self.get_overlay(CB_KEY)[ATTR_KEY]

    # Returns the attribute type of a certain attribute.
    def get_attribute_type(self, attribute_name):
        return self.get_attributes()[attribute_name]

    # Returns the format value of a certain attribute.
    def get_attribute_format(self, attribute_name):
        try:
            formats = self.get_overlay(FORMAT_KEY)[ATTR_FORMAT_KEY]
            attr_format = formats[attribute_name]
        except (Exception, KeyError):
            return None
        else:
            return attr_format

    # Returns the Conformance Overlay value of a certain attribute.
    def get_attribute_conformance(self, attribute_name):
        try:
            conformance = self.get_overlay(CONF_KEY)[ATTR_CONF_KEY]
            attr_conformance = conformance[attribute_name]

        except (Exception, KeyError) as err:
            return False
        else:
            return attr_conformance == "M"

    # Returns a dictionary of all attributes, with lists of entry codes as values.
    def get_entry_codes(self):
        try:
            ecodes = self.get_overlay(EC_KEY)[ATTR_EC_KEY]
        except Exception:
            return {}
        else:
            return ecodes

    # Returns the character encoding of the specified attribute.
    def get_character_encoding(self, attribute_name):
        try:
            if (
                not self.get_overlay(CHE_KEY)[ATTR_CHE_KEY]
                or not self.get_overlay(CHE_KEY)[ATTR_CHE_KEY][attribute_name]
            ):
                return DEFAULT_ENCODING
            else:
                return self.get_overlay(CHE_KEY)[ATTR_CHE_KEY][attribute_name]
        except (Exception, KeyError):
            return None

    # Validates the number and name of all attributes.
    def validate_attribute(self, data_set: OCADataSet) -> OCADataSetErr.AttributeErr:
        rslt = OCADataSetErr.AttributeErr()
        rslt.errs += [
            (i, ATTR_UNMATCH_MSG)
            for i in list(data_set.data)
            if i not in self.get_attributes()
        ]
        rslt.errs += [
            (i, ATTR_MISSING_MSG)
            for i in self.get_attributes()
            if i not in list(data_set.data)
        ]
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
                try:
                    data_entry = data_set.data[attr][i]
                except KeyError:
                    continue
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
                            rslt.errs[attr][
                                i
                            ] = f"{FORMAT_ERR_MSG} Supported format: {attr_format}."
                            break
                elif not match_format(attr_type, attr_format, data_entry):
                    # Attributes with entry codes.
                    if attr in self.get_entry_codes():
                        rslt.errs[attr][
                            i
                        ] = f"{EC_FORMAT_ERR_MSG} Supported format for entry code is: {attr_format}."
                    else:
                        # Non-array Attributes
                        rslt.errs[attr][i] = f"{FORMAT_ERR_MSG} Supported format: {attr_format}."
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
                    rslt.errs[attr][i
                    ] = f"{EC_ERR_MSG} Entry codes allowed: {attr_entry_codes[attr]}."
        return rslt

    # Validates all attributes for character encoding.
    def validate_encoding(self, data_set: OCADataSet) -> OCADataSetErr.EncodingErr:
        rslt = OCADataSetErr.EncodingErr()
        for attr in self.get_attributes():
            attr_char_encode = self.get_character_encoding(attr)
            rslt.errs[attr] = {}
            for i in range(len(data_set.data)):
                data_entry = data_set.data[attr][i]
                if not match_character_encoding(data_entry, attr_char_encode):
                    rslt.errs[attr][i] = f"{CHE_ERR_MSG} Supported character encoding: {attr_char_encode}."
        return rslt

    # Print warning messages for any flagged attributes.
    def flagged_alarm(self):
        if FLAG_KEY in self.get_overlay(CB_KEY) and self.get_overlay(CB_KEY)[FLAG_KEY]:
            print("Contains flagged data. Please check the following attribute(s):")
            for attr in self.get_overlay(CB_KEY)[FLAG_KEY]:
                print(attr)
            print()

    # Prints warning messages for any overlays with a different version number.
    def version_alarm(self):
        version_error = False
        for overlay_file in self.overlays_dict:
            file_ver = self.get_overlay_version(overlay_file)
            if file_ver and file_ver != OCA_VERSION:
                version_error = True
                print(
                    "Warning: overlay",
                    overlay_file,
                    "has a different OCA specification version.",
                )
        if version_error:
            print()

    # Validates all attributes.
    def validate(
        self,
        data_set: OCADataSet,
        show_data_preview=False,
        enable_flagged_alarm=True,
        enable_version_alarm=True,
    ) -> OCADataSetErr:
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
        rslt.char_encode_err = self.validate_encoding(data_set)
        return rslt


def match_datetime(pattern, data_str):
    # Converts the ISO 8601 format into Python DateTime format.
    def iso2py(iso_str):
        iso_conv = {
            "YYYY": "%Y",
            "MM": "%m",
            "DDD": "%j",
            "DD": "%d",
            "D": "%w",
            "ww": "%W",
            "+hh:mm": "%z",
            "-hh:mm": "%z",
            "+hhmm": "%z",
            "-hhmm": "%z",
            "Z": "%z",
            "hh": "%H",
            "mm": "%M",
            "sss": "%f",
            "ss": "%S",
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
            return match_datetime(
                pattern.split("/")[0], data_str.split("/")[0]
            ) and match_datetime(pattern.split("/")[1], data_str.split("/")[1])
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
    return data_str in [
        "True",
        "true",
        "TRUE",
        "T",
        "1",
        "1.0",
        "False",
        "false",
        "FALSE",
        "F",
        "0",
        "0.0",
    ]


def match_format(attr_type, pattern, data_str):
    if "DateTime" in attr_type:
        return match_datetime(pattern, data_str)
    elif "Numeric" in attr_type or "Text" in attr_type:
        return match_regex(pattern, data_str)
    elif "Boolean" in attr_type:
        return match_boolean(data_str)
    else:
        return True


def is_valid_utf8(data_input):
    # Decode the data entered in UTF-8.
    data_str = str(data_input)
    try:
        data_str.encode("utf-8").decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def is_valid_utf16le(data_input):
    # Decode the data entered in UTF-16LE.
    data_str = str(data_input)
    try:
        data_str.decode("utf-16le")
        return True
    except UnicodeDecodeError:
        return False


def is_valid_iso8859_1(data_input):
    # Decode the data entered in ISO 8859-1.
    data_str = str(data_input)
    try:
        data_str.decode("iso-8859-1")
        return True
    except UnicodeDecodeError:
        return False


def match_character_encoding(data_str, attr_char_encode):
    if attr_char_encode == "utf-8":
        return is_valid_utf8(data_str)
    elif attr_char_encode == "utf-16le":
        return is_valid_utf16le(data_str)
    elif attr_char_encode == "iso-8859-1":
        return is_valid_iso8859_1(data_str)
    else:
        return False
