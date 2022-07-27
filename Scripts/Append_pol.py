import arcpy
#Set environments
arcpy.env.XYResolution = "0.00001 Meters"
arcpy.env.XYTolerance = "0.0001 Meters"

arcpy.env.overwriteOutput = True
arcpy.env.workspace = arcpy.GetParameterAsText(0)
C2=arcpy.GetParameterAsText(1)
C3=arcpy.GetParameterAsText(2)

# List all file geodatabases in the current workspace
workspaces = arcpy.ListWorkspaces("*", "FileGDB")
fcs=[]
for workspace in workspaces:
    # List all Dissec FCS in workspaces
    arcpy.env.workspace = workspace
    featureclasses = arcpy.ListFeatureClasses("DissecHC1*")
    if len (featureclasses)>0:
        fc=featureclasses[0]
        path="%s\%s" % (workspace,fc)
        fcs.append(path)
if len(fcs)>0:
    spatial_reference = arcpy.Describe(fcs[0]).spatialReference
    DissecOut_folder=arcpy.GetParameterAsText(3)
    DissecOut_name=arcpy.GetParameterAsText(4)
    DissecOut_C1=DissecOut_name+"C1"
    arcpy.CreateFeatureclass_management(DissecOut_folder, DissecOut_C1, "POLYGON", "", "", "", spatial_reference)
    target="%s\%s" % (DissecOut_folder,DissecOut_C1)
    arcpy.AddField_management(target, "Classe_Dis_C1", "TEXT", "", "", "", "", "NULLABLE")
    arcpy.Append_management (fcs, target, "NO_TEST")

    if C2!="0":
        fcs=[]
        for workspace in workspaces:
            arcpy.env.workspace = workspace
            featureclasses = arcpy.ListFeatureClasses("DissecHC2*")
            if len (featureclasses)>0:
                fc=featureclasses[0]
                path="%s\%s" % (workspace,fc)
                fcs.append(path)
        if len(fcs)>0:
            spatial_reference = arcpy.Describe(fcs[0]).spatialReference
            DissecOut_C2=DissecOut_name+"C2"
            arcpy.CreateFeatureclass_management(DissecOut_folder, DissecOut_C2, "POLYGON", "", "", "", spatial_reference)
            target="%s\%s" % (DissecOut_folder,DissecOut_C2)
            arcpy.AddField_management(target, "Classe_Dis_C2", "TEXT", "", "", "", "", "NULLABLE")
            arcpy.Append_management (fcs, target, "NO_TEST")
    if C3!="0":
        fcs=[]
        for workspace in workspaces:
            arcpy.env.workspace = workspace
            featureclasses = arcpy.ListFeatureClasses("DissecHC3*")
            if len (featureclasses)>0:
                fc=featureclasses[0]
                path="%s\%s" % (workspace,fc)
                fcs.append(path)
        if len(fcs)>0:
            spatial_reference = arcpy.Describe(fcs[0]).spatialReference
            DissecOut_C3=DissecOut_name+"C3"
            arcpy.CreateFeatureclass_management(DissecOut_folder, DissecOut_C3, "POLYGON", "", "", "", spatial_reference)
            target="%s\%s" % (DissecOut_folder,DissecOut_C3)
            arcpy.AddField_management(target, "Classe_Dis_C3", "TEXT", "", "", "", "", "NULLABLE")
            arcpy.Append_management (fcs, target, "NO_TEST")
        
