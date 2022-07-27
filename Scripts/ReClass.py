import arcpy
#Set environments
arcpy.env.XYResolution = "0.00001 Meters"
arcpy.env.XYTolerance = "0.0001 Meters"
arcpy.env.overwriteOutput = True

#Variable
folder=arcpy.GetParameterAsText(0)
arcpy.env.workspace=folder
C_str=arcpy.GetParameterAsText(1)
Sufix=arcpy.GetParameterAsText(2)

#List Classes function
def list_classes (c_str, Classes):
    c_list = c_str.split(";")
    for c in c_list:
        c_int=int(c)
        Classes.append(c_int)
#Build list classes
Classes=[]
list_classes (C_str, Classes)

#Define field name
field="Classe_Dis"+Sufix

#function for calc class
def CalcClass (lenght, Class_list):
    for c,x in enumerate(Class_list):
        if lenght <= x:
            return c
            break

# List all file geodatabases in the current workspace
workspaces = arcpy.ListWorkspaces("*", "FileGDB")
fcs=[]
for workspace in workspaces:
    # List all DisH_ FCS in workspaces
    arcpy.env.workspace = workspace
    featureclasses = arcpy.ListFeatureClasses("DisH_*")
    if len (featureclasses)>0:
        fc_name=featureclasses[0]
        fc="%s\%s" % (workspace,fc_name)
        arcpy.AddField_management(fc, field, "Text", "", "", "", "", "NULLABLE")
        #Calculate Dissecation field with update cursor
        cursor = arcpy.UpdateCursor(fc)
        for row in cursor:
            value=row.getValue("MAX")
            class_pol=CalcClass(value, Classes)
            classe= "Classe %d" %class_pol
            row.setValue(field, classe)
            cursor.updateRow(row)
        del cursor, row
        #Dissolve polygons based on dissecation classes
        Basin_ID=(fc_name.split("_"))[1]
        DissecH_Dissolve="%s\%s" % (workspace,Basin_ID)
        arcpy.Dissolve_management(fc, DissecH_Dissolve, [field],"", "SINGLE_PART")
        #Split polygons
        drenagem=folder+"\General.gdb\Drenagem"
        infeatures=[DissecH_Dissolve,drenagem]
        Bacia_split=Basin_ID+"_Split"
        clusTol = "0.01 Meters"
        arcpy.FeatureToPolygon_management(infeatures, Bacia_split, clusTol,"NO_ATTRIBUTES", "")
        #Union polygons
        infeatures=[DissecH_Dissolve,Bacia_split]
        DissecH_union="DissecUnion_"+Basin_ID
        arcpy.Union_analysis(infeatures,DissecH_union,"ALL",clusTol)
        #Clip polygons
        DissecH_F="DissecH_"+Basin_ID+"_"+Sufix
        Basin=workspace+"\\"+Basin_ID
        arcpy.Clip_analysis (DissecH_union, Basin, DissecH_F)

        #Build DissecH List
        path="%s\%s" % (workspace,DissecH_F)
        fcs.append(path)

if len(fcs)>0:
    spatial_reference = arcpy.Describe(fcs[0]).spatialReference
    DissecOut_folder=arcpy.GetParameterAsText(3)
    DissecOut_name=arcpy.GetParameterAsText(4)
    DissecOut=DissecOut_name
    arcpy.CreateFeatureclass_management(DissecOut_folder, DissecOut, "POLYGON", "", "", "", spatial_reference)
    target="%s\%s" % (DissecOut_folder,DissecOut)
    arcpy.AddField_management(target, field, "TEXT", "", "", "", "", "NULLABLE")
    arcpy.Append_management (fcs, target, "NO_TEST")

    
