# Import system modules
import arcpy, os, random, sys
from arcpy import env
from arcpy.sa import *
import math
from operator import itemgetter
from collections import OrderedDict

#Set environments
arcpy.env.overwriteOutput = True
arcpy.env.XYResolution = "0.00001 Meters"
arcpy.env.XYTolerance = "0.0001 Meters"

# Check out the ArcGIS extension license
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension('3D')
  
# Set local variables
env.workspace = arcpy.GetParameterAsText(0)
Stream = arcpy.GetParameterAsText(1)
Basin = arcpy.GetParameterAsText(2)
Springs = arcpy.GetParameterAsText(3)
SplitStream_par = float(arcpy.GetParameterAsText(4))
Group =float(arcpy.GetParameterAsText(5))
DEM=arcpy.GetParameterAsText(6)
c_str_C1 = arcpy.GetParameterAsText(7)
c_str_C2 = arcpy.GetParameterAsText(8)
c_str_C3 = arcpy.GetParameterAsText(9)
#Build Dissection classes
def list_classes (c_str, Classes):
    c_list = c_str.split(";")
    for c in c_list:
        c_int=int(c)
        Classes.append(c_int)
Classes_C1=[]
list_classes (c_str_C1, Classes_C1)
if c_str_C2!="0":
    Classes_C2=[]
    list_classes (c_str_C2, Classes_C2)
if c_str_C3!="0":
    Classes_C3=[]
    list_classes (c_str_C3, Classes_C3)

#function for calc class
def CalcClass (lenght, Class_list):
    for c,x in enumerate(Class_list):
        if lenght <= x:
            return c+1
            break

#Get Basin ID
Basin_ids = arcpy.SearchCursor (Basin)
rowB = Basin_ids.next()
Basin_idN = int(rowB.getValue("ID_Basin"))
Basin_id = "%d"%(Basin_idN)
arcpy.AddMessage("Processando Bacia {0}".format(Basin_id))
   
#Basin Buffer and set extent
arcpy.MakeFeatureLayer_management(Basin, "Basin_layer")
b100="in_memory"+"\\"+"b100"
b_0_5="in_memory"+"\\"+"b_0_5"
arcpy.Buffer_analysis("Basin_layer", b100, "100 Meters", "FULL")
arcpy.Buffer_analysis("Basin_layer", b_0_5, "0.05 Meters", "FULL")
descBasin = arcpy.Describe(b100)
arcpy.env.extent = descBasin.extent

#Prepare DEM
DEM_R="Dem_R"
arcpy.Resample_management(DEM, DEM_R, "0.5", "NEAREST")
arcpy.MakeRasterLayer_management (DEM_R, "DEM_R_layer")

####START - Processing Stream####
##Split Stream##

###START SPLIT LINE CODE IN A SAME DISTANCE### Source: http://nodedangles.wordpress.com/2011/05/01/quick-dirty-arcpy-batch-splitting-polylines-to-a-specific-length/
def splitline (inFC,FCName,alongDist):

    OutDir = env.workspace
    outFCName = FCName
    outFC = OutDir+"/"+outFCName

    def distPoint(p1, p2):
        calc1 = p1.X - p2.X
        calc2 = p1.Y - p2.Y

        return math.sqrt((calc1**2)+(calc2**2))

    def midpoint(prevpoint,nextpoint,targetDist,totalDist):
        newX = prevpoint.X + ((nextpoint.X - prevpoint.X) * (targetDist/totalDist))
        newY = prevpoint.Y + ((nextpoint.Y - prevpoint.Y) * (targetDist/totalDist))
        return arcpy.Point(newX, newY)

    def splitShape(feat,splitDist):
        # Count the number of points in the current multipart feature
        #
        partcount = feat.partCount
        partnum = 0
        # Enter while loop for each part in the feature (if a singlepart feature
        # this will occur only once)
        #
        lineArray = arcpy.Array()

        while partnum < partcount:

              part = feat.getPart(partnum)

              totalDist = 0

              pnt = part.next()
              pntcount = 0

              prevpoint = None
              shapelist = []

              # Enter while loop for each vertex
              #
              while pnt:

                    if not (prevpoint is None):
                        thisDist = distPoint(prevpoint,pnt)
                        maxAdditionalDist = splitDist - totalDist

                        if (totalDist+thisDist)> splitDist:
                              while(totalDist+thisDist) > splitDist:
                                    maxAdditionalDist = splitDist - totalDist
                                    newpoint = midpoint(prevpoint,pnt,maxAdditionalDist,thisDist)
                                    lineArray.add(newpoint)
                                    shapelist.append(lineArray)

                                    lineArray = arcpy.Array()
                                    lineArray.add(newpoint)
                                    prevpoint = newpoint
                                    thisDist = distPoint(prevpoint,pnt)
                                    totalDist = 0

                              lineArray.add(pnt)
                              totalDist+=thisDist
                        else:
                              totalDist+=thisDist
                              lineArray.add(pnt)
                              #shapelist.append(lineArray)
                    else:
                        lineArray.add(pnt)
                        totalDist = 0

                    prevpoint = pnt                
                    pntcount += 1

                    pnt = part.next()

                    # If pnt is null, either the part is finished or there is an
                    #   interior ring
                    #
                    if not pnt:
                        pnt = part.next()
                              
              partnum += 1

        if (lineArray.count > 1):
              shapelist.append(lineArray)

        return shapelist

    if arcpy.Exists(outFC):
        arcpy.Delete_management(outFC)

    arcpy.Copy_management(inFC,outFC)

    deleterows = arcpy.UpdateCursor(outFC)
    for iDRow in deleterows:       
         deleterows.deleteRow(iDRow)

    del iDRow
    del deleterows

    inputRows = arcpy.SearchCursor(inFC)
    outputRows = arcpy.InsertCursor(outFC)
    fields = arcpy.ListFields(inFC)

    numRecords = int(arcpy.GetCount_management(inFC).getOutput(0))
    OnePercentThreshold = numRecords // 100

    iCounter = 0
    iCounter2 = 0

    for iInRow in inputRows:
        inGeom = iInRow.shape
        iCounter+=1
        iCounter2+=1    
        if (iCounter2 > (OnePercentThreshold+0)):
              iCounter2=0

        if (inGeom.length > alongDist):
              shapeList = splitShape(iInRow.shape,alongDist)

              for itmp in shapeList:
                    newRow = outputRows.newRow()
                    for ifield in fields:
                        if (ifield.editable):
                              newRow.setValue(ifield.name,iInRow.getValue(ifield.name))
                    newRow.shape = itmp
                    outputRows.insertRow(newRow)
        else:
              outputRows.insertRow(iInRow)

    del inputRows
    del outputRows

