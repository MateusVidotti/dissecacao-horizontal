# Name: Flipline_Example.py
# Description: Flip line features
# Requirements: 

import arcpy
from arcpy import env
import os
inFeatures=arcpy.GetParameterAsText(0)
try:
    arcpy.FlipLine_edit(inFeatures)
except Exception, e:
    # If an error occurred, print line number and error message
    import traceback, sys
    tb = sys.exc_info()[2]
    print "Line %i" % tb.tb_lineno
    print e.message
