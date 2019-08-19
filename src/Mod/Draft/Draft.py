# -*- coding: utf-8 -*-

#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2009, 2010                                              *
#*   Yorik van Havre <yorik@uncreated.net>, Ken Cline <cline@frii.com>     *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

#from __future__ import division

__title__="FreeCAD Draft Workbench"
__author__ = "Yorik van Havre, Werner Mayer, Martin Burbaum, Ken Cline, Dmitry Chigrin, Daniel Falck"
__url__ = "http://www.freecadweb.org"

## \addtogroup DRAFT
#  \brief Create and manipulate basic 2D objects
#
#  This module offers a range of tools to create and manipulate basic 2D objects
#
#  The module allows to create 2D geometric objects such as line, rectangle, circle,
#  etc, modify these objects by moving, scaling or rotating them, and offers a couple of
#  other utilities to manipulate further these objects, such as decompose them (downgrade)
#  into smaller elements.
#
#  The functionality of the module is divided into GUI tools, usable from the
#  FreeCAD interface, and corresponding python functions, that can perform the same
#  operation programmatically.
#
#  @{

"""The Draft module offers a range of tools to create and manipulate basic 2D objects"""

import FreeCAD, math, sys, os, DraftVecUtils, WorkingPlane
from FreeCAD import Vector

if FreeCAD.GuiUp:
    import FreeCADGui, Draft_rc
    from PySide import QtCore
    from PySide.QtCore import QT_TRANSLATE_NOOP
    gui = True
    #from DraftGui import translate
else:
    def QT_TRANSLATE_NOOP(ctxt,txt):
        return txt
    #print("FreeCAD Gui not present. Draft module will have some features disabled.")
    gui = False

def translate(ctx,txt):
    return txt

arrowtypes = ["Dot","Circle","Arrow","Tick","Tick-2"]

#---------------------------------------------------------------------------
# Backwards compatibility
#---------------------------------------------------------------------------

import DraftLayer
_VisGroup = DraftLayer.Layer
_ViewProviderVisGroup = DraftLayer.ViewProviderLayer
makeLayer = DraftLayer.makeLayer

# import DraftFillet
# Fillet = DraftFillet.Fillet
# makeFillet = DraftFillet.makeFillet

#---------------------------------------------------------------------------
# General functions
#---------------------------------------------------------------------------

def stringencodecoin(ustr):
    """stringencodecoin(str): Encodes a unicode object to be used as a string in coin"""
    try:
        from pivy import coin
        coin4 = coin.COIN_MAJOR_VERSION >= 4
    except (ImportError, AttributeError):
        coin4 = False
    if coin4:
        return ustr.encode('utf-8')
    else:
        return ustr.encode('latin1')

def typecheck (args_and_types, name="?"):
    """typecheck([arg1,type),(arg2,type),...]): checks arguments types"""
    for v,t in args_and_types:
        if not isinstance (v,t):
            w = "typecheck[" + str(name) + "]: "
            w += str(v) + " is not " + str(t) + "\n"
            FreeCAD.Console.PrintWarning(w)
            raise TypeError("Draft." + str(name))

def getParamType(param):
    if param in ["dimsymbol","dimPrecision","dimorientation","precision","defaultWP",
                 "snapRange","gridEvery","linewidth","UiMode","modconstrain","modsnap",
                 "maxSnapEdges","modalt","HatchPatternResolution","snapStyle",
                 "dimstyle","gridSize"]:
        return "int"
    elif param in ["constructiongroupname","textfont","patternFile","template",
                   "snapModes","FontFile","ClonePrefix","labeltype"] \
        or "inCommandShortcut" in param:
        return "string"
    elif param in ["textheight","tolerance","gridSpacing","arrowsize","extlines","dimspacing",
                   "dimovershoot","extovershoot"]:
        return "float"
    elif param in ["selectBaseObjects","alwaysSnap","grid","fillmode","saveonexit","maxSnap",
                   "SvgLinesBlack","dxfStdSize","showSnapBar","hideSnapBar","alwaysShowGrid",
                   "renderPolylineWidth","showPlaneTracker","UsePartPrimitives","DiscretizeEllipses",
                   "showUnit"]:
        return "bool"
    elif param in ["color","constructioncolor","snapcolor","gridColor"]:
        return "unsigned"
    else:
        return None

def getParam(param,default=None):
    """getParam(parameterName): returns a Draft parameter value from the current config"""
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft")
    t = getParamType(param)
    #print("getting param ",param, " of type ",t, " default: ",str(default))
    if t == "int":
        if default == None:
            default = 0
        if param == "linewidth":
            return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").GetInt("DefaultShapeLineWidth",default)
        return p.GetInt(param,default)
    elif t == "string":
        if default == None:
            default = ""
        return p.GetString(param,default)
    elif t == "float":
        if default == None:
            default = 0
        return p.GetFloat(param,default)
    elif t == "bool":
        if default == None:
            default = False
        return p.GetBool(param,default)
    elif t == "unsigned":
        if default == None:
            default = 0
        if param == "color":
            return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").GetUnsigned("DefaultShapeLineColor",default)
        return p.GetUnsigned(param,default)
    else:
        return None

def setParam(param,value):
    """setParam(parameterName,value): sets a Draft parameter with the given value"""
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft")
    t = getParamType(param)
    if t == "int":
        if param == "linewidth":
            FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").SetInt("DefaultShapeLineWidth",value)
        else:
            p.SetInt(param,value)
    elif t == "string":
        p.SetString(param,value)
    elif t == "float":
        p.SetFloat(param,value)
    elif t == "bool":
        p.SetBool(param,value)
    elif t == "unsigned":
        if param == "color":
            FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View").SetUnsigned("DefaultShapeLineColor",value)
        else:
            p.SetUnsigned(param,value)

def precision():
    """precision(): returns the precision value from Draft user settings"""
    return getParam("precision",6)

def tolerance():
    """tolerance(): returns the tolerance value from Draft user settings"""
    return getParam("tolerance",0.05)

def epsilon():
    ''' epsilon(): returns a small number based on Draft.tolerance() for use in
    floating point comparisons.  Use with caution. '''
    return (1.0/(10.0**tolerance()))

def getRealName(name):
    """getRealName(string): strips the trailing numbers from a string name"""
    for i in range(1,len(name)):
        if not name[-i] in '1234567890':
            return name[:len(name)-(i-1)]
    return name

def getType(obj):
    """getType(object): returns the Draft type of the given object"""
    import Part
    if not obj:
        return None
    if isinstance(obj,Part.Shape):
        return "Shape"
    if "Proxy" in obj.PropertiesList:
        if hasattr(obj.Proxy,"Type"):
            return obj.Proxy.Type
    if obj.isDerivedFrom("Sketcher::SketchObject"):
        return "Sketch"
    if (obj.TypeId == "Part::Line"):
        return "Part::Line"
    if (obj.TypeId == "Part::Offset2D"):
        return "Offset2D"
    if obj.isDerivedFrom("Part::Feature"):
        return "Part"
    if (obj.TypeId == "App::Annotation"):
        return "Annotation"
    if obj.isDerivedFrom("Mesh::Feature"):
        return "Mesh"
    if obj.isDerivedFrom("Points::Feature"):
        return "Points"
    if (obj.TypeId == "App::DocumentObjectGroup"):
        return "Group"
    if (obj.TypeId == "App::Part"):
        return "App::Part"
    return "Unknown"

def getObjectsOfType(objectslist,typ):
    """getObjectsOfType(objectslist,typ): returns a list of objects of type "typ" found
    in the given object list"""
    objs = []
    for o in objectslist:
        if getType(o) == typ:
            objs.append(o)
    return objs

def get3DView():
    """get3DView(): returns the current view if it is 3D, or the first 3D view found, or None"""
    if FreeCAD.GuiUp:
        import FreeCADGui
        v = FreeCADGui.ActiveDocument.ActiveView
        if "View3DInventor" in str(type(v)):
            return v
        #print("Debug: Draft: Warning, not working in active view")
        v = FreeCADGui.ActiveDocument.mdiViewsOfType("Gui::View3DInventor")
        if v:
            return v[0]
    return None

def isClone(obj,objtype,recursive=False):
    """isClone(obj,objtype,[recursive]): returns True if the given object is
    a clone of an object of the given type. If recursive is True, also check if
    the clone is a clone of clone (of clone...)  of the given type."""
    if isinstance(objtype,list):
        return any([isClone(obj,t,recursive) for t in objtype])
    if getType(obj) == "Clone":
        if len(obj.Objects) == 1:
            if getType(obj.Objects[0]) == objtype:
                return True
            elif recursive and (getType(obj.Objects[0]) == "Clone"):
                return isClone(obj.Objects[0],objtype,recursive)
    elif hasattr(obj,"CloneOf"):
        if obj.CloneOf:
            return True
    return False