###END SPLIT LINE CODE IN A SAME DISTANCE###

Stream_Split = "Stream_Split"
splitline(Stream,Stream_Split,SplitStream_par)

####END - Processing Stream####

####Processing Basin####
#Densify Basin
BasinN="BasinN"
arcpy.Copy_management(Basin, BasinN)
Densi_BasinV = SplitStream_par/4
Densi_BasinV = "%f Meters" %Densi_BasinV
arcpy.Densify_edit(Basin, "DISTANCE", Densi_BasinV)

#Basin to line
Basin_line = "in_memory\Basin_line"
b_line_0_5="in_memory\B_line_0_5"
arcpy.FeatureToLine_management([Basin], Basin_line)
arcpy.FeatureToLine_management([b_0_5], b_line_0_5)
#Delete the first point of basin
StreamStart_point  = "in_memory\StreamStart_point"
arcpy.FeatureVerticesToPoints_management(Stream, StreamStart_point , "START")
DrenaStart_buffer1="in_memory\DrenaStart_buffer1"
arcpy.Buffer_analysis(StreamStart_point , DrenaStart_buffer1, "1 Meters", "FULL", "ROUND", "NONE", "")
BasinLine_erase = "in_memory\Basinline_erase"
arcpy.Erase_analysis(Basin_line, DrenaStart_buffer1, BasinLine_erase)
BasinLine_dissolve="in_memory\Basinline_dissolve"
arcpy.Dissolve_management(BasinLine_erase, BasinLine_dissolve, "", "", "SINGLE_PART", "DISSOLVE_LINES")
#Class Basin
arcpy.MakeFeatureLayer_management(Springs, "Springs_layer")
arcpy.SelectLayerByLocation_management("Springs_layer", 'COMPLETELY_WITHIN', Basin, "", "NEW_SELECTION")
Basin_cursor = sorted(arcpy.da.SearchCursor("Springs_layer", "OBJECTID"))
if len(Basin_cursor)==1:
    BasinSpring=True
else:
    BasinSpring=False


# Generate Distance 
DistMap = "in_memory\DistMap"
arcpy.gp.EucDistance_sa(Stream_Split, DistMap, "", "0.5")

#Buffer Stream_split
Stream_buffer2m = "in_memory\Stream_buffer2m"
arcpy.Buffer_analysis(Stream_Split, Stream_buffer2m, "2 Meters", "FULL", "ROUND", "NONE", "")

#Add and calculate Azimute field in Stream_Split
arcpy.AddField_management(Stream_Split, "azimuth", "Double", "", "", "", "", "NULLABLE")
codeblock = """def CalculaAzimuth(linea):
    if (hasattr(linea,'type') and linea.type == 'polyline'):
        xf = linea.firstPoint.X
        yf = linea.firstPoint.Y
        xl = linea.lastPoint.X
        yl = linea.lastPoint.Y
        dX = xl - xf
        dY = yl - yf
        PI = math.pi
        Azimuth = 0 #Default case, dX = 0 and dY >= 0
        if dX > 0:
            Azimuth = 90 - math.atan( dY / dX ) * 180 / PI
        elif dX < 0:
            Azimuth = 270 - math.atan( dY / dX )* 180 / PI
        elif dY < 0:
            Azimuth = 180
        return Azimuth
    else:
        return False"""
