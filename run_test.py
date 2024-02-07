from oca_ds_validator.oca_ds_validator import OCABundle, OCADataSet

test_bd = OCABundle("./tests_files/test_bundle.json")
valid_ds = OCADataSet.from_path("./tests_files/data_entry_example.xlsx")

valid_rslt = test_bd.validate(valid_ds)
valid_rslt.overview()
# Found 5 problematic row(s) in the following attribute(s): {'Breed'}

# valid_rslt.first_err_col()
# Format error(s) would occur in the following row(s):
# row 0 :  Entry code format mismatch (manually fix the attribute format). Supported format for entry code is: [A-Z]{15}.
# row 1 :  Entry code format mismatch (manually fix the attribute format). Supported format for entry code is: [A-Z]{15}.
# row 2 :  Entry code format mismatch (manually fix the attribute format). Supported format for entry code is: [A-Z]{15}.
# row 3 :  Entry code format mismatch (manually fix the attribute format). Supported format for entry code is: [A-Z]{15}.
# row 4 :  Entry code format mismatch (manually fix the attribute format). Supported format for entry code is: [A-Z]{15}.

# print(valid_rslt.get_attr_err())
# print(valid_rslt.get_format_err())
# print(valid_rslt.get_ecode_err())
# print(valid_rslt.get_char_encode_err())