def getGroupNames():
    """returns a list of existing groups in the document"""
    glist = []
    doc = FreeCAD.ActiveDocument
    for obj in doc.Objects:
        if obj.isDerivedFrom("App::DocumentObjectGroup") or (getType(obj) in ["Floor","Building","Site"]):
            glist.append(obj.Name)
    return glist

def ungroup(obj):
    """removes the current object from any group it belongs to"""
    for g in getGroupNames():
        grp = FreeCAD.ActiveDocument.getObject(g)
        if obj in grp.Group:
            g = grp.Group
            g.remove(obj)
            grp.Group = g

def autogroup(obj):
    """adds a given object to the autogroup, if applicable"""
    if FreeCAD.GuiUp:
        if hasattr(FreeCADGui,"draftToolBar"):
            if hasattr(FreeCADGui.draftToolBar,"autogroup") and (not FreeCADGui.draftToolBar.isConstructionMode()):
                if FreeCADGui.draftToolBar.autogroup != None:
                    g = FreeCAD.ActiveDocument.getObject(FreeCADGui.draftToolBar.autogroup)
                    if g:
                        found = False
                        for o in g.Group:
                            if o.Name == obj.Name:
                                found = True
                        if not found:
                            gr = g.Group
                            gr.append(obj)
                            g.Group = gr
                else:
                    # Arch active container
                    a = FreeCADGui.ActiveDocument.ActiveView.getActiveObject("Arch")
                    if a:
                        a.addObject(obj)

def dimSymbol(symbol=None,invert=False):
    """returns the current dim symbol from the preferences as a pivy SoMarkerSet"""
    if symbol == None:
        symbol = getParam("dimsymbol",0)
    from pivy import coin
    if symbol == 0:
        return coin.SoSphere()
    elif symbol == 1:
        marker = coin.SoMarkerSet()
        marker.markerIndex = FreeCADGui.getMarkerIndex("circle", 9)
        return marker
    elif symbol == 2:
        marker = coin.SoSeparator()
        t = coin.SoTransform()
        t.translation.setValue((0,-2,0))
        t.center.setValue((0,2,0))
        if invert:
            t.rotation.setValue(coin.SbVec3f((0,0,1)),-math.pi/2)
        else:
            t.rotation.setValue(coin.SbVec3f((0,0,1)),math.pi/2)
        c = coin.SoCone()
        c.height.setValue(4)
        marker.addChild(t)
        marker.addChild(c)
        return marker
    elif symbol == 3:
        marker = coin.SoSeparator()
        c = coin.SoCoordinate3()
        c.point.setValues([(-1,-2,0),(0,2,0),(1,2,0),(0,-2,0)])
        f = coin.SoFaceSet()
        marker.addChild(c)
        marker.addChild(f)
        return marker
    elif symbol == 4:
        return dimDash((-1.5,-1.5,0),(1.5,1.5,0))
    else:
        print("Draft.dimsymbol: Not implemented")
        return coin.SoSphere()

def dimDash(p1, p2):
    """dimDash(p1, p2): returns pivy SoSeparator.
    Used for making Tick-2, DimOvershoot, ExtOvershoot dashes.
    """
    from pivy import coin
    dash = coin.SoSeparator()
    v = coin.SoVertexProperty()
    v.vertex.set1Value(0, p1)
    v.vertex.set1Value(1, p2)
    l = coin.SoLineSet()
    l.vertexProperty = v
    dash.addChild(l)
    return dash

def shapify(obj):
    """shapify(object): transforms a parametric shape object into
    non-parametric and returns the new object"""
    try:
        shape = obj.Shape
    except Exception:
        return None
    if len(shape.Faces) == 1:
        name = "Face"
    elif len(shape.Solids) == 1:
        name = "Solid"
    elif len(shape.Solids) > 1:
        name = "Compound"
    elif len(shape.Faces) > 1:
        name = "Shell"
    elif len(shape.Wires) == 1:
        name = "Wire"
    elif len(shape.Edges) == 1:
        import DraftGeomUtils
        if DraftGeomUtils.geomType(shape.Edges[0]) == "Line":
            name = "Line"
        else:
            name = "Circle"
    else:
        name = getRealName(obj.Name)
    FreeCAD.ActiveDocument.removeObject(obj.Name)
    newobj = FreeCAD.ActiveDocument.addObject("Part::Feature",name)
    newobj.Shape = shape

    return newobj

def getGroupContents(objectslist,walls=False,addgroups=False,spaces=False,noarchchild=False):
    """getGroupContents(objectlist,[walls,addgroups]): if any object of the given list
    is a group, its content is appended to the list, which is returned. If walls is True,
    walls and structures are also scanned for included windows or rebars. If addgroups
    is true, the group itself is also included in the list."""
    def getWindows(obj):
        l = []
        if getType(obj) in ["Wall","Structure"]:
            for o in obj.OutList:
                l.extend(getWindows(o))
            for i in obj.InList:
                if (getType(i) in ["Window"]) or isClone(obj,"Window"):
                    if hasattr(i,"Hosts"):
                        if obj in i.Hosts:
                            l.append(i)
                elif (getType(i) in ["Rebar"]) or isClone(obj,"Rebar"):
                    if hasattr(i,"Host"):
                        if obj == i.Host:
                            l.append(i)
        elif (getType(obj) in ["Window","Rebar"]) or isClone(obj,["Window","Rebar"]):
            l.append(obj)
        return l

    newlist = []
    if not isinstance(objectslist,list):
        objectslist = [objectslist]
    for obj in objectslist:
        if obj:
            if obj.isDerivedFrom("App::DocumentObjectGroup") or ((getType(obj) in ["App::Part","Building","BuildingPart","Space","Site"]) and hasattr(obj,"Group")):
                if getType(obj) == "Site":
                    if obj.Shape:
                        newlist.append(obj)
                if obj.isDerivedFrom("Drawing::FeaturePage"):
                    # skip if the group is a page
                    newlist.append(obj)
                else:
                    if addgroups or (spaces and (getType(obj) == "Space")):
                        newlist.append(obj)
                    if noarchchild and (getType(obj) in ["Building","BuildingPart"]):
                        pass
                    else:
                        newlist.extend(getGroupContents(obj.Group,walls,addgroups))
            else:
                #print("adding ",obj.Name)
                newlist.append(obj)
                if walls:
                    newlist.extend(getWindows(obj))

    # cleaning possible duplicates
    cleanlist = []
    for obj in newlist:
        if not obj in cleanlist:
            cleanlist.append(obj)
    return cleanlist

def removeHidden(objectslist):
    """removeHidden(objectslist): removes hidden objects from the list"""
    newlist = objectslist[:]
    for o in objectslist:
        if o.ViewObject:
            if not o.ViewObject.isVisible():
                newlist.remove(o)
    return newlist

def printShape(shape):
    """prints detailed information of a shape"""
    print("solids: ", len(shape.Solids))
    print("faces: ", len(shape.Faces))
    print("wires: ", len(shape.Wires))
    print("edges: ", len(shape.Edges))
    print("verts: ", len(shape.Vertexes))
    if shape.Faces:
        for f in range(len(shape.Faces)):
            print("face ",f,":")
            for v in shape.Faces[f].Vertexes:
                print("    ",v.Point)
    elif shape.Wires:
        for w in range(len(shape.Wires)):
            print("wire ",w,":")
            for v in shape.Wires[w].Vertexes:
                print("    ",v.Point)
    else:
        for v in shape.Vertexes:
            print("    ",v.Point)

def compareObjects(obj1,obj2):
    """Prints the differences between 2 objects"""

    if obj1.TypeId != obj2.TypeId:
        print(obj1.Name + " and " + obj2.Name + " are of different types")
    elif getType(obj1) != getType(obj2):
        print(obj1.Name + " and " + obj2.Name + " are of different types")
    else:
        for p in obj1.PropertiesList:
            if p in obj2.PropertiesList:
                if p in ["Shape","Label"]:
                    pass
                elif p ==  "Placement":
                    delta = str((obj1.Placement.Base.sub(obj2.Placement.Base)).Length)
                    print("Objects have different placements. Distance between the 2: " + delta + " units")
                else:
                    if getattr(obj1,p) != getattr(obj2,p):
                        print("Property " + p + " has a different value")
            else:
                print("Property " + p + " doesn't exist in one of the objects")