arcpy.CalculateField_management(Stream_Split,"azimuth",'CalculaAzimuth(!shape!)','PYTHON_9.3', codeblock)

#Calculate Maximum Elevation for SplitStream Segments
##Add Field (z_max)
arcpy.MakeFeatureLayer_management(Stream_Split, "SplitStream_layer")
arcpy.AddField_management ("SplitStream_layer", "z_max", "LONG")
arcpy.AddField_management ("SplitStream_layer", "z_maxID", "LONG")
##Calculate SplitStream_Maxtab
SplitStream_Maxtab="SplitStream_Maxtab"
outZSaT=ZonalStatisticsAsTable ("SplitStream_layer", "OBJECTID", "DEM_R_layer", SplitStream_Maxtab, "NODATA", "MAXIMUM")
arcpy.MakeTableView_management ("SplitStream_Maxtab", "SplitStream_Maxtab_view")
##Add join
arcpy.AddJoin_management ("SplitStream_layer", "OBJECTID", "SplitStream_Maxtab_view", "OBJECTID_1")
##Calculate field
arcpy.CalculateField_management ("SplitStream_layer", "z_max", "[SplitStream_Maxtab.MAX]", "VB", "")
##Remove join
arcpy.RemoveJoin_management ("SplitStream_layer")
arcpy.CalculateField_management ("SplitStream_layer", "z_maxID", "[z_max]+[OBJECTID]", "VB", "")

##Generate Stream_EndsPoint
Stream_EndsPoint = "in_memory\StreamEnds_B%s"%Basin_id
arcpy.FeatureVerticesToPoints_management(Stream, Stream_EndsPoint, "BOTH_ENDS")
##Select Mid stream Segments
arcpy.SelectLayerByLocation_management("SplitStream_layer", '', "", "", "SWITCH_SELECTION")
arcpy.SelectLayerByLocation_management("SplitStream_layer", 'intersect', Stream_EndsPoint, "", "REMOVE_FROM_SELECTION")
##Calculate distance to Basin border
arcpy.Near_analysis("SplitStream_layer", Basin_line)
##Select SplitStream Segments with distance Less than 0.5 meter
arcpy.SelectLayerByAttribute_management("SplitStream_layer", "SUBSET_SELECTION", 'NEAR_DIST < 0.5')

#Mid drena segments to point
StreamPoints = "StreamPoints"
arcpy.FeatureVerticesToPoints_management(Stream_Split, StreamPoints, "MID")
arcpy.AddField_management(StreamPoints, "azimuth2", "Double", "", "", "", "", "NULLABLE")

#Add XY field and ID_ptdren field to StreamPoints
arcpy.AddXY_management(StreamPoints)
arcpy.AddField_management(StreamPoints, "ID_ptdren", "SHORT", "", "", "", "", "NULLABLE")
#assign ID_ptdren with OBJECTID
cursorP = arcpy.UpdateCursor(StreamPoints)
for rowP in cursorP:
    rowP.setValue("ID_ptdren", rowP.getValue("OBJECTID"))
    cursorP.updateRow(rowP)
del cursorP, rowP

#Start - Calculate azimuth seg dren X g
StreamPoints_cursor = arcpy.da.UpdateCursor(StreamPoints, ("OBJECTID","azimuth2"))
StreamPoints_list = sorted (arcpy.da.SearchCursor(StreamPoints, ["OBJECTID","POINT_X","POINT_Y"]))
e=0
g=int(Group/2)
for a in StreamPoints_cursor:
    if (e-g)<0:
        firstx=StreamPoints_list[0][1]
        firsty=StreamPoints_list[0][2]
    else:
        firstx=StreamPoints_list[e-g][1]
        firsty=StreamPoints_list[e-g][2]
    if (e+g)>(len(StreamPoints_list)-1):
        lastx=StreamPoints_list[len(StreamPoints_list)-1][1]
        lasty=StreamPoints_list[len(StreamPoints_list)-1][2]
    else:
        lastx=StreamPoints_list[e+g][1]
        lasty=StreamPoints_list[e+g][2]
    #Calculate Azimuth
    xf = firstx
    yf = firsty
    xl = lastx
    yl = lasty
    dX = xl - xf
    dY = yl - yf
    PI = math.pi
    Azimuth = 0 #Default case, dX = 0 and dY >= 0
    if dX > 0:
        Azimuth = 90 - math.atan( dY / dX ) * 180 / PI
    elif dX < 0:
        Azimuth = 270 - math.atan( dY / dX )* 180 / PI
    elif dY < 0:
        Azimuth = 180
    a[1]=Azimuth
    StreamPoints_cursor.updateRow(a)
    e+=1

