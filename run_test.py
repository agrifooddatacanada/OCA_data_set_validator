from oca_ds_validator import OCADataSet, OCADataSetErr, OCABundle

test_bd = OCABundle("./test_bundle.zip")
valid_ds = OCADataSet.from_path("./valid_data_set.csv")
error_ds = OCADataSet.from_path("./error_data_set.csv")

valid_rslt = test_bd.validate(valid_ds)
valid_rslt.overview() 
# No error was found.

error_rslt = test_bd.validate(error_ds)
error_rslt.overview()
# Attribute error found. {'analysisDate'} found in the OCA Bundle but not in 
# the data set; {'message'} found in the data set but not in the OCA Bundle.
# Found 5 problematic row(s) in the following attribute(s): {'location', 
# 'insectWeight', 'insectCount', 'collectionDate', 'insectType'}


# print(error_rslt.get_attr_err())
# print(error_rslt.get_format_err())
# print(error_rslt.get_ecode_err())