def formatObject(target,origin=None):
    """
    formatObject(targetObject,[originObject]): This function applies
    to the given target object the current properties
    set on the toolbar (line color and line width),
    or copies the properties of another object if given as origin.
    It also places the object in construction group if needed.
    """
    if not target:
        return
    obrep = target.ViewObject
    if not obrep:
        return
    ui = None
    if gui:
        if hasattr(FreeCADGui,"draftToolBar"):
            ui = FreeCADGui.draftToolBar
    if ui:
        doc = FreeCAD.ActiveDocument
        if ui.isConstructionMode():
            col = fcol = ui.getDefaultColor("constr")
            gname = getParam("constructiongroupname","Construction")
            grp = doc.getObject(gname)
            if not grp:
                grp = doc.addObject("App::DocumentObjectGroup",gname)
            grp.addObject(target)
            if hasattr(obrep,"Transparency"):
                obrep.Transparency = 80
        else:
            col = ui.getDefaultColor("ui")
            fcol = ui.getDefaultColor("face")
        col = (float(col[0]),float(col[1]),float(col[2]),0.0)
        fcol = (float(fcol[0]),float(fcol[1]),float(fcol[2]),0.0)
        lw = ui.linewidth
        fs = ui.fontsize
        if not origin or not hasattr(origin,'ViewObject'):
            if "FontSize" in obrep.PropertiesList: obrep.FontSize = fs
            if "TextColor" in obrep.PropertiesList: obrep.TextColor = col
            if "LineWidth" in obrep.PropertiesList: obrep.LineWidth = lw
            if "PointColor" in obrep.PropertiesList: obrep.PointColor = col
            if "LineColor" in obrep.PropertiesList: obrep.LineColor = col
            if "ShapeColor" in obrep.PropertiesList: obrep.ShapeColor = fcol
        else:
            matchrep = origin.ViewObject
            for p in matchrep.PropertiesList:
                if not p in ["DisplayMode","BoundingBox","Proxy","RootNode","Visibility"]:
                    if p in obrep.PropertiesList:
                        if not obrep.getEditorMode(p):
                            if hasattr(getattr(matchrep,p),"Value"):
                                val = getattr(matchrep,p).Value
                            else:
                                val = getattr(matchrep,p)
                            try:
                                setattr(obrep,p,val)
                            except Exception:
                                pass
            if matchrep.DisplayMode in obrep.listDisplayModes():
                obrep.DisplayMode = matchrep.DisplayMode
            if hasattr(matchrep,"DiffuseColor") and hasattr(obrep,"DiffuseColor"):
                obrep.DiffuseColor = matchrep.DiffuseColor

def getSelection():
    """getSelection(): returns the current FreeCAD selection"""
    if gui:
        return FreeCADGui.Selection.getSelection()
    return None

def getSelectionEx():
    """getSelectionEx(): returns the current FreeCAD selection (with subobjects)"""
    if gui:
        return FreeCADGui.Selection.getSelectionEx()
    return None

def select(objs=None):
    """select(object): deselects everything and selects only the passed object or list"""
    if gui:
        FreeCADGui.Selection.clearSelection()
        if objs:
            if not isinstance(objs,list):
                objs = [objs]
            for obj in objs:
                if obj:
                    FreeCADGui.Selection.addSelection(obj)

def loadSvgPatterns():
    """loads the default Draft SVG patterns and custom patters if available"""
    import importSVG
    from PySide import QtCore
    FreeCAD.svgpatterns = {}
    # getting default patterns
    patfiles = QtCore.QDir(":/patterns").entryList()
    for fn in patfiles:
        fn = ":/patterns/"+str(fn)
        f = QtCore.QFile(fn)
        f.open(QtCore.QIODevice.ReadOnly)
        p = importSVG.getContents(str(f.readAll()),'pattern',True)
        if p:
            for k in p:
                p[k] = [p[k],fn]
            FreeCAD.svgpatterns.update(p)
    # looking for user patterns
    altpat = getParam("patternFile","")
    if os.path.isdir(altpat):
        for f in os.listdir(altpat):
            if f[-4:].upper() == ".SVG":
                p = importSVG.getContents(altpat+os.sep+f,'pattern')
                if p:
                    for k in p:
                        p[k] = [p[k],altpat+os.sep+f]
                    FreeCAD.svgpatterns.update(p)

def svgpatterns():
    """svgpatterns(): returns a dictionary with installed SVG patterns"""
    if hasattr(FreeCAD,"svgpatterns"):
        return FreeCAD.svgpatterns
    else:
        loadSvgPatterns()
        if hasattr(FreeCAD,"svgpatterns"):
            return FreeCAD.svgpatterns
    return {}

def loadTexture(filename,size=None):
    """loadTexture(filename,[size]): returns a SoSFImage from a file. If size
    is defined (an int or a tuple), and provided the input image is a png file,
    it will be scaled to match the given size."""
    if gui:
        from pivy import coin
        from PySide import QtGui,QtSvg
        try:
            p = QtGui.QImage(filename)
            # buggy - TODO: allow to use resolutions
            #if size and (".svg" in filename.lower()):
            #    # this is a pattern, not a texture
            #    if isinstance(size,int):
            #        size = (size,size)
            #    svgr = QtSvg.QSvgRenderer(filename)
            #    p = QtGui.QImage(size[0],size[1],QtGui.QImage.Format_ARGB32)
            #    pa = QtGui.QPainter()
            #    pa.begin(p)
            #    svgr.render(pa)
            #    pa.end()
            #else:
            #    p = QtGui.QImage(filename)
            size = coin.SbVec2s(p.width(), p.height())
            buffersize = p.byteCount()
            numcomponents = int (float(buffersize) / ( size[0] * size[1] ))

            img = coin.SoSFImage()
            width = size[0]
            height = size[1]
            byteList = []
            isPy2 = sys.version_info.major < 3

            for y in range(height):
                #line = width*numcomponents*(height-(y));
                for x in range(width):
                    rgb = p.pixel(x,y)
                    if numcomponents == 1:
                        if isPy2:
                            byteList.append(chr(QtGui.qGray( rgb )))
                        else:
                            byteList.append(chr(QtGui.qGray( rgb )).encode('latin-1'))
                    elif numcomponents == 2:
                        if isPy2:
                            byteList.append(chr(QtGui.qGray( rgb )))
                            byteList.append(chr(QtGui.qAlpha( rgb )))
                        else:
                            byteList.append(chr(QtGui.qGray( rgb )).encode('latin-1'))
                            byteList.append(chr(QtGui.qAlpha( rgb )).encode('latin-1'))
                    elif numcomponents == 3:
                        if isPy2:
                            byteList.append(chr(QtGui.qRed( rgb )))
                            byteList.append(chr(QtGui.qGreen( rgb )))
                            byteList.append(chr(QtGui.qBlue( rgb )))
                        else:
                            byteList.append(chr(QtGui.qRed( rgb )).encode('latin-1'))
                            byteList.append(chr(QtGui.qGreen( rgb )).encode('latin-1'))
                            byteList.append(chr(QtGui.qBlue( rgb )).encode('latin-1'))
                    elif numcomponents == 4:
                        if isPy2:
                            byteList.append(chr(QtGui.qRed( rgb )))
                            byteList.append(chr(QtGui.qGreen( rgb )))
                            byteList.append(chr(QtGui.qBlue( rgb )))
                            byteList.append(chr(QtGui.qAlpha( rgb )))
                        else:
                            byteList.append(chr(QtGui.qRed( rgb )).encode('latin-1'))
                            byteList.append(chr(QtGui.qGreen( rgb )).encode('latin-1'))
                            byteList.append(chr(QtGui.qBlue( rgb )).encode('latin-1'))
                            byteList.append(chr(QtGui.qAlpha( rgb )).encode('latin-1'))
                    #line += numcomponents

            bytes = b"".join(byteList)
            img.setValue(size, numcomponents, bytes)
        except:
            print("Draft: unable to load texture")
            return None
        else:
            return img
    return None

def getMovableChildren(objectslist,recursive=True):
    """getMovableChildren(objectslist,[recursive]): extends the given list of objects
    with all child objects that have a "MoveWithHost" property set to True. If
    recursive is True, all descendents are considered, otherwise only direct children."""
    added = []
    if not isinstance(objectslist,list):
        objectslist = [objectslist]
    for obj in objectslist:
        if not (getType(obj) in ["Clone","SectionPlane","Facebinder","BuildingPart"]):
            # objects that should never move their children
            children = obj.OutList
            if  hasattr(obj,"Proxy"):
                if obj.Proxy:
                    if hasattr(obj.Proxy,"getSiblings") and not(getType(obj) in ["Window"]):
                        #children.extend(obj.Proxy.getSiblings(obj))
                        pass
            for child in children:
                if hasattr(child,"MoveWithHost"):
                    if child.MoveWithHost:
                        if hasattr(obj,"CloneOf"):
                            if obj.CloneOf:
                                if obj.CloneOf.Name != child.Name:
                                    added.append(child)
                            else:
                                added.append(child)
                        else:
                            added.append(child)
            if recursive:
                added.extend(getMovableChildren(children))
    return added