del a, e, StreamPoints_cursor, StreamPoints_list
#END - Calculate azimuth seg dren X g


#Generate pts_Basin
pts_Basin = "in_memory\pts_Basin"
arcpy.FeatureVerticesToPoints_management(BasinLine_dissolve, pts_Basin, "ALL")
if BasinSpring==True:
    arcpy.MakeFeatureLayer_management(BasinN, "BasinN_layer")
    Densi_BasinV_N="%f Meters" %SplitStream_par
    arcpy.Densify_edit("BasinN_layer", "DISTANCE", Densi_BasinV_N)
    Basin_line_N = "in_memory\Basin_line_N"
    arcpy.FeatureToLine_management([BasinN], Basin_line_N)
    BasinLine_erase_N = "in_memory\Basinline_erase_N"
    arcpy.Erase_analysis(Basin_line_N, DrenaStart_buffer1, BasinLine_erase_N)
    BasinLine_dissolve_N="in_memory\BasinLine_dissolve_N"
    arcpy.Dissolve_management(BasinLine_erase_N, BasinLine_dissolve_N, "", "", "SINGLE_PART", "DISSOLVE_LINES")
    pts_Basin_N="in_memory\pts_Basin_N"
    arcpy.FeatureVerticesToPoints_management(BasinLine_dissolve_N, pts_Basin_N, "ALL")

#Add XY field, direcao field and delete overlap points
arcpy.AddXY_management(pts_Basin)
arcpy.DeleteIdentical_management(pts_Basin, "POINT_X;POINT_Y", "0.001 Meters", "0")

#Create linesC, linesC_L and linesC_R
spatial_reference = arcpy.Describe(Basin).spatialReference
arcpy.CreateFeatureclass_management(env.workspace, "linesC_L", "POLYLINE", "", "", "", spatial_reference)
arcpy.CreateFeatureclass_management(env.workspace, "linesC_R", "POLYLINE", "", "", "", spatial_reference)
arcpy.CreateFeatureclass_management(env.workspace, "linesC", "POLYLINE", "", "", "", spatial_reference)
linesC_L = "linesC_L"
linesC_R = "linesC_R"
linesC = "linesC"

#Create layers
expressionZ = '"z_max">=0'
arcpy.MakeFeatureLayer_management (StreamPoints, "StreamPoints_layer", expressionZ)
arcpy.MakeFeatureLayer_management(pts_Basin, "pts_Basin_layer")

##Analyse StreamPoints##
#Create StreamPoints List#
##Generate Cursors
rows_StreamPoints=sorted(arcpy.da.SearchCursor("StreamPoints_layer", "z_maxID"))
rows_SplitStream=sorted(arcpy.da.SearchCursor("SplitStream_layer", "z_maxID"))
#Definig StreamPoints_list
StreamPoints_list = []
##Populate StreamPoints_list
if len(rows_SplitStream)>0:
    StreamPoints_values = []
    for value in rows_StreamPoints:
        StreamPoints_values.append (int(value[0]))
   
    n=1
    while (len(rows_SplitStream)+1)>=n:
        if n==1:
            listP=[]
            for value in StreamPoints_values:
                if value<=rows_SplitStream[0][0]:
                    listP.append(value)
        if n==(len(rows_SplitStream)+1):
            listP=[]
            for value in StreamPoints_values:
                if value>rows_SplitStream[n-2][0]:
                    listP.append(value)
        if n>1 and n<=len(rows_SplitStream):
            listP=[]
            for value in StreamPoints_values:
                if value>rows_SplitStream[n-2][0] and value<=rows_SplitStream[n-1][0]:
                    listP.append(value)
        ##StreamPoints_list
        listP_corect=[]
        len_list=len(listP)
        for e, pt in enumerate (listP):
            if e<len_list-(e+1):
                listP_corect.append(str(listP[e]))
                listP_corect.append(str(listP[len_list-(e+1)]))
                continue
            if e==len_list-(e+1):
                listP_corect.append(str(listP[e]))
                break
            else:
                break
        listP=listP_corect
        for row in listP:
            StreamPoints_list.append(row)
        n+=1
    #Remove duplicate values 
    StreamPoints_list=list(list(OrderedDict.fromkeys(StreamPoints_list).keys()))
else:
    for row in rows_StreamPoints:
        StreamPoints_list.append(int(row[0]))
    ##Invert StreamPoints_list
    StreamPoints_List_corect=[]
    len_list=len(StreamPoints_list)
    for e, pt in enumerate (StreamPoints_list):
        if e<len_list-(e+1):
            StreamPoints_List_corect.append(str(StreamPoints_list[e]))
            StreamPoints_List_corect.append(str(StreamPoints_list[len_list-(e+1)]))
            continue
        if e==len_list-(e+1):
            StreamPoints_List_corect.append(str(StreamPoints_list[e]))
            break
        else:
            break
    StreamPoints_list=StreamPoints_List_corect

#Process all StreamPoints
len_list=len(StreamPoints_list)
pt_n=0
arcpy.AddMessage(StreamPoints_list)
for row_ptdrena in StreamPoints_list:
    pt_n+=1
    arcpy.AddMessage("Processando B{0} Ponto {1}/{2}".format(Basin_id,pt_n,len_list))
    #Get id ptdrena
    ID_StreamPoint = str(row_ptdrena)
    # Make a pt_select layer    
    expressionS = '"z_maxID" ='+ID_StreamPoint
    arcpy.MakeFeatureLayer_management ("StreamPoints_layer", "StreamPoints_layer_S", expressionS)
    #Select Switch Drena_Split segment
    expression_drena='"z_maxID" <> %d'% (int(ID_StreamPoint))
    arcpy.MakeFeatureLayer_management (Stream_Split, "Stream_Split_layer", expression_drena)
           
    # Get pt direction
    dir_rows = arcpy.SearchCursor ("StreamPoints_layer_S")
    dir_row = dir_rows.next()
    dir_seg = int(dir_row.getValue("azimuth2"))
    del dir_rows, dir_row

    #Create expression_leftlines
    LimitL_min = dir_seg
    LimitL_max = LimitL_min + 180
    if LimitL_max<=360:
        expression_leftlines = 'AZIMUTH > %s and AZIMUTH <= %s'% (LimitL_min, LimitL_max)
    elif LimitL_max>360:
        LimitL_max-=360
        expression_leftlines = 'AZIMUTH > %s OR AZIMUTH <= %s'% (LimitL_min, LimitL_max)
    
    ##Create a angle restriction for sightlines
    #Calculate base values
    base1 = dir_seg+90
    if base1>360:
        base1-=360
    base2 = dir_seg-90
    if base2<0:
        base2+=360
    open_ang=5
    base1_min = base1 - open_ang
    if base1_min<0:
        base1_min+=360
    base1_max = base1 + open_ang
    if base1_max>360:
       base1_max-=360 
    base2_min = base2 - open_ang
    if base2_min<0:
        base2_min+=360
    base2_max = base2 + open_ang
    if base2_max>360:
        base2_max-=360
    base1_min = "%f" % base1_min
    base1_max = "%f" % base1_max
    base2_min = "%f" % base2_min
    base2_max = "%f" % base2_max

    # Create expression_sightlines to limit sightlines angles
    expression_sightlines = 'AZIMUTH > %s and AZIMUTH <= %s or AZIMUTH > %s and AZIMUTH<= %s'% (base1_min, base1_max, base2_min, base2_max)
    if base2<=open_ang or base2>360-open_ang:
        expression_sightlines = 'AZIMUTH > %s and AZIMUTH <= %s or AZIMUTH > %s or AZIMUTH<= %s'% (base1_min, base1_max, base2_min, base2_max)
    if base1 <= open_ang or base1>360-open_ang:
        expression_sightlines = 'AZIMUTH > %s or AZIMUTH <= %s or AZIMUTH > %s and AZIMUTH<= %s'% (base1_min, base1_max, base2_min, base2_max)
    
    #Build Sightlines
    sightlines = "in_memory\sightline_pt"+ID_StreamPoint
    arcpy.ddd.ConstructSightLines("StreamPoints_layer_S", "pts_Basin_layer", sightlines, "<None>", "<None>", "<None>", "0.5", "OUTPUT_THE_DIRECTION")
    
    ###Spatial Query### part 1
    #Filter Sightlines with open_angle using expression_sightlines
    #sightlines_Selected = "sightline_pt"+ID_StreamPoint+"_S"
    #arcpy.FeatureClassToFeatureClass_conversion(sightlines, env.workspace, sightlines_Selected, expression_sightlines)
    sightlines_Selected="in_memory\sightline_pt"+ID_StreamPoint+"_S"
    sightlines_Selected_name="sightline_pt"+ID_StreamPoint+"_S"
    arcpy.FeatureClassToFeatureClass_conversion(sightlines, "in_memory", sightlines_Selected_name, expression_sightlines)
    arcpy.MakeFeatureLayer_management (sightlines_Selected, "sightlines_layer")

    arcpy.SelectLayerByLocation_management("sightlines_layer", '', "", "", "SWITCH_SELECTION")
    arcpy.SelectLayerByLocation_management("sightlines_layer", 'intersect', linesC_L, "", "REMOVE_FROM_SELECTION")
    arcpy.SelectLayerByLocation_management("sightlines_layer", 'intersect', linesC_R, "", "REMOVE_FROM_SELECTION")
    arcpy.SelectLayerByLocation_management("sightlines_layer", 'intersect', b_line_0_5, "", "REMOVE_FROM_SELECTION")
    arcpy.SelectLayerByLocation_management("sightlines_layer", 'intersect', "Stream_Split_layer", "", "REMOVE_FROM_SELECTION")
    
    ###Atribute Left Query### part2
    #Build Left Sightlines apling expression_leftline to select left lines
    arcpy.MakeFeatureLayer_management ("sightlines_layer", "sightlinesED_layer")
    sightlines_SelectedL = "in_memory\\sightline_pt"+ID_StreamPoint+"_S_L"
    sightlines_SelectedL_name="sightline_pt"+ID_StreamPoint+"_S_L"
    arcpy.SelectLayerByAttribute_management("sightlinesED_layer", "NEW_SELECTION", expression_leftlines)
    #Export Left Sightlines Selection
    arcpy.FeatureClassToFeatureClass_conversion("sightlinesED_layer", "in_memory", sightlines_SelectedL_name)
    arcpy.AddGeometryAttributes_management (sightlines_SelectedL, "LENGTH", "", "", "")

    ###Atribute Right Query### part2
    #Build Right Sightlines apling invert expression_leftline to select Right lines
    sightlines_SelectedR = "in_memory\sightline_pt"+ID_StreamPoint+"_S_R"
    sightlines_SelectedR_name="sightline_pt"+ID_StreamPoint+"_S_R"
    arcpy.SelectLayerByAttribute_management("sightlinesED_layer", "SWITCH_SELECTION")
    #Export Right Sightlines Selection            
    arcpy.FeatureClassToFeatureClass_conversion("sightlinesED_layer", "in_memory", sightlines_SelectedR_name)
    arcpy.AddGeometryAttributes_management (sightlines_SelectedR, "LENGTH", "", "", "")
  

    ###START - Select the best sightlines###
    #Select Best left line
    lenght_cursor_left = sorted(arcpy.da.SearchCursor(sightlines_SelectedL, ["LENGTH", "OID_TARGET"]))
    if len(lenght_cursor_left)>0:
        Add_L=True
        #lenght_left=lenght_cursor_left[0][0]
        Lenght_left=lenght_cursor_left[0][0]
        m_rowID = lenght_cursor_left[0][1]
        #classL = CalcClass(lenght_left)
        m_rowID = "%d" % m_rowID
        expressionF = 'OID_TARGET='+ m_rowID
        arcpy.MakeFeatureLayer_management (sightlines_SelectedL, "sightlineL_select", expressionF)
        arcpy.Append_management ("sightlineL_select", linesC_L, "NO_TEST", "", "")
    #Select Best Right line
    lenght_cursor_right = sorted(arcpy.da.SearchCursor(sightlines_SelectedR, ["LENGTH", "OID_TARGET"]))
    if len(lenght_cursor_right)>0:
        Add_R=True
        Lenght_right=lenght_cursor_right[0][0]
        m_rowID = lenght_cursor_right[0][1]
        m_rowID = "%d" % m_rowID
        expressionF = 'OID_TARGET='+ m_rowID
        arcpy.MakeFeatureLayer_management (sightlines_SelectedR, "sightlineR_select", expressionF)
        arcpy.Append_management ("sightlineR_select", linesC_R, "NO_TEST", "", "")
    #Clean memory
    try:
        arcpy.Delete_management("sightlines_layer")
        arcpy.Delete_management("sightlines_layer")
        arcpy.Delete_management(sightlines)
        arcpy.Delete_management(sightlines_Selected)
        arcpy.Delete_management(sightlines_SelectedL)
        arcpy.Delete_management(sightlines_SelectedR)
    except:
        pass

        ###END - Select the best sightlines### 