def makeArray(baseobject,arg1,arg2,arg3,arg4=None,arg5=None,arg6=None,name="Array",useLink=False):
    """makeArray(object,xvector,yvector,xnum,ynum,[name]) for rectangular array, or
    makeArray(object,xvector,yvector,zvector,xnum,ynum,znum,[name]) for rectangular array, or
    makeArray(object,center,totalangle,totalnum,[name]) for polar array, or
    makeArray(object,rdistance,tdistance,axis,center,ncircles,symmetry,[name]) for circular array:
    Creates an array of the given object
    with, in case of rectangular array, xnum of iterations in the x direction
    at xvector distance between iterations, same for y direction with yvector and ynum,
    same for z direction with zvector and znum. In case of polar array, center is a vector, 
    totalangle is the angle to cover (in degrees) and totalnum is the number of objects, 
    including the original. In case of a circular array, rdistance is the distance of the 
    circles, tdistance is the distance within circles, axis the rotation-axes, center the
    center of rotation, ncircles the number of circles and symmetry the number
    of symmetry-axis of the distribution. The result is a parametric Draft Array.
    """

    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if useLink:
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name,_Array(None),None,True)
    else:
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
        _Array(obj)
    obj.Base = baseobject
    if arg6:
        if isinstance(arg1, (int, float)):
            obj.ArrayType = "circular"
            obj.RadialDistance = arg1
            obj.TangentialDistance = arg2
            obj.Axis = arg3
            obj.Center = arg4
            obj.NumberCircles = arg5
            obj.Symmetry = arg6
        else:
            obj.ArrayType = "ortho"
            obj.IntervalX = arg1
            obj.IntervalY = arg2
            obj.IntervalZ = arg3
            obj.NumberX = arg4
            obj.NumberY = arg5
            obj.NumberZ = arg6
    elif arg4:
        obj.ArrayType = "ortho"
        obj.IntervalX = arg1
        obj.IntervalY = arg2
        obj.NumberX = arg3
        obj.NumberY = arg4
    else:
        obj.ArrayType = "polar"
        obj.Center = arg1
        obj.Angle = arg2
        obj.NumberPolar = arg3
    if gui:
        if useLink:
            _ViewProviderDraftLink(obj.ViewObject)
        else:
            _ViewProviderDraftArray(obj.ViewObject)
            formatObject(obj,obj.Base)
            if len(obj.Base.ViewObject.DiffuseColor) > 1:
                obj.ViewObject.Proxy.resetColors(obj.ViewObject)
        baseobject.ViewObject.hide()
        select(obj)
    return obj

def makePathArray(baseobject,pathobject,count,xlate=None,align=False,pathobjsubs=[],useLink=False):
    """makePathArray(docobj,path,count,xlate,align,pathobjsubs,useLink): distribute
    count copies of a document baseobject along a pathobject or subobjects of a
    pathobject. Optionally translates each copy by FreeCAD.Vector xlate direction
    and distance to adjust for difference in shape centre vs shape reference point.
    Optionally aligns baseobject to tangent/normal/binormal of path."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if useLink:
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","PathArray",_PathArray(None),None,True)
    else:
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","PathArray")
        _PathArray(obj)
    obj.Base = baseobject
    obj.PathObj = pathobject
    if pathobjsubs:
        sl = []
        for sub in pathobjsubs:
            sl.append((obj.PathObj,sub))
        obj.PathSubs = list(sl)
    if count > 1:
        obj.Count = count
    if xlate:
        obj.Xlate = xlate
    obj.Align = align
    if gui:
        if useLink:
            _ViewProviderDraftLink(obj.ViewObject)
        else:
            _ViewProviderDraftArray(obj.ViewObject)
            formatObject(obj,obj.Base)
            if len(obj.Base.ViewObject.DiffuseColor) > 1:
                obj.ViewObject.Proxy.resetColors(obj.ViewObject)
        baseobject.ViewObject.hide()
        select(obj)
    return obj

def makePointArray(base, ptlst):
    """makePointArray(base,pointlist):"""
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","PointArray")
    _PointArray(obj, base, ptlst)
    obj.Base = base
    obj.PointList = ptlst
    if gui:
        _ViewProviderDraftArray(obj.ViewObject)
        base.ViewObject.hide()
        formatObject(obj,obj.Base)
        if len(obj.Base.ViewObject.DiffuseColor) > 1:
            obj.ViewObject.Proxy.resetColors(obj.ViewObject)
        select(obj)
    return obj


def extrude(obj,vector,solid=False):
    """makeExtrusion(object,vector): extrudes the given object
    in the direction given by the vector. The original object
    gets hidden."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    newobj = FreeCAD.ActiveDocument.addObject("Part::Extrusion","Extrusion")
    newobj.Base = obj
    newobj.Dir = vector
    newobj.Solid = solid
    if gui:
        obj.ViewObject.Visibility = False
        formatObject(newobj,obj)
        select(newobj)

    return newobj


def fuse(object1,object2):
    """fuse(oject1,object2): returns an object made from
    the union of the 2 given objects. If the objects are
    coplanar, a special Draft Wire is used, otherwise we use
    a standard Part fuse."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    import DraftGeomUtils, Part
    # testing if we have holes:
    holes = False
    fshape = object1.Shape.fuse(object2.Shape)
    fshape = fshape.removeSplitter()
    for f in fshape.Faces:
        if len(f.Wires) > 1:
            holes = True
    if DraftGeomUtils.isCoplanar(object1.Shape.fuse(object2.Shape).Faces) and not holes:
        obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","Fusion")
        _Wire(obj)
        if gui:
            _ViewProviderWire(obj.ViewObject)
        obj.Base = object1
        obj.Tool = object2
    elif holes:
        # temporary hack, since Part::Fuse objects don't remove splitters
        obj = FreeCAD.ActiveDocument.addObject("Part::Feature","Fusion")
        obj.Shape = fshape
    else:
        obj = FreeCAD.ActiveDocument.addObject("Part::Fuse","Fusion")
        obj.Base = object1
        obj.Tool = object2
    if gui:
        object1.ViewObject.Visibility = False
        object2.ViewObject.Visibility = False
        formatObject(obj,object1)
        select(obj)

    return obj

def cut(object1,object2):
    """cut(oject1,object2): returns a cut object made from
    the difference of the 2 given objects."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::Cut","Cut")
    obj.Base = object1
    obj.Tool = object2
    object1.ViewObject.Visibility = False
    object2.ViewObject.Visibility = False
    formatObject(obj,object1)
    select(obj)

    return obj


def isClosedEdge(edge_index, object):
    return edge_index + 1 >= len(object.Points)


def filterObjectsForModifiers(objects, isCopied=False):
    filteredObjects = []
    for object in objects:
        if hasattr(object, "MoveBase") and object.MoveBase and object.Base:
            parents = []
            for parent in object.Base.InList:
                if parent.isDerivedFrom("Part::Feature"):
                    parents.append(parent.Name)
            if len(parents) > 1:
                warningMessage = translate("draft","%s shares a base with %d other objects. Please check if you want to modify this.") % (object.Name,len(parents) - 1)
                FreeCAD.Console.PrintError(warningMessage)
                if FreeCAD.GuiUp:
                    FreeCADGui.getMainWindow().showMessage(warningMessage, 0)
            filteredObjects.append(object.Base)
        elif hasattr(object,"Placement") and object.getEditorMode("Placement") == ["ReadOnly"] and not isCopied:
           FreeCAD.Console.PrintError(translate("%s cannot be modified because its placement is readonly.") % obj.Name)
           continue
        else:
           filteredObjects.append(object)
    return filteredObjects


def getDXF(obj,direction=None):
    """getDXF(object,[direction]): returns a DXF entity from the given
    object. If direction is given, the object is projected in 2D."""
    plane = None
    result = ""
    if obj.isDerivedFrom("Drawing::View") or obj.isDerivedFrom("TechDraw::DrawView"):
        if obj.Source.isDerivedFrom("App::DocumentObjectGroup"):
            for o in obj.Source.Group:
                result += getDXF(o,obj.Direction)
        else:
            result += getDXF(obj.Source,obj.Direction)
        return result
    if direction:
        if isinstance(direction,FreeCAD.Vector):
            if direction != Vector(0,0,0):
                plane = WorkingPlane.plane()
                plane.alignToPointAndAxis(Vector(0,0,0),direction)

    def getProj(vec):
        if not plane: return vec
        nx = DraftVecUtils.project(vec,plane.u)
        ny = DraftVecUtils.project(vec,plane.v)
        return Vector(nx.Length,ny.Length,0)

    if getType(obj) == "Dimension":
        p1 = getProj(obj.Start)
        p2 = getProj(obj.End)
        p3 = getProj(obj.Dimline)
        result += "0\nDIMENSION\n8\n0\n62\n0\n3\nStandard\n70\n1\n"
        result += "10\n"+str(p3.x)+"\n20\n"+str(p3.y)+"\n30\n"+str(p3.z)+"\n"
        result += "13\n"+str(p1.x)+"\n23\n"+str(p1.y)+"\n33\n"+str(p1.z)+"\n"
        result += "14\n"+str(p2.x)+"\n24\n"+str(p2.y)+"\n34\n"+str(p2.z)+"\n"

    elif getType(obj) == "Annotation":
        p = getProj(obj.Position)
        count = 0
        for t in obj.LabeLtext:
            result += "0\nTEXT\n8\n0\n62\n0\n"
            result += "10\n"+str(p.x)+"\n20\n"+str(p.y+count)+"\n30\n"+str(p.z)+"\n"
            result += "40\n1\n"
            result += "1\n"+str(t)+"\n"
            result += "7\nSTANDARD\n"
            count += 1

    elif hasattr(obj,'Shape'):
        # TODO do this the Draft way, for ex. using polylines and rectangles
        import Drawing
        if not direction:
            direction = FreeCAD.Vector(0,0,-1)
        if DraftVecUtils.isNull(direction):
            direction = FreeCAD.Vector(0,0,-1)
        try:
            d = Drawing.projectToDXF(obj.Shape,direction)
        except:
            print("Draft.getDXF: Unable to project ",obj.Label," to ",direction)
        else:
            result += d

    else:
        print("Draft.getDXF: Unsupported object: ",obj.Label)

    return result