##START - Processing Last Point###
if BasinSpring==True:
    #Get id ptdrena
    arcpy.MakeFeatureLayer_management (pts_Basin_N, "pts_Basin_layer_N")

    #Select Stream Segments
    arcpy.MakeFeatureLayer_management (Stream_Split, "Stream_Split_layer")
    arcpy.SelectLayerByLocation_management("Stream_Split_layer", '', "", "", "SWITCH_SELECTION")
    arcpy.SelectLayerByLocation_management("Stream_Split_layer", 'intersect', "Springs_layer", "", "REMOVE_FROM_SELECTION")       
    
    #Build Sightlines
    sightlines = "in_memory\sightline_ptNascente"
    arcpy.ddd.ConstructSightLines("Springs_layer", "pts_Basin_layer_N", sightlines, "<None>", "<None>", "<None>", "0.5", "OUTPUT_THE_DIRECTION")
    arcpy.MakeFeatureLayer_management (sightlines, "sightlines_layer")
      
    ###Spatial Query### part 1
    arcpy.SelectLayerByLocation_management("sightlines_layer", '', "", "", "SWITCH_SELECTION")
    arcpy.SelectLayerByLocation_management("sightlines_layer", 'intersect', linesC_L, "", "REMOVE_FROM_SELECTION")
    arcpy.SelectLayerByLocation_management("sightlines_layer", 'intersect', linesC_R, "", "REMOVE_FROM_SELECTION")
    sightlines_SelectedED = "in_memory\sightline_ptNascente_ED"
    sightlines_SelectedED_name="sightline_ptNascente_ED"
    arcpy.FeatureClassToFeatureClass_conversion("sightlines_layer", "in_memory", sightlines_SelectedED_name)

    ##Spatial Query### part 2
    arcpy.MakeFeatureLayer_management (sightlines_SelectedED, "sightlines_SelectedED_layer")
    arcpy.SelectLayerByLocation_management("sightlines_SelectedED_layer", '', "", "", "SWITCH_SELECTION")
    arcpy.SelectLayerByLocation_management("sightlines_SelectedED_layer", 'intersect', b_line_0_5, "", "REMOVE_FROM_SELECTION")
    arcpy.Append_management ("sightlines_SelectedED_layer", linesC, "NO_TEST", "", "")
    #Clean memory
    try:
        arcpy.Delete_management(sightlines)
        arcpy.Delete_management(sightlines_SelectedED)
    except:
        pass

###END - Last Point Processing###

#Apeend sightlines
arcpy.Append_management(linesC_L, linesC, "NO_TEST", "", "")
arcpy.Append_management(linesC_R, linesC, "NO_TEST", "", "")

# Build Dissecation pol
infeatures = [linesC, Stream, Basin]
DissecH_pol = "DisH_B"+Basin_id
clusTol = "0.01 Meters"
arcpy.FeatureToPolygon_management(infeatures, DissecH_pol, clusTol,"NO_ATTRIBUTES", "")

# Add Horizontal dissecation field
arcpy.AddField_management(DissecH_pol, "Classe_Dis_C1", "Text", "", "", "", "", "NULLABLE")
if c_str_C2!="0":
    arcpy.AddField_management(DissecH_pol, "Classe_Dis_C2", "Text", "", "", "", "", "NULLABLE")
if c_str_C3!="0":
    arcpy.AddField_management(DissecH_pol, "Classe_Dis_C3", "Text", "", "", "", "", "NULLABLE")

# Calculate max dist table
MaxDist_Table = env.workspace+"\MaxDist_table"
outZSaT = ZonalStatisticsAsTable(DissecH_pol, "OBJECTID", DistMap, MaxDist_Table, "NODATA", "MAXIMUM")

#Add Join
arcpy.MakeFeatureLayer_management(DissecH_pol, "DissecH_pol_lyr")
arcpy.JoinField_management("DissecH_pol_lyr", "OBJECTID", MaxDist_Table, "OBJECTID_1", ["MAX"])
DissecH_pol2 = "DisH2_B"+Basin_id
arcpy.FeatureClassToFeatureClass_conversion("DissecH_pol_lyr", env.workspace, DissecH_pol2)

#Calculate Dissecation field with update cursor
cursor = arcpy.UpdateCursor(DissecH_pol2)
for row in cursor:
    value=row.getValue("MAX")
    class_pol_C1=CalcClass(value, Classes_C1)
    if isinstance (class_pol_C1, int)==True:
        classe_C1= "Classe %d" %class_pol_C1
        row.setValue("Classe_Dis_C1", classe_C1)
    else:
        arcpy.AddMessage("ALERTA!!!POLIGONO NÃO CLASSIFICADO. MAIOR CLASSE DE DISSECAÇÃO FORNECIDA MENOR QUE A DISSECAÇÃO DO POLIGONO")
    if c_str_C2!="0":
        class_pol_C2=CalcClass(value, Classes_C2)
        if isinstance (class_pol_C2, int)==True:
            classe_C2= "Classe %d" %class_pol_C2
            row.setValue("Classe_Dis_C2", classe_C2)
        else:
            arcpy.AddMessage("ALERTA!!!POLIGONO NÃO CLASSIFICADO. MAIOR CLASSE DE DISSECAÇÃO FORNECIDA MENOR QUE A DISSECAÇÃO DO POLIGONO")
    if c_str_C3!="0":
        class_pol_C3=CalcClass(value, Classes_C3)
        if isinstance (class_pol_C3, int)==True:
            classe_C3= "Classe %d" %class_pol_C3
            row.setValue("Classe_Dis_C3", classe_C3)
        else:
            arcpy.AddMessage("ALERTA!!!POLIGONO NÃO CLASSIFICADO. MAIOR CLASSE DE DISSECAÇÃO FORNECIDA MENOR QUE A DISSECAÇÃO DO POLIGONO")
    cursor.updateRow(row)
del cursor, row