def getrgb(color,testbw=True):
    """getRGB(color,[testbw]): returns a rgb value #000000 from a freecad color
    if testwb = True (default), pure white will be converted into pure black"""
    r = str(hex(int(color[0]*255)))[2:].zfill(2)
    g = str(hex(int(color[1]*255)))[2:].zfill(2)
    b = str(hex(int(color[2]*255)))[2:].zfill(2)
    col = "#"+r+g+b
    if testbw:
        if col == "#ffffff":
            #print(getParam('SvgLinesBlack'))
            if getParam('SvgLinesBlack',True):
                col = "#000000"
    return col


import getSVG as svg


getSVG = svg.getSVG


def getCloneBase(obj,strict=False):
    """getCloneBase(obj,[strict]): returns the object cloned by this object, if
    any, or this object if it is no clone. If strict is True, if this object is
    not a clone, this function returns False"""
    if hasattr(obj,"CloneOf"):
        if obj.CloneOf:
            return getCloneBase(obj.CloneOf)
    if getType(obj) == "Clone":
        return obj.Objects[0]
    if strict:
        return False
    return obj


def getParameterFromV0(edge, offset):
    """return parameter at distance offset from edge.Vertexes[0]
    sb method in Part.TopoShapeEdge???"""

    lpt = edge.valueAt(edge.getParameterByLength(0))
    vpt = edge.Vertexes[0].Point

    if not DraftVecUtils.equals(vpt, lpt):
        # this edge is flipped
        length = edge.Length - offset
    else:
        # this edge is right way around
        length = offset

    return (edge.getParameterByLength(length))


#---------------------------------------------------------------------------
# Python Features definitions
#---------------------------------------------------------------------------





class _DrawingView(_DraftObject):
    """The Draft DrawingView object"""
    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"DrawingView")
        obj.addProperty("App::PropertyVector","Direction","Shape View",QT_TRANSLATE_NOOP("App::Property","Projection direction"))
        obj.addProperty("App::PropertyFloat","LineWidth","View Style",QT_TRANSLATE_NOOP("App::Property","The width of the lines inside this object"))
        obj.addProperty("App::PropertyLength","FontSize","View Style",QT_TRANSLATE_NOOP("App::Property","The size of the texts inside this object"))
        obj.addProperty("App::PropertyLength","LineSpacing","View Style",QT_TRANSLATE_NOOP("App::Property","The spacing between lines of text"))
        obj.addProperty("App::PropertyColor","LineColor","View Style",QT_TRANSLATE_NOOP("App::Property","The color of the projected objects"))
        obj.addProperty("App::PropertyLink","Source","Base",QT_TRANSLATE_NOOP("App::Property","The linked object"))
        obj.addProperty("App::PropertyEnumeration","FillStyle","View Style",QT_TRANSLATE_NOOP("App::Property","Shape Fill Style"))
        obj.addProperty("App::PropertyEnumeration","LineStyle","View Style",QT_TRANSLATE_NOOP("App::Property","Line Style"))
        obj.addProperty("App::PropertyBool","AlwaysOn","View Style",QT_TRANSLATE_NOOP("App::Property","If checked, source objects are displayed regardless of being visible in the 3D model"))
        obj.FillStyle = ['shape color'] + list(svgpatterns().keys())
        obj.LineStyle = ['Solid','Dashed','Dotted','Dashdot']
        obj.LineWidth = 0.35
        obj.FontSize = 12

    def execute(self, obj):
        result = ""
        if hasattr(obj,"Source"):
            if obj.Source:
                if hasattr(obj,"LineStyle"):
                    ls = obj.LineStyle
                else:
                    ls = None
                if hasattr(obj,"LineColor"):
                    lc = obj.LineColor
                else:
                    lc = None
                if hasattr(obj,"LineSpacing"):
                    lp = obj.LineSpacing
                else:
                    lp = None
                if obj.Source.isDerivedFrom("App::DocumentObjectGroup"):
                    svg = ""
                    shapes = []
                    others = []
                    objs = getGroupContents([obj.Source])
                    for o in objs:
                        v = o.ViewObject.isVisible()
                        if hasattr(obj,"AlwaysOn"):
                            if obj.AlwaysOn:
                                v = True
                        if v:
                            svg += getSVG(o,obj.Scale,obj.LineWidth,obj.FontSize.Value,obj.FillStyle,obj.Direction,ls,lc,lp)
                else:
                    svg = getSVG(obj.Source,obj.Scale,obj.LineWidth,obj.FontSize.Value,obj.FillStyle,obj.Direction,ls,lc,lp)
                result += '<g id="' + obj.Name + '"'
                result += ' transform="'
                result += 'rotate('+str(obj.Rotation)+','+str(obj.X)+','+str(obj.Y)+') '
                result += 'translate('+str(obj.X)+','+str(obj.Y)+') '
                result += 'scale('+str(obj.Scale)+','+str(-obj.Scale)+')'
                result += '">'
                result += svg
                result += '</g>'
        obj.ViewResult = result

    def getDXF(self,obj):
        "returns a DXF fragment"
        return getDXF(obj)

class _BSpline(_DraftObject):
    """The BSpline object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"BSpline")
        obj.addProperty("App::PropertyVectorList","Points","Draft", QT_TRANSLATE_NOOP("App::Property","The points of the B-spline"))
        obj.addProperty("App::PropertyBool","Closed","Draft",QT_TRANSLATE_NOOP("App::Property","If the B-spline is closed or not"))
        obj.addProperty("App::PropertyBool","MakeFace","Draft",QT_TRANSLATE_NOOP("App::Property","Create a face if this spline is closed"))
        obj.addProperty("App::PropertyArea","Area","Draft",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.MakeFace = getParam("fillmode",True)
        obj.Closed = False
        obj.Points = []
        self.assureProperties(obj)

    def assureProperties(self, obj): # for Compatibility with older versions
        if not hasattr(obj, "Parameterization"):
            obj.addProperty("App::PropertyFloat","Parameterization","Draft",QT_TRANSLATE_NOOP("App::Property","Parameterization factor"))
            obj.Parameterization = 1.0
            self.knotSeq = []

    def parameterization (self, pts, a, closed):
        # Computes a knot Sequence for a set of points
        # fac (0-1) : parameterization factor
        # fac=0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length
        if closed: # we need to add the first point as the end point
            pts.append(pts[0])
        params = [0]
        for i in range(1,len(pts)):
            p = pts[i].sub(pts[i-1])
            pl = pow(p.Length,a)
            params.append(params[-1] + pl)
        return params

    def onChanged(self, fp, prop):
        if prop == "Parameterization":
            if fp.Parameterization < 0.:
                fp.Parameterization = 0.
            if fp.Parameterization > 1.0:
                fp.Parameterization = 1.0

    def execute(self, obj):
        import Part
        self.assureProperties(obj)
        if obj.Points:
            self.knotSeq = self.parameterization(obj.Points, obj.Parameterization, obj.Closed)
            plm = obj.Placement
            if obj.Closed and (len(obj.Points) > 2):
                if obj.Points[0] == obj.Points[-1]:  # should not occur, but OCC will crash
                    FreeCAD.Console.PrintError(translate('draft',  "_BSpline.createGeometry: Closed with same first/last Point. Geometry not updated.")+"\n")
                    return
                spline = Part.BSplineCurve()
                spline.interpolate(obj.Points, PeriodicFlag = True, Parameters = self.knotSeq)
                # DNC: bug fix: convert to face if closed
                shape = Part.Wire(spline.toShape())
                # Creating a face from a closed spline cannot be expected to always work
                # Usually, if the spline is not flat the call of Part.Face() fails
                try:
                    if hasattr(obj,"MakeFace"):
                        if obj.MakeFace:
                            shape = Part.Face(shape)
                    else:
                        shape = Part.Face(shape)
                except Part.OCCError:
                    pass
                obj.Shape = shape
                if hasattr(obj,"Area") and hasattr(shape,"Area"):
                    obj.Area = shape.Area
            else:
                spline = Part.BSplineCurve()
                spline.interpolate(obj.Points, PeriodicFlag = False, Parameters = self.knotSeq)
                shape = spline.toShape()
                obj.Shape = shape
                if hasattr(obj,"Area") and hasattr(shape,"Area"):
                    obj.Area = shape.Area
            obj.Placement = plm
        obj.positionBySupport()

# for compatibility with older versions
_ViewProviderBSpline = _ViewProviderWire

class _BezCurve(_DraftObject):
    """The BezCurve object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"BezCurve")
        obj.addProperty("App::PropertyVectorList","Points","Draft",QT_TRANSLATE_NOOP("App::Property","The points of the Bezier curve"))
        obj.addProperty("App::PropertyInteger","Degree","Draft",QT_TRANSLATE_NOOP("App::Property","The degree of the Bezier function"))
        obj.addProperty("App::PropertyIntegerList","Continuity","Draft",QT_TRANSLATE_NOOP("App::Property","Continuity"))
        obj.addProperty("App::PropertyBool","Closed","Draft",QT_TRANSLATE_NOOP("App::Property","If the Bezier curve should be closed or not"))
        obj.addProperty("App::PropertyBool","MakeFace","Draft",QT_TRANSLATE_NOOP("App::Property","Create a face if this curve is closed"))
        obj.addProperty("App::PropertyLength","Length","Draft",QT_TRANSLATE_NOOP("App::Property","The length of this object"))
        obj.addProperty("App::PropertyArea","Area","Draft",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.MakeFace = getParam("fillmode",True)
        obj.Closed = False
        obj.Degree = 3
        obj.Continuity = []
        #obj.setEditorMode("Degree",2)#hide
        obj.setEditorMode("Continuity",1)#ro

    def execute(self, fp):
        self.createGeometry(fp)
        fp.positionBySupport()

    def _segpoleslst(self,fp):
        """split the points into segments"""
        if not fp.Closed and len(fp.Points) >= 2: #allow lower degree segment
            poles=fp.Points[1:]
        elif fp.Closed and len(fp.Points) >= fp.Degree: #drawable
            #poles=fp.Points[1:(fp.Degree*(len(fp.Points)//fp.Degree))]+fp.Points[0:1]
            poles=fp.Points[1:]+fp.Points[0:1]
        else:
            poles=[]
        return [poles[x:x+fp.Degree] for x in \
            range(0, len(poles), (fp.Degree or 1))]

    def resetcontinuity(self,fp):
        fp.Continuity = [0]*(len(self._segpoleslst(fp))-1+1*fp.Closed)
        #nump= len(fp.Points)-1+fp.Closed*1
        #numsegments = (nump // fp.Degree) + 1 * (nump % fp.Degree > 0) -1
        #fp.Continuity = [0]*numsegments

    def onChanged(self, fp, prop):
        if prop == 'Closed': # if remove the last entry when curve gets opened
            oldlen = len(fp.Continuity)
            newlen = (len(self._segpoleslst(fp))-1+1*fp.Closed)
            if oldlen > newlen:
                fp.Continuity = fp.Continuity[:newlen]
            if oldlen < newlen:
                fp.Continuity = fp.Continuity + [0]*(newlen-oldlen)
        if hasattr(fp,'Closed') and fp.Closed and prop in  ['Points','Degree','Closed'] and\
                len(fp.Points) % fp.Degree: # the curve editing tools can't handle extra points
            fp.Points=fp.Points[:(fp.Degree*(len(fp.Points)//fp.Degree))] #for closed curves
        if prop in ["Degree"] and fp.Degree >= 1: #reset Continuity
            self.resetcontinuity(fp)
        if prop in ["Points","Degree","Continuity","Closed"]:
            self.createGeometry(fp)

    def createGeometry(self,fp):
        import Part
        plm = fp.Placement
        if fp.Points:
            startpoint=fp.Points[0]
            edges = []
            for segpoles in self._segpoleslst(fp):
#                if len(segpoles) == fp.Degree # would skip additional poles
                 c = Part.BezierCurve() #last segment may have lower degree
                 c.increase(len(segpoles))
                 c.setPoles([startpoint]+segpoles)
                 edges.append(Part.Edge(c))
                 startpoint = segpoles[-1]
            w = Part.Wire(edges)
            if fp.Closed and w.isClosed():
                try:
                    if hasattr(fp,"MakeFace"):
                        if fp.MakeFace:
                            w = Part.Face(w)
                    else:
                        w = Part.Face(w)
                except Part.OCCError:
                    pass
            fp.Shape = w
            if hasattr(fp,"Area") and hasattr(w,"Area"):
                fp.Area = w.Area
            if hasattr(fp,"Length") and hasattr(w,"Length"):
                fp.Length = w.Length            
        fp.Placement = plm

    @classmethod
    def symmetricpoles(cls,knot, p1, p2):
        """make two poles symmetric respective to the knot"""
        p1h=FreeCAD.Vector(p1)
        p2h=FreeCAD.Vector(p2)
        p1h.multiply(0.5)
        p2h.multiply(0.5)
        return ( knot+p1h-p2h , knot+p2h-p1h)

    @classmethod
    def tangentpoles(cls,knot, p1, p2,allowsameside=False):
        """make two poles have the same tangent at knot"""
        p12n=p2.sub(p1)
        p12n.normalize()
        p1k=knot-p1
        p2k=knot-p2
        p1k_= FreeCAD.Vector(p12n)
        kon12=(p1k*p12n)
        if allowsameside or not (kon12 < 0 or p2k*p12n > 0):# instead of moving
            p1k_.multiply(kon12)
            pk_k=knot-p1-p1k_
            return (p1+pk_k,p2+pk_k)
        else:
            return cls.symmetricpoles(knot, p1, p2)

    @staticmethod
    def modifysymmetricpole(knot,p1):
        """calculate the coordinates of the opposite pole
        of a symmetric knot"""
        return knot+knot-p1

    @staticmethod
    def modifytangentpole(knot,p1,oldp2):
        """calculate the coordinates of the opposite pole
        of a tangent knot"""
        pn=knot-p1
        pn.normalize()
        pn.multiply((knot-oldp2).Length)
        return pn+knot

# for compatibility with older versions ???????
_ViewProviderBezCurve = _ViewProviderWire

class _Block(_DraftObject):
    """The Block object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"Block")
        obj.addProperty("App::PropertyLinkList","Components","Draft",QT_TRANSLATE_NOOP("App::Property","The components of this block"))

    def execute(self, obj):
        import Part
        plm = obj.Placement
        shps = []
        for c in obj.Components:
            shps.append(c.Shape)
        if shps:
            shape = Part.makeCompound(shps)
            obj.Shape = shape
        obj.Placement = plm
        obj.positionBySupport()

class _Shape2DView(_DraftObject):
    """The Shape2DView object"""

    def __init__(self,obj):
        obj.addProperty("App::PropertyLink","Base","Draft",QT_TRANSLATE_NOOP("App::Property","The base object this 2D view must represent"))
        obj.addProperty("App::PropertyVector","Projection","Draft",QT_TRANSLATE_NOOP("App::Property","The projection vector of this object"))
        obj.addProperty("App::PropertyEnumeration","ProjectionMode","Draft",QT_TRANSLATE_NOOP("App::Property","The way the viewed object must be projected"))
        obj.addProperty("App::PropertyIntegerList","FaceNumbers","Draft",QT_TRANSLATE_NOOP("App::Property","The indices of the faces to be projected in Individual Faces mode"))
        obj.addProperty("App::PropertyBool","HiddenLines","Draft",QT_TRANSLATE_NOOP("App::Property","Show hidden lines"))
        obj.addProperty("App::PropertyBool","FuseArch","Draft",QT_TRANSLATE_NOOP("App::Property","Fuse wall and structure objects of same type and material"))
        obj.addProperty("App::PropertyBool","Tessellation","Draft",QT_TRANSLATE_NOOP("App::Property","Tessellate Ellipses and B-splines into line segments"))
        obj.addProperty("App::PropertyBool","InPlace","Draft",QT_TRANSLATE_NOOP("App::Property","For Cutlines and Cutfaces modes, this leaves the faces at the cut location"))
        obj.addProperty("App::PropertyFloat","SegmentLength","Draft",QT_TRANSLATE_NOOP("App::Property","Length of line segments if tessellating Ellipses or B-splines into line segments"))
        obj.addProperty("App::PropertyBool","VisibleOnly","Draft",QT_TRANSLATE_NOOP("App::Property","If this is True, this object will be recomputed only if it is visible"))
        obj.Projection = Vector(0,0,1)
        obj.ProjectionMode = ["Solid","Individual Faces","Cutlines","Cutfaces"]
        obj.HiddenLines = False
        obj.Tessellation = False
        obj.VisibleOnly = False
        obj.InPlace = True
        obj.SegmentLength = .05
        _DraftObject.__init__(self,obj,"Shape2DView")

    def getProjected(self,obj,shape,direction):
        "returns projected edges from a shape and a direction"
        import Part,Drawing,DraftGeomUtils
        edges = []
        groups = Drawing.projectEx(shape,direction)
        for g in groups[0:5]:
            if g:
                edges.append(g)
        if hasattr(obj,"HiddenLines"):
            if obj.HiddenLines:
                for g in groups[5:]:
                    edges.append(g)
        #return Part.makeCompound(edges)
        if hasattr(obj,"Tessellation") and obj.Tessellation:
            return DraftGeomUtils.cleanProjection(Part.makeCompound(edges),obj.Tessellation,obj.SegmentLength)
        else:
            return Part.makeCompound(edges)
            #return DraftGeomUtils.cleanProjection(Part.makeCompound(edges))

    def execute(self,obj):
        if hasattr(obj,"VisibleOnly"):
            if obj.VisibleOnly:
                if obj.ViewObject:
                    if obj.ViewObject.Visibility == False:
                        return False
        import Part, DraftGeomUtils
        obj.positionBySupport()
        pl = obj.Placement
        if obj.Base:
            if getType(obj.Base) in ["BuildingPart","SectionPlane"]:
                objs = []
                if getType(obj.Base) == "SectionPlane":
                    objs = obj.Base.Objects
                    cutplane = obj.Base.Shape
                else:
                    objs = obj.Base.Group
                    cutplane = Part.makePlane(1000,1000,FreeCAD.Vector(-500,-500,0))
                    m = 1
                    if obj.Base.ViewObject and hasattr(obj.Base.ViewObject,"CutMargin"):
                        m = obj.Base.ViewObject.CutMargin.Value
                    cutplane.translate(FreeCAD.Vector(0,0,m))
                    cutplane.Placement = cutplane.Placement.multiply(obj.Base.Placement)
                if objs:
                    onlysolids = True
                    if hasattr(obj.Base,"OnlySolids"):
                        onlysolids = obj.Base.OnlySolids
                    import Arch, Part, Drawing
                    objs = getGroupContents(objs,walls=True)
                    objs = removeHidden(objs)
                    shapes = []
                    if hasattr(obj,"FuseArch") and obj.FuseArch:
                        shtypes = {}
                        for o in objs:
                            if getType(o) in ["Wall","Structure"]:
                                if onlysolids:
                                    shtypes.setdefault(o.Material.Name if (hasattr(o,"Material") and o.Material) else "None",[]).extend(o.Shape.Solids)
                                else:
                                    shtypes.setdefault(o.Material.Name if (hasattr(o,"Material") and o.Material) else "None",[]).append(o.Shape.copy())
                            elif o.isDerivedFrom("Part::Feature"):
                                if onlysolids:
                                    shapes.extend(o.Shape.Solids)
                                else:
                                    shapes.append(o.Shape.copy())
                        for k,v in shtypes.items():
                            v1 = v.pop()
                            if v:
                                v1 = v1.multiFuse(v)
                                v1 = v1.removeSplitter()
                            if v1.Solids:
                                shapes.extend(v1.Solids)
                            else:
                                print("Shape2DView: Fusing Arch objects produced non-solid results")
                                shapes.append(v1)
                    else:
                        for o in objs:
                            if o.isDerivedFrom("Part::Feature"):
                                if onlysolids:
                                    shapes.extend(o.Shape.Solids)
                                else:
                                    shapes.append(o.Shape.copy())
                    clip = False
                    if hasattr(obj.Base,"Clip"):
                        clip = obj.Base.Clip
                    cutp,cutv,iv = Arch.getCutVolume(cutplane,shapes,clip)
                    cuts = []
                    opl = FreeCAD.Placement(obj.Base.Placement)
                    proj = opl.Rotation.multVec(FreeCAD.Vector(0,0,1))
                    if obj.ProjectionMode == "Solid":
                        for sh in shapes:
                            if cutv:
                                if sh.Volume < 0:
                                    sh.reverse()
                                #if cutv.BoundBox.intersect(sh.BoundBox):
                                #    c = sh.cut(cutv)
                                #else:
                                #    c = sh.copy()
                                c = sh.cut(cutv)
                                if onlysolids:
                                    cuts.extend(c.Solids)
                                else:
                                    cuts.append(c)
                            else:
                                if onlysolids:
                                    cuts.extend(sh.Solids)
                                else:
                                    cuts.append(sh.copy())
                        comp = Part.makeCompound(cuts)
                        obj.Shape = self.getProjected(obj,comp,proj)
                    elif obj.ProjectionMode in ["Cutlines","Cutfaces"]:
                        for sh in shapes:
                            if sh.Volume < 0:
                                sh.reverse()
                            c = sh.section(cutp)
                            faces = []
                            if (obj.ProjectionMode == "Cutfaces") and (sh.ShapeType == "Solid"):
                                if hasattr(obj,"InPlace"):
                                    if not obj.InPlace:
                                        c = self.getProjected(obj,c,proj)
                                wires = DraftGeomUtils.findWires(c.Edges)
                                for w in wires:
                                    if w.isClosed():
                                        faces.append(Part.Face(w))
                            if faces:
                                cuts.extend(faces)
                            else:
                                cuts.append(c)
                        comp = Part.makeCompound(cuts)
                        opl = FreeCAD.Placement(obj.Base.Placement)
                        comp.Placement = opl.inverse()
                        if comp:
                            obj.Shape = comp

            elif obj.Base.isDerivedFrom("App::DocumentObjectGroup"):
                shapes = []
                objs = getGroupContents(obj.Base)
                for o in objs:
                    if o.isDerivedFrom("Part::Feature"):
                        if o.Shape:
                            if not o.Shape.isNull():
                                shapes.append(o.Shape)
                if shapes:
                    import Part
                    comp = Part.makeCompound(shapes)
                    obj.Shape = self.getProjected(obj,comp,obj.Projection)

            elif obj.Base.isDerivedFrom("Part::Feature"):
                if not DraftVecUtils.isNull(obj.Projection):
                    if obj.ProjectionMode == "Solid":
                        obj.Shape = self.getProjected(obj,obj.Base.Shape,obj.Projection)
                    elif obj.ProjectionMode == "Individual Faces":
                        import Part
                        if obj.FaceNumbers:
                            faces = []
                            for i in obj.FaceNumbers:
                                if len(obj.Base.Shape.Faces) > i:
                                    faces.append(obj.Base.Shape.Faces[i])
                            views = []
                            for f in faces:
                                views.append(self.getProjected(obj,f,obj.Projection))
                            if views:
                                obj.Shape = Part.makeCompound(views)
                    else:
                        FreeCAD.Console.PrintWarning(obj.ProjectionMode+" mode not implemented\n")
        if not DraftGeomUtils.isNull(pl):
            obj.Placement = pl



class _Array(_DraftLink):
    "The Draft Array object"

    def __init__(self,obj):
        _DraftLink.__init__(self,obj,"Array")

    def attach(self, obj):
        obj.addProperty("App::PropertyLink","Base","Draft",QT_TRANSLATE_NOOP("App::Property","The base object that must be duplicated"))
        obj.addProperty("App::PropertyEnumeration","ArrayType","Draft",QT_TRANSLATE_NOOP("App::Property","The type of array to create"))
        obj.addProperty("App::PropertyVector","Axis","Draft",QT_TRANSLATE_NOOP("App::Property","The axis direction"))
        obj.addProperty("App::PropertyInteger","NumberX","Draft",QT_TRANSLATE_NOOP("App::Property","Number of copies in X direction"))
        obj.addProperty("App::PropertyInteger","NumberY","Draft",QT_TRANSLATE_NOOP("App::Property","Number of copies in Y direction"))
        obj.addProperty("App::PropertyInteger","NumberZ","Draft",QT_TRANSLATE_NOOP("App::Property","Number of copies in Z direction"))
        obj.addProperty("App::PropertyInteger","NumberPolar","Draft",QT_TRANSLATE_NOOP("App::Property","Number of copies"))
        obj.addProperty("App::PropertyVectorDistance","IntervalX","Draft",QT_TRANSLATE_NOOP("App::Property","Distance and orientation of intervals in X direction"))
        obj.addProperty("App::PropertyVectorDistance","IntervalY","Draft",QT_TRANSLATE_NOOP("App::Property","Distance and orientation of intervals in Y direction"))
        obj.addProperty("App::PropertyVectorDistance","IntervalZ","Draft",QT_TRANSLATE_NOOP("App::Property","Distance and orientation of intervals in Z direction"))
        obj.addProperty("App::PropertyVectorDistance","IntervalAxis","Draft",QT_TRANSLATE_NOOP("App::Property","Distance and orientation of intervals in Axis direction"))
        obj.addProperty("App::PropertyVectorDistance","Center","Draft",QT_TRANSLATE_NOOP("App::Property","Center point"))
        obj.addProperty("App::PropertyAngle","Angle","Draft",QT_TRANSLATE_NOOP("App::Property","Angle to cover with copies"))
        obj.addProperty("App::PropertyDistance","RadialDistance","Draft",QT_TRANSLATE_NOOP("App::Property","Distance between copies in a circle"))
        obj.addProperty("App::PropertyDistance","TangentialDistance","Draft",QT_TRANSLATE_NOOP("App::Property","Distance between circles"))
        obj.addProperty("App::PropertyInteger","NumberCircles","Draft",QT_TRANSLATE_NOOP("App::Property","number of circles"))
        obj.addProperty("App::PropertyInteger","Symmetry","Draft",QT_TRANSLATE_NOOP("App::Property","number of circles"))
        obj.addProperty("App::PropertyBool","Fuse","Draft",QT_TRANSLATE_NOOP("App::Property","Specifies if copies must be fused (slower)"))
        obj.Fuse = False
        if self.useLink:
            obj.addProperty("App::PropertyInteger","Count","Draft",'')
            obj.addProperty("App::PropertyBool","ExpandArray","Draft",
                    QT_TRANSLATE_NOOP("App::Property","Show array element as children object"))
            obj.ExpandArray = False

        obj.ArrayType = ['ortho','polar','circular']
        obj.NumberX = 1
        obj.NumberY = 1
        obj.NumberZ = 1
        obj.NumberPolar = 1
        obj.IntervalX = Vector(1,0,0)
        obj.IntervalY = Vector(0,1,0)
        obj.IntervalZ = Vector(0,0,1)
        obj.Angle = 360
        obj.Axis = Vector(0,0,1)
        obj.RadialDistance = 1.0
        obj.TangentialDistance = 1.0
        obj.NumberCircles = 2
        obj.Symmetry = 1

        _DraftLink.attach(self,obj)

    def linkSetup(self,obj):
        _DraftLink.linkSetup(self,obj)
        obj.configLinkProperty(ElementCount='Count')
        obj.setPropertyStatus('Count','Hidden')

    def execute(self,obj):
        if obj.Base:
            pl = obj.Placement
            if obj.ArrayType == "ortho":
                pls = self.rectArray(obj.Base.Placement,obj.IntervalX,obj.IntervalY,
                                    obj.IntervalZ,obj.NumberX,obj.NumberY,obj.NumberZ)
            elif obj.ArrayType == "circular":
                pls = self.circArray(obj.Base.Placement,obj.RadialDistance,obj.TangentialDistance,
                                     obj.Axis,obj.Center,obj.NumberCircles,obj.Symmetry)
            else:
                av = obj.IntervalAxis if hasattr(obj,"IntervalAxis") else None
                pls = self.polarArray(obj.Base.Placement,obj.Center,obj.Angle.Value,obj.NumberPolar,obj.Axis,av)

            return _DraftLink.buildShape(self,obj,pl,pls)

    def rectArray(self,pl,xvector,yvector,zvector,xnum,ynum,znum):
        import Part
        base = [pl.copy()]
        for xcount in range(xnum):
            currentxvector=Vector(xvector).multiply(xcount)
            if not xcount==0:
                npl = pl.copy()
                npl.translate(currentxvector)
                base.append(npl)
            for ycount in range(ynum):
                currentyvector=FreeCAD.Vector(currentxvector)
                currentyvector=currentyvector.add(Vector(yvector).multiply(ycount))
                if not ycount==0:
                    npl = pl.copy()
                    npl.translate(currentyvector)
                    base.append(npl)
                for zcount in range(znum):
                    currentzvector=FreeCAD.Vector(currentyvector)
                    currentzvector=currentzvector.add(Vector(zvector).multiply(zcount))
                    if not zcount==0:
                        npl = pl.copy()
                        npl.translate(currentzvector)
                        base.append(npl)
        return base

    def circArray(self,pl,rdist,tdist,axis,center,cnum,sym):
        import Part
        sym = max(1, sym)
        lead = (0,1,0)
        if axis.x == 0 and axis.z == 0: lead = (1,0,0)
        direction = axis.cross(Vector(lead)).normalize()
        base = [pl.copy()]
        for xcount in range(1, cnum):
            rc = xcount*rdist
            c = 2*rc*math.pi
            n = math.floor(c/tdist)
            n = math.floor(n/sym)*sym
            if n == 0: continue
            angle = 360/n
            for ycount in range(0, n):
                npl = pl.copy()
                trans = FreeCAD.Vector(direction).multiply(rc)
                npl.translate(trans)
                npl.rotate(npl.Rotation.inverted().multVec(center-trans), axis, ycount*angle)
                base.append(npl)
        return base

    def polarArray(self,pl,center,angle,num,axis,axisvector):
        #print("angle ",angle," num ",num)
        import Part
        base = [pl.copy()]
        if angle == 360:
            fraction = float(angle)/num
        else:
            if num == 0:
                return base
            fraction = float(angle)/(num-1)
        for i in range(num-1):
            currangle = fraction + (i*fraction)
            npl = pl.copy()
            npl.rotate(DraftVecUtils.tup(center), DraftVecUtils.tup(axis), currangle)
            if axisvector:
                if not DraftVecUtils.isNull(axisvector):
                    npl.translate(FreeCAD.Vector(axisvector).multiply(i+1))
            base.append(npl)
        return base

class _PathArray(_DraftLink):
    """The Draft Path Array object"""

    def __init__(self,obj):
        _DraftLink.__init__(self,obj,"PathArray")

    def attach(self,obj):
        obj.addProperty("App::PropertyLinkGlobal","Base","Draft",QT_TRANSLATE_NOOP("App::Property","The base object that must be duplicated"))
        obj.addProperty("App::PropertyLinkGlobal","PathObj","Draft",QT_TRANSLATE_NOOP("App::Property","The path object along which to distribute objects"))
        obj.addProperty("App::PropertyLinkSubListGlobal","PathSubs",QT_TRANSLATE_NOOP("App::Property","Selected subobjects (edges) of PathObj"))
        obj.addProperty("App::PropertyInteger","Count","Draft",QT_TRANSLATE_NOOP("App::Property","Number of copies"))
        obj.addProperty("App::PropertyVectorDistance","Xlate","Draft",QT_TRANSLATE_NOOP("App::Property","Optional translation vector"))
        obj.addProperty("App::PropertyBool","Align","Draft",QT_TRANSLATE_NOOP("App::Property","Orientation of Base along path"))
        obj.Count = 2
        obj.PathSubs = []
        obj.Xlate = FreeCAD.Vector(0,0,0)
        obj.Align = False

        if self.useLink:
            obj.addProperty("App::PropertyBool","ExpandArray","Draft",
                    QT_TRANSLATE_NOOP("App::Property","Show array element as children object"))
            obj.ExpandArray = False

        _DraftLink.attach(self,obj)

    def linkSetup(self,obj):
        _DraftLink.linkSetup(self,obj)
        obj.configLinkProperty(ElementCount='Count')

    def execute(self,obj):
        import FreeCAD
        import Part
        import DraftGeomUtils
        if obj.Base and obj.PathObj:
            pl = obj.Placement
            if obj.PathSubs:
                w = self.getWireFromSubs(obj)
            elif (hasattr(obj.PathObj.Shape,'Wires') and obj.PathObj.Shape.Wires):
                w = obj.PathObj.Shape.Wires[0]
            elif obj.PathObj.Shape.Edges:
                w = Part.Wire(obj.PathObj.Shape.Edges)
            else:
                FreeCAD.Console.PrintLog ("_PathArray.createGeometry: path " + obj.PathObj.Name + " has no edges\n")
                return
            base = calculatePlacementsOnPath(
                    obj.Base.Shape.Placement.Rotation,w,obj.Count,obj.Xlate,obj.Align)
            return _DraftLink.buildShape(self,obj,pl,base)

    def getWireFromSubs(self,obj):
        '''Make a wire from PathObj subelements'''
        import Part
        sl = []
        for sub in obj.PathSubs:
            edgeNames = sub[1]
            for n in edgeNames:
                e = sub[0].Shape.getElement(n)
                sl.append(e)
        return Part.Wire(sl)

    def pathArray(self,shape,pathwire,count,xlate,align):
        '''Distribute shapes along a path.'''
        import Part

        placements = calculatePlacementsOnPath(
            shape.Placement.Rotation, pathwire, count, xlate, align)

        base = []

        for placement in placements:
            ns = shape.copy()
            ns.Placement = placement

            base.append(ns)

        return (Part.makeCompound(base))

def convertDraftTexts(textslist=[]):
    """converts the given Draft texts (or all that are found in the active document) to the new object"""
    if not isinstance(textslist,list):
        textslist = [textslist]
    if not textslist:
        for o in FreeCAD.ActiveDocument.Objects:
            if o.TypeId == "App::Annotation":
                textslist.append(o)
    todelete = []
    for o in textslist:
        l = o.Label
        o.Label = l+".old"
        obj = makeText(o.LabelText,point=o.Position)
        obj.Label = l
        todelete.append(o.Name)
        for p in o.InList:
            if p.isDerivedFrom("App::DocumentObjectGroup"):
                if o in p.Group:
                    g = p.Group
                    g.append(obj)
                    p.Group = g
    for n in todelete:
        FreeCAD.ActiveDocument.removeObject(n)

## @}