#Dissolve polygons based on dissecation classes
DissecH_Dissolve_C1="in_memory"+"\\"+"DissHC1_B"+Basin_id
arcpy.Dissolve_management(DissecH_pol2, DissecH_Dissolve_C1, ["Classe_Dis_C1"],"", "SINGLE_PART")
if c_str_C2!="0":
    DissecH_Dissolve_C2="in_memory"+"\\"+"DissHC2_B"+Basin_id
    arcpy.Dissolve_management(DissecH_pol2, DissecH_Dissolve_C2, ["Classe_Dis_C2"],"", "SINGLE_PART")
if c_str_C3!="0":
    DissecH_Dissolve_C3="in_memory"+"\\"+"DissHC3_B"+Basin_id
    arcpy.Dissolve_management(DissecH_pol2, DissecH_Dissolve_C3, ["Classe_Dis_C3"],"", "SINGLE_PART")    
    
#Split polygons
infeatures=[DissecH_Dissolve_C1,Stream]
Basin_split_C1="in_memory"+"\\"+"B"+Basin_id+"_Split_C1"
arcpy.FeatureToPolygon_management(infeatures, Basin_split_C1, clusTol,"NO_ATTRIBUTES", "")
if c_str_C2!="0":
    infeatures=[DissecH_Dissolve_C2,Stream]
    Basin_split_C2="in_memory"+"\\"+"B"+Basin_id+"_Split_C2"
    arcpy.FeatureToPolygon_management(infeatures, Basin_split_C2, clusTol,"NO_ATTRIBUTES", "")
if c_str_C3!="0":
    infeatures=[DissecH_Dissolve_C3,Stream]
    Basin_split_C3="in_memory"+"\\"+"B"+Basin_id+"_Split_C3"
    arcpy.FeatureToPolygon_management(infeatures, Basin_split_C3, clusTol,"NO_ATTRIBUTES", "")
    
#Union polygons
infeatures=[DissecH_Dissolve_C1,Basin_split_C1]
DissecH_Union_C1="in_memory"+"\\"+"DissecH_UnionC1_B"+Basin_id
arcpy.Union_analysis(infeatures,DissecH_Union_C1,"ALL",clusTol)
if c_str_C2!="0":
    infeatures=[DissecH_Dissolve_C2,Basin_split_C2]
    DissecH_Union_C2="in_memory"+"\\"+"DissecH_UnionC2_B"+Basin_id
    arcpy.Union_analysis(infeatures,DissecH_Union_C2,"ALL",clusTol)
if c_str_C3!="0":
    infeatures=[DissecH_Dissolve_C3,Basin_split_C3]
    DissecH_Union_C3="in_memory"+"\\"+"DissecH_UnionC3_B"+Basin_id
    arcpy.Union_analysis(infeatures,DissecH_Union_C3,"ALL",clusTol)

#Clip polygons
DissecH_F_C1="DissecHC1_B"+Basin_id
arcpy.Clip_analysis (DissecH_Union_C1, Basin, DissecH_F_C1)
if c_str_C2!="0":
    DissecH_F_C2="DissecHC2_B"+Basin_id
    arcpy.Clip_analysis (DissecH_Union_C2, Basin, DissecH_F_C2)
if c_str_C3!="0":
    DissecH_F_C3="DissecHC3_B"+Basin_id
    arcpy.Clip_analysis (DissecH_Union_C3, Basin, DissecH_F_C3)


#Clean memory
try:
    arcpy.Delete_management(Stream_Split)
    arcpy.Delete_management(DistMap)
    arcpy.Delete_management(Stream_buffer2m)
    arcpy.Delete_management(StreamPoints)
    arcpy.Delete_management(BasinN)
    arcpy.Delete_management(Basin_line)
    arcpy.Delete_management(b_line_0_5)
    arcpy.Delete_management(StreamStart_point)
    arcpy.Delete_management(DrenaStart_buffer1)
    arcpy.Delete_management(BasinLine_erase)
    arcpy.Delete_management(BasinLine_dissolve)
    arcpy.Delete_management(pts_Basin)
    arcpy.Delete_management(Basin_line_N)
    arcpy.Delete_management(BasinLine_erase_N)
    arcpy.Delete_management(BasinLine_dissolve_N)
    arcpy.Delete_management(pts_Basin_N)
    arcpy.Delete_management(b100)
    arcpy.Delete_management(b_0_5)
    arcpy.Delete_management(DissecH_Dissolve_C1)
    arcpy.Delete_management(DissecH_Dissolve_C2)
    arcpy.Delete_management(DissecH_Dissolve_C3)
    arcpy.Delete_management(Basin_split_C1)
    arcpy.Delete_management(Basin_split_C2)
    arcpy.Delete_management(Basin_split_C3)
    arcpy.Delete_management(DissecH_Union_C1)
    arcpy.Delete_management(DissecH_Union_C2)
    arcpy.Delete_management(DissecH_Union_C3)
except:
    pass
