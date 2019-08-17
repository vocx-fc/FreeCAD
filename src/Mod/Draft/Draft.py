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


def makeCopy(obj,force=None,reparent=False):
    """makeCopy(object): returns an exact copy of an object"""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if (getType(obj) == "Rectangle") or (force == "Rectangle"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _Rectangle(newobj)
        if gui:
            _ViewProviderRectangle(newobj.ViewObject)
    elif (getType(obj) == "Point") or (force == "Point"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _Point(newobj)
        if gui:
            _ViewProviderPoint(newobj.ViewObject)
    elif (getType(obj) == "Dimension") or (force == "Dimension"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _Dimension(newobj)
        if gui:
            _ViewProviderDimension(newobj.ViewObject)
    elif (getType(obj) == "Wire") or (force == "Wire"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _Wire(newobj)
        if gui:
            _ViewProviderWire(newobj.ViewObject)
    elif (getType(obj) == "Circle") or (force == "Circle"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _Circle(newobj)
        if gui:
            _ViewProviderDraft(newobj.ViewObject)
    elif (getType(obj) == "Polygon") or (force == "Polygon"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _Polygon(newobj)
        if gui:
            _ViewProviderDraft(newobj.ViewObject)
    elif (getType(obj) == "BSpline") or (force == "BSpline"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _BSpline(newobj)
        if gui:
            _ViewProviderWire(newobj.ViewObject)
    elif (getType(obj) == "Block") or (force == "BSpline"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _Block(newobj)
        if gui:
            _ViewProviderDraftPart(newobj.ViewObject)
    elif (getType(obj) == "DrawingView") or (force == "DrawingView"):
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        _DrawingView(newobj)
    elif (getType(obj) == "Structure") or (force == "Structure"):
        import ArchStructure
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        ArchStructure._Structure(newobj)
        if gui:
            ArchStructure._ViewProviderStructure(newobj.ViewObject)
    elif (getType(obj) == "Wall") or (force == "Wall"):
        import ArchWall
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        ArchWall._Wall(newobj)
        if gui:
            ArchWall._ViewProviderWall(newobj.ViewObject)
    elif (getType(obj) == "Window") or (force == "Window"):
        import ArchWindow
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        ArchWindow._Window(newobj)
        if gui:
            ArchWindow._ViewProviderWindow(newobj.ViewObject)
    elif (getType(obj) == "Panel") or (force == "Panel"):
        import ArchPanel
        newobj = FreeCAD.ActiveDocument.addObject(obj.TypeId,getRealName(obj.Name))
        ArchPanel._Panel(newobj)
        if gui:
            ArchPanel._ViewProviderPanel(newobj.ViewObject)
    elif (getType(obj) == "Sketch") or (force == "Sketch"):
        newobj = FreeCAD.ActiveDocument.addObject("Sketcher::SketchObject",getRealName(obj.Name))
        for geo in obj.Geometry:
            newobj.addGeometry(geo)
        for con in obj.Constraints:
            newobj.addConstraint(con)
    elif hasattr(obj, 'Shape'):
        newobj = FreeCAD.ActiveDocument.addObject("Part::Feature",getRealName(obj.Name))
        newobj.Shape = obj.Shape
    else:
        print("Error: Object type cannot be copied")
        return None
    for p in obj.PropertiesList:
        if not p in ["Proxy","ExpressionEngine"]:
            if p in newobj.PropertiesList:
                if not "ReadOnly" in newobj.getEditorMode(p):
                    try:
                        setattr(newobj,p,obj.getPropertyByName(p))
                    except AttributeError:
                        try:
                            setattr(newobj,p,obj.getPropertyByName(p).Value)
                        except AttributeError:
                            pass
    if reparent:
        parents = obj.InList
        if parents:
            for par in parents:
                if par.isDerivedFrom("App::DocumentObjectGroup"):
                    par.addObject(newobj)
                else:
                    for prop in par.PropertiesList:
                        if getattr(par,prop) == obj:
                            setattr(par,prop,newobj)

    formatObject(newobj,obj)
    return newobj


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

def joinWires(wires, joinAttempts = 0):
    """joinWires(objects): merges a set of wires where possible, if any of those
    wires have a coincident start and end point"""
    if joinAttempts > len(wires):
        return
    joinAttempts += 1
    for wire1Index, wire1 in enumerate(wires):
        for wire2Index, wire2 in enumerate(wires):
            if wire2Index <= wire1Index:
                continue
            if joinTwoWires(wire1, wire2):
                wires.pop(wire2Index)
                break
    joinWires(wires, joinAttempts)

def joinTwoWires(wire1, wire2):
    """joinTwoWires(object, object): joins two wires if they share a common
    point as a start or an end"""
    wire1AbsPoints = [wire1.Placement.multVec(point) for point in wire1.Points]
    wire2AbsPoints = [wire2.Placement.multVec(point) for point in wire2.Points]
    if (wire1AbsPoints[0] == wire2AbsPoints[-1] and wire1AbsPoints[-1] == wire2AbsPoints[0]) \
        or (wire1AbsPoints[0] == wire2AbsPoints[0] and wire1AbsPoints[-1] == wire2AbsPoints[-1]):
        wire2AbsPoints.pop()
        wire1.Closed = True
    elif wire1AbsPoints[0] == wire2AbsPoints[0]:
        wire1AbsPoints = list(reversed(wire1AbsPoints))
    elif wire1AbsPoints[0] == wire2AbsPoints[-1]:
        wire1AbsPoints = list(reversed(wire1AbsPoints))
        wire2AbsPoints = list(reversed(wire2AbsPoints))
    elif wire1AbsPoints[-1] == wire2AbsPoints[-1]:
        wire2AbsPoints = list(reversed(wire2AbsPoints))
    elif wire1AbsPoints[-1] == wire2AbsPoints[0]:
        pass
    else:
        return False
    wire2AbsPoints.pop(0)
    wire1.Points = [wire1.Placement.inverse().multVec(point) for point in wire1AbsPoints] + [wire1.Placement.inverse().multVec(point) for point in wire2AbsPoints]
    FreeCAD.ActiveDocument.removeObject(wire2.Name)
    return True

def split(wire, newPoint, edgeIndex):
    if getType(wire) != "Wire":
        return
    elif wire.Closed:
        splitClosedWire(wire, edgeIndex)
    else:
        splitOpenWire(wire, newPoint, edgeIndex)

def splitClosedWire(wire, edgeIndex):
    wire.Closed = False
    if edgeIndex == len(wire.Points):
        makeWire([wire.Placement.multVec(wire.Points[0]),
            wire.Placement.multVec(wire.Points[-1])], placement=wire.Placement)
    else:
        makeWire([wire.Placement.multVec(wire.Points[edgeIndex-1]),
            wire.Placement.multVec(wire.Points[edgeIndex])], placement=wire.Placement)
        wire.Points = list(reversed(wire.Points[0:edgeIndex])) + list(reversed(wire.Points[edgeIndex:]))

def splitOpenWire(wire, newPoint, edgeIndex):
    wire1Points = []
    wire2Points = []
    for index, point in enumerate(wire.Points):
        if index == edgeIndex:
            wire1Points.append(wire.Placement.inverse().multVec(newPoint))
            wire2Points.append(newPoint)
            wire2Points.append(wire.Placement.multVec(point))
        elif index < edgeIndex:
            wire1Points.append(point)
        elif index > edgeIndex:
            wire2Points.append(wire.Placement.multVec(point))
    wire.Points = wire1Points
    makeWire(wire2Points, placement=wire.Placement)

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

def moveVertex(object, vertex_index, vector):
    points = object.Points
    points[vertex_index] = points[vertex_index].add(vector)
    object.Points = points

def moveEdge(object, edge_index, vector):
    moveVertex(object, edge_index, vector)
    if isClosedEdge(edge_index, object):
        moveVertex(object, 0, vector)
    else:
        moveVertex(object, edge_index+1, vector)

def copyMovedEdges(arguments):
    copied_edges = []
    for argument in arguments:
        copied_edges.append(copyMovedEdge(argument[0], argument[1], argument[2]))
    joinWires(copied_edges)

def copyMovedEdge(object, edge_index, vector):
    vertex1 = object.Placement.multVec(object.Points[edge_index]).add(vector)
    if isClosedEdge(edge_index, object):
        vertex2 = object.Placement.multVec(object.Points[0]).add(vector)
    else:
        vertex2 = object.Placement.multVec(object.Points[edge_index+1]).add(vector)
    return makeLine(vertex1, vertex2)

def copyRotatedEdges(arguments):
    copied_edges = []
    for argument in arguments:
        copied_edges.append(copyRotatedEdge(argument[0], argument[1],
            argument[2], argument[3], argument[4]))
    joinWires(copied_edges)

def copyRotatedEdge(object, edge_index, angle, center, axis):
    vertex1 = rotateVectorFromCenter(
        object.Placement.multVec(object.Points[edge_index]),
        angle, axis, center)
    if isClosedEdge(edge_index, object):
        vertex2 = rotateVectorFromCenter(
            object.Placement.multVec(object.Points[0]),
            angle, axis, center)
    else:
        vertex2 = rotateVectorFromCenter(
            object.Placement.multVec(object.Points[edge_index+1]),
            angle, axis, center)
    return makeLine(vertex1, vertex2)

def isClosedEdge(edge_index, object):
    return edge_index + 1 >= len(object.Points)

def move(objectslist,vector,copy=False):
    """move(objects,vector,[copy]): Moves the objects contained
    in objects (that can be an object or a list of objects)
    in the direction and distance indicated by the given
    vector. If copy is True, the actual objects are not moved, but copies
    are created instead. The objects (or their copies) are returned."""
    typecheck([(vector,Vector), (copy,bool)], "move")
    if not isinstance(objectslist,list): objectslist = [objectslist]
    objectslist.extend(getMovableChildren(objectslist))
    newobjlist = []
    newgroups = {}
    objectslist = filterObjectsForModifiers(objectslist, copy)
    for obj in objectslist:
        if getType(obj) == "Point":
            v = Vector(obj.X,obj.Y,obj.Z)
            v = v.add(vector)
            if copy:
                newobj = makeCopy(obj)
            else:
                newobj = obj
            newobj.X = v.x
            newobj.Y = v.y
            newobj.Z = v.z
        elif hasattr(obj,'Shape'):
            if copy:
                newobj = makeCopy(obj)
            else:
                newobj = obj
            pla = newobj.Placement
            pla.move(vector)
        elif getType(obj) == "Annotation":
            if copy:
                newobj = FreeCAD.ActiveDocument.addObject("App::Annotation",getRealName(obj.Name))
                newobj.LabelText = obj.LabelText
                if gui:
                    formatObject(newobj,obj)
            else:
                newobj = obj
            newobj.Position = obj.Position.add(vector)
        elif getType(obj) == "DraftText":
            if copy:
                newobj = FreeCAD.ActiveDocument.addObject("App::FeaturePython",getRealName(obj.Name))
                DraftText(newobj)
                if gui:
                    ViewProviderDraftText(newobj.ViewObject)
                    formatObject(newobj,obj)
                newobj.Text = obj.Text
                newobj.Placement = obj.Placement
                if gui:
                    formatObject(newobj,obj)
            else:
                newobj = obj
            newobj.Placement.Base = obj.Placement.Base.add(vector)
        elif getType(obj) == "Dimension":
            if copy:
                newobj = FreeCAD.ActiveDocument.addObject("App::FeaturePython",getRealName(obj.Name))
                _Dimension(newobj)
                if gui:
                    _ViewProviderDimension(newobj.ViewObject)
                    formatObject(newobj,obj)
            else:
                newobj = obj
            newobj.Start = obj.Start.add(vector)
            newobj.End = obj.End.add(vector)
            newobj.Dimline = obj.Dimline.add(vector)
        else:
            if copy and obj.isDerivedFrom("Mesh::Feature"):
                print("Mesh copy not supported at the moment") # TODO
            newobj = obj
            if "Placement" in obj.PropertiesList:
                pla = obj.Placement
                pla.move(vector)
        newobjlist.append(newobj)
        if copy:
            for p in obj.InList:
                if p.isDerivedFrom("App::DocumentObjectGroup") and (p in objectslist):
                    g = newgroups.setdefault(p.Name,FreeCAD.ActiveDocument.addObject(p.TypeId,p.Name))
                    g.addObject(newobj)
                    break
                if getType(p) == "Layer":
                    p.Proxy.addObject(p,newobj)
    if copy and getParam("selectBaseObjects",False):
        select(objectslist)
    else:
        select(newobjlist)
    if len(newobjlist) == 1: return newobjlist[0]
    return newobjlist


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

def rotateVertex(object, vertex_index, angle, center, axis):
    points = object.Points
    points[vertex_index] = object.Placement.inverse().multVec(
        rotateVectorFromCenter(
            object.Placement.multVec(points[vertex_index]),
            angle, axis, center))
    object.Points = points

def rotateVectorFromCenter(vector, angle, axis, center):
    rv = vector.sub(center)
    rv = DraftVecUtils.rotate(rv, math.radians(angle), axis)
    return center.add(rv)

def rotateEdge(object, edge_index, angle, center, axis):
    rotateVertex(object, edge_index, angle, center, axis)
    if isClosedEdge(edge_index, object):
        rotateVertex(object, 0, angle, center, axis)
    else:
        rotateVertex(object, edge_index+1, angle, center, axis)

def rotate(objectslist,angle,center=Vector(0,0,0),axis=Vector(0,0,1),copy=False):
    """rotate(objects,angle,[center,axis,copy]): Rotates the objects contained
    in objects (that can be a list of objects or an object) of the given angle
    (in degrees) around the center, using axis as a rotation axis. If axis is
    omitted, the rotation will be around the vertical Z axis.
    If copy is True, the actual objects are not moved, but copies
    are created instead. The objects (or their copies) are returned."""
    import Part
    typecheck([(copy,bool)], "rotate")
    if not isinstance(objectslist,list): objectslist = [objectslist]
    objectslist.extend(getMovableChildren(objectslist))
    newobjlist = []
    newgroups = {}
    objectslist = filterObjectsForModifiers(objectslist, copy)
    for obj in objectslist:
        if copy:
            newobj = makeCopy(obj)
        else:
            newobj = obj
        if hasattr(obj,'Shape'):
            shape = obj.Shape.copy()
            shape.rotate(DraftVecUtils.tup(center), DraftVecUtils.tup(axis), angle)
            newobj.Shape = shape
        elif (obj.isDerivedFrom("App::Annotation")):
            if axis.normalize() == Vector(1,0,0):
                newobj.ViewObject.RotationAxis = "X"
                newobj.ViewObject.Rotation = angle
            elif axis.normalize() == Vector(0,1,0):
                newobj.ViewObject.RotationAxis = "Y"
                newobj.ViewObject.Rotation = angle
            elif axis.normalize() == Vector(0,-1,0):
                newobj.ViewObject.RotationAxis = "Y"
                newobj.ViewObject.Rotation = -angle
            elif axis.normalize() == Vector(0,0,1):
                newobj.ViewObject.RotationAxis = "Z"
                newobj.ViewObject.Rotation = angle
            elif axis.normalize() == Vector(0,0,-1):
                newobj.ViewObject.RotationAxis = "Z"
                newobj.ViewObject.Rotation = -angle
        elif getType(obj) == "Point":
            v = Vector(obj.X,obj.Y,obj.Z)
            rv = v.sub(center)
            rv = DraftVecUtils.rotate(rv,math.radians(angle),axis)
            v = center.add(rv)
            newobj.X = v.x
            newobj.Y = v.y
            newobj.Z = v.z
        elif hasattr(obj,"Placement"):
            shape = Part.Shape()
            shape.Placement = obj.Placement
            shape.rotate(DraftVecUtils.tup(center), DraftVecUtils.tup(axis), angle)
            newobj.Placement = shape.Placement
        if copy:
            formatObject(newobj,obj)
        newobjlist.append(newobj)
        if copy:
            for p in obj.InList:
                if p.isDerivedFrom("App::DocumentObjectGroup") and (p in objectslist):
                    g = newgroups.setdefault(p.Name,FreeCAD.ActiveDocument.addObject(p.TypeId,p.Name))
                    g.addObject(newobj)
                    break
    if copy and getParam("selectBaseObjects",False):
        select(objectslist)
    else:
        select(newobjlist)
    if len(newobjlist) == 1: return newobjlist[0]
    return newobjlist

def scaleVectorFromCenter(vector, scale, center):
    return vector.sub(center).scale(scale.x, scale.y, scale.z).add(center)

def scaleVertex(object, vertex_index, scale, center):
    points = object.Points
    points[vertex_index] = object.Placement.inverse().multVec(
        scaleVectorFromCenter(
            object.Placement.multVec(points[vertex_index]),
            scale, center))
    object.Points = points

def scaleEdge(object, edge_index, scale, center):
    scaleVertex(object, edge_index, scale, center)
    if isClosedEdge(edge_index, object):
        scaleVertex(object, 0, scale, center)
    else:
        scaleVertex(object, edge_index+1, scale, center)

def copyScaledEdges(arguments):
    copied_edges = []
    for argument in arguments:
        copied_edges.append(copyScaledEdge(argument[0], argument[1],
            argument[2], argument[3]))
    joinWires(copied_edges)

def copyScaledEdge(object, edge_index, scale, center):
    vertex1 = scaleVectorFromCenter(
        object.Placement.multVec(object.Points[edge_index]),
        scale, center)
    if isClosedEdge(edge_index, object):
        vertex2 = scaleVectorFromCenter(
            object.Placement.multVec(object.Points[0]),
            scale, center)
    else:
        vertex2 = scaleVectorFromCenter(
            object.Placement.multVec(object.Points[edge_index+1]),
            scale, center)
    return makeLine(vertex1, vertex2)

def scale(objectslist,scale=Vector(1,1,1),center=Vector(0,0,0),copy=False):
    """scale(objects,vector,[center,copy,legacy]): Scales the objects contained
    in objects (that can be a list of objects or an object) of the given scale
    factors defined by the given vector (in X, Y and Z directions) around
    given center. If copy is True, the actual objects are not moved, but copies
    are created instead. The objects (or their copies) are returned."""
    if not isinstance(objectslist, list):
        objectslist = [objectslist]
    newobjlist = []
    for obj in objectslist:
        if copy:
            newobj = makeCopy(obj)
        else:
            newobj = obj
        if hasattr(obj,'Shape'):
            scaled_shape = obj.Shape.copy()
            m = FreeCAD.Matrix()
            m.move(obj.Placement.Base.negative())
            m.move(center.negative())
            m.scale(scale.x,scale.y,scale.z)
            m.move(center)
            m.move(obj.Placement.Base)
            scaled_shape = scaled_shape.transformGeometry(m)
        if getType(obj) == "Rectangle":
            p = []
            for v in scaled_shape.Vertexes:
                p.append(v.Point)
            pl = obj.Placement.copy()
            pl.Base = p[0]
            diag = p[2].sub(p[0])
            bb = p[1].sub(p[0])
            bh = p[3].sub(p[0])
            nb = DraftVecUtils.project(diag,bb)
            nh = DraftVecUtils.project(diag,bh)
            if obj.Length < 0: l = -nb.Length
            else: l = nb.Length
            if obj.Height < 0: h = -nh.Length
            else: h = nh.Length
            newobj.Length = l
            newobj.Height = h
            tr = p[0].sub(obj.Shape.Vertexes[0].Point)
            newobj.Placement = pl
        elif getType(obj) == "Wire" or getType(obj) == "BSpline":
            for index, point in enumerate(newobj.Points):
                scaleVertex(newobj, index, scale, center)
        elif hasattr(obj,'Shape'):
            newobj.Shape = scaled_shape
        elif (obj.TypeId == "App::Annotation"):
            factor = scale.y * obj.ViewObject.FontSize
            newobj.ViewObject.FontSize = factor
            d = obj.Position.sub(center)
            newobj.Position = center.add(Vector(d.x*scale.x,d.y*scale.y,d.z*scale.z))
        if copy:
            formatObject(newobj,obj)
        newobjlist.append(newobj)
    if copy and getParam("selectBaseObjects",False):
        select(objectslist)
    else:
        select(newobjlist)
    if len(newobjlist) == 1: return newobjlist[0]
    return newobjlist

def offset(obj,delta,copy=False,bind=False,sym=False,occ=False):
    """offset(object,delta,[copymode],[bind]): offsets the given wire by
    applying the given delta Vector to its first vertex. If copymode is
    True, another object is created, otherwise the same object gets
    offsetted. If bind is True, and provided the wire is open, the original
    and the offsetted wires will be bound by their endpoints, forming a face
    if sym is True, bind must be true too, and the offset is made on both
    sides, the total width being the given delta length. If offsetting a
    BSpline, the delta must not be a Vector but a list of Vectors, one for
    each node of the spline."""
    import Part, DraftGeomUtils
    newwire = None
    delete = None

    if getType(obj) in ["Sketch","Part"]:
        copy = True
        print("the offset tool is currently unable to offset a non-Draft object directly - Creating a copy")

    def getRect(p,obj):
        """returns length,height,placement"""
        pl = obj.Placement.copy()
        pl.Base = p[0]
        diag = p[2].sub(p[0])
        bb = p[1].sub(p[0])
        bh = p[3].sub(p[0])
        nb = DraftVecUtils.project(diag,bb)
        nh = DraftVecUtils.project(diag,bh)
        if obj.Length.Value < 0: l = -nb.Length
        else: l = nb.Length
        if obj.Height.Value < 0: h = -nh.Length
        else: h = nh.Length
        return l,h,pl

    def getRadius(obj,delta):
        """returns a new radius for a regular polygon"""
        an = math.pi/obj.FacesNumber
        nr = DraftVecUtils.rotate(delta,-an)
        nr.multiply(1/math.cos(an))
        nr = obj.Shape.Vertexes[0].Point.add(nr)
        nr = nr.sub(obj.Placement.Base)
        nr = nr.Length
        if obj.DrawMode == "inscribed":
            return nr
        else:
            return nr * math.cos(math.pi/obj.FacesNumber)

    newwire = None
    if getType(obj) == "Circle":
        pass
    elif getType(obj) == "BSpline":
        pass
    else:
        if sym:
            d1 = Vector(delta).multiply(0.5)
            d2 = d1.negative()
            n1 = DraftGeomUtils.offsetWire(obj.Shape,d1)
            n2 = DraftGeomUtils.offsetWire(obj.Shape,d2)
        else:
            if isinstance(delta,float) and (len(obj.Shape.Edges) == 1):
                # circle
                c = obj.Shape.Edges[0].Curve
                nc = Part.Circle(c.Center,c.Axis,delta)
                if len(obj.Shape.Vertexes) > 1:
                    nc = Part.ArcOfCircle(nc,obj.Shape.Edges[0].FirstParameter,obj.Shape.Edges[0].LastParameter)
                newwire = Part.Wire(nc.toShape())
                p = []
            else:
                newwire = DraftGeomUtils.offsetWire(obj.Shape,delta)
                if DraftGeomUtils.hasCurves(newwire) and copy:
                    p = []
                else:
                    p = DraftGeomUtils.getVerts(newwire)
    if occ:
        newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
        newobj.Shape = DraftGeomUtils.offsetWire(obj.Shape,delta,occ=True)
        formatObject(newobj,obj)
        if not copy:
            delete = obj.Name
    elif bind:
        if not DraftGeomUtils.isReallyClosed(obj.Shape):
            if sym:
                s1 = n1
                s2 = n2
            else:
                s1 = obj.Shape
                s2 = newwire
            if s1 and s2:
                w1 = s1.Edges
                w2 = s2.Edges
                w3 = Part.LineSegment(s1.Vertexes[0].Point,s2.Vertexes[0].Point).toShape()
                w4 = Part.LineSegment(s1.Vertexes[-1].Point,s2.Vertexes[-1].Point).toShape()
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
                newobj.Shape = Part.Face(Part.Wire(w1+[w3]+w2+[w4]))
            else:
                print("Draft.offset: Unable to bind wires")
        else:
            newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
            newobj.Shape = Part.Face(obj.Shape.Wires[0])
        if not copy:
            delete = obj.Name
    elif copy:
        newobj = None
        if sym: return None
        if getType(obj) == "Wire":
            if p:
                newobj = makeWire(p)
                newobj.Closed = obj.Closed
            elif newwire:
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
                newobj.Shape = newwire
            else:
                print("Draft.offset: Unable to duplicate this object")
        elif getType(obj) == "Rectangle":
            if p:
                length,height,plac = getRect(p,obj)
                newobj = makeRectangle(length,height,plac)
            elif newwire:
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
                newobj.Shape = newwire
            else:
                print("Draft.offset: Unable to duplicate this object")
        elif getType(obj) == "Circle":
            pl = obj.Placement
            newobj = makeCircle(delta)
            newobj.FirstAngle = obj.FirstAngle
            newobj.LastAngle = obj.LastAngle
            newobj.Placement = pl
        elif getType(obj) == "Polygon":
            pl = obj.Placement
            newobj = makePolygon(obj.FacesNumber)
            newobj.Radius = getRadius(obj,delta)
            newobj.DrawMode = obj.DrawMode
            newobj.Placement = pl
        elif getType(obj) == "BSpline":
            newobj = makeBSpline(delta)
            newobj.Closed = obj.Closed
        else:
            # try to offset anyway
            try:
                if p:
                    newobj = makeWire(p)
                    newobj.Closed = obj.Shape.isClosed()
            except Part.OCCError:
                pass
            if not(newobj) and newwire:
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
                newobj.Shape = newwire
            else:
                print("Draft.offset: Unable to create an offset")
        if newobj:
            formatObject(newobj,obj)
    else:
        newobj = None
        if sym: return None
        if getType(obj) == "Wire":
            if obj.Base or obj.Tool:
                FreeCAD.Console.PrintWarning("Warning: object history removed\n")
                obj.Base = None
                obj.Tool = None
            obj.Points = p
        elif getType(obj) == "BSpline":
            #print(delta)
            obj.Points = delta
            #print("done")
        elif getType(obj) == "Rectangle":
            length,height,plac = getRect(p,obj)
            obj.Placement = plac
            obj.Length = length
            obj.Height = height
        elif getType(obj) == "Circle":
            obj.Radius = delta
        elif getType(obj) == "Polygon":
            obj.Radius = getRadius(obj,delta)
        elif getType(obj) == 'Part':
            print("unsupported object") # TODO
        newobj = obj
    if copy and getParam("selectBaseObjects",False):
        select(newobj)
    else:
        select(obj)
    if delete:
        FreeCAD.ActiveDocument.removeObject(delete)
    return newobj

def draftify(objectslist,makeblock=False,delete=True):
    """draftify(objectslist,[makeblock],[delete]): turns each object of the given list
    (objectslist can also be a single object) into a Draft parametric
    wire. If makeblock is True, multiple objects will be grouped in a block.
    If delete = False, old objects are not deleted"""
    import DraftGeomUtils, Part

    if not isinstance(objectslist,list):
        objectslist = [objectslist]
    newobjlist = []
    for obj in objectslist:
        if hasattr(obj,'Shape'):
            for cluster in Part.getSortedClusters(obj.Shape.Edges):
                w = Part.Wire(cluster)
                if DraftGeomUtils.hasCurves(w):
                    if (len(w.Edges) == 1) and (DraftGeomUtils.geomType(w.Edges[0]) == "Circle"):
                        nobj = makeCircle(w.Edges[0])
                    else:
                        nobj = FreeCAD.ActiveDocument.addObject("Part::Feature",obj.Name)
                        nobj.Shape = w
                else:
                    nobj = makeWire(w)
                newobjlist.append(nobj)
                formatObject(nobj,obj)
                # sketches are always in wireframe mode. In Draft we don't like that!
                nobj.ViewObject.DisplayMode = "Flat Lines"
            if delete:
                FreeCAD.ActiveDocument.removeObject(obj.Name)

    if makeblock:
        return makeBlock(newobjlist)
    else:
        if len(newobjlist) == 1:
            return newobjlist[0]
        return newobjlist

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


def makeSketch(objectslist,autoconstraints=False,addTo=None,
        delete=False,name="Sketch",radiusPrecision=-1):
    """makeSketch(objectslist,[autoconstraints],[addTo],[delete],[name],[radiusPrecision]):

    Makes a Sketch objectslist with the given Draft objects.

    * objectlist: can be single or list of objects of Draft type objects,
        Part::Feature, Part.Shape, or mix of them.

    * autoconstraints(False): if True, constraints will be automatically added to
        wire nodes, rectangles and circles.

    * addTo(None) : if set to an existing sketch, geometry will be added to it
        instead of creating a new one.

    * delete(False): if True, the original object will be deleted.
        If set to a string 'all' the object and all its linked object will be
        deleted

    * name('Sketch'): the name for the new sketch object

    * radiusPrecision(-1): If <0, disable radius constraint. If =0, add indiviaul
        radius constraint. If >0, the radius will be rounded according to this
        precision, and 'Equal' constraint will be added to curve with equal
        radius within precision."""

    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return

    import Part, DraftGeomUtils
    from Sketcher import Constraint
    import Sketcher
    import math

    StartPoint = 1
    EndPoint = 2
    MiddlePoint = 3
    deletable = None

    if not isinstance(objectslist,(list,tuple)):
        objectslist = [objectslist]
    for obj in objectslist:
        if isinstance(obj,Part.Shape):
            shape = obj
        elif not hasattr(obj,'Shape'):
            FreeCAD.Console.PrintError(translate("draft","not shape found"))
            return None
        else:
            shape = obj.Shape
        if not DraftGeomUtils.isPlanar(shape):
            FreeCAD.Console.PrintError(translate("draft","All Shapes must be co-planar"))
            return None
    if addTo:
        nobj = addTo
    else:
        nobj = FreeCAD.ActiveDocument.addObject("Sketcher::SketchObject", name)
        deletable = nobj
        nobj.ViewObject.Autoconstraints = False

    # Collect constraints and add in one go to improve performance
    constraints = []
    radiuses = {}

    def addRadiusConstraint(edge):
        try:
            if radiusPrecision<0:
                return
            if radiusPrecision==0:
                constraints.append(Constraint('Radius',
                        nobj.GeometryCount-1, edge.Curve.Radius))
                return
            r = round(edge.Curve.Radius,radiusPrecision)
            constraints.append(Constraint('Equal',
                    radiuses[r],nobj.GeometryCount-1))
        except KeyError:
            radiuses[r] = nobj.GeometryCount-1
            constraints.append(Constraint('Radius',nobj.GeometryCount-1, r))
        except AttributeError:
            pass

    def convertBezier(edge):
        if DraftGeomUtils.geomType(edge) == "BezierCurve":
            return(edge.Curve.toBSpline(edge.FirstParameter,edge.LastParameter).toShape())
        else:
            return(edge)

    rotation = None
    for obj in objectslist:
        ok = False
        tp = getType(obj)
        if tp in ["Circle","Ellipse"]:
            if obj.Shape.Edges:
                if rotation is None:
                    rotation = obj.Placement.Rotation
                edge = obj.Shape.Edges[0]
                if len(edge.Vertexes) == 1:
                    newEdge = DraftGeomUtils.orientEdge(edge)
                    nobj.addGeometry(newEdge)
                else:
                    # make new ArcOfCircle
                    circle = DraftGeomUtils.orientEdge(edge)
                    angle  = edge.Placement.Rotation.Angle
                    axis   = edge.Placement.Rotation.Axis
                    circle.Center = DraftVecUtils.rotate(edge.Curve.Center, -angle, axis)
                    first  = math.radians(obj.FirstAngle)
                    last   = math.radians(obj.LastAngle)
                    arc    = Part.ArcOfCircle(circle, first, last)
                    nobj.addGeometry(arc)
                addRadiusConstraint(edge)
                ok = True
        elif tp == "Rectangle":
            if rotation is None:
                rotation = obj.Placement.Rotation
            if obj.FilletRadius.Value == 0:
                for edge in obj.Shape.Edges:
                    nobj.addGeometry(DraftGeomUtils.orientEdge(edge))
                if autoconstraints:
                    last = nobj.GeometryCount - 1
                    segs = [last-3,last-2,last-1,last]
                    if obj.Placement.Rotation.Q == (0,0,0,1):
                        constraints.append(Constraint("Coincident",last-3,EndPoint,last-2,StartPoint))
                        constraints.append(Constraint("Coincident",last-2,EndPoint,last-1,StartPoint))
                        constraints.append(Constraint("Coincident",last-1,EndPoint,last,StartPoint))
                        constraints.append(Constraint("Coincident",last,EndPoint,last-3,StartPoint))
                    constraints.append(Constraint("Horizontal",last-3))
                    constraints.append(Constraint("Vertical",last-2))
                    constraints.append(Constraint("Horizontal",last-1))
                    constraints.append(Constraint("Vertical",last))
                ok = True
        elif tp in ["Wire","Polygon"]:
            if obj.FilletRadius.Value == 0:
                closed = False
                if tp == "Polygon":
                    closed = True
                elif hasattr(obj,"Closed"):
                    closed = obj.Closed

                if obj.Shape.Edges:
                    if (len(obj.Shape.Vertexes) < 3):
                        e = obj.Shape.Edges[0]
                        nobj.addGeometry(Part.LineSegment(e.Curve,e.FirstParameter,e.LastParameter))
                    else:
                        # Use the first three points to make a working plane. We've already
                        # checked to make sure everything is coplanar
                        plane = Part.Plane(*[i.Point for i in obj.Shape.Vertexes[:3]])
                        normal = plane.Axis
                        if rotation is None:
                            axis = FreeCAD.Vector(0,0,1).cross(normal)
                            angle = DraftVecUtils.angle(normal, FreeCAD.Vector(0,0,1)) * FreeCAD.Units.Radian
                            rotation = FreeCAD.Rotation(axis, angle)
                        for edge in obj.Shape.Edges:
                            # edge.rotate(FreeCAD.Vector(0,0,0), rotAxis, rotAngle)
                            edge = DraftGeomUtils.orientEdge(edge, normal)
                            nobj.addGeometry(edge)
                        if autoconstraints:
                            last = nobj.GeometryCount
                            segs = list(range(last-len(obj.Shape.Edges),last-1))
                            for seg in segs:
                                constraints.append(Constraint("Coincident",seg,EndPoint,seg+1,StartPoint))
                                if DraftGeomUtils.isAligned(nobj.Geometry[seg],"x"):
                                    constraints.append(Constraint("Vertical",seg))
                                elif DraftGeomUtils.isAligned(nobj.Geometry[seg],"y"):
                                    constraints.append(Constraint("Horizontal",seg))
                            if closed:
                                constraints.append(Constraint("Coincident",last-1,EndPoint,segs[0],StartPoint))
                    ok = True
        elif tp == "BSpline":
            if obj.Shape.Edges:
                nobj.addGeometry(obj.Shape.Edges[0].Curve)
                nobj.exposeInternalGeometry(nobj.GeometryCount-1)
                ok = True
        elif tp == "BezCurve":
            if obj.Shape.Edges:
                bez = obj.Shape.Edges[0].Curve
                bsp = bez.toBSpline(bez.FirstParameter,bez.LastParameter)
                nobj.addGeometry(bsp)
                nobj.exposeInternalGeometry(nobj.GeometryCount-1)
                ok = True
        elif tp == 'Shape' or hasattr(obj,'Shape'):
            shape = obj if tp == 'Shape' else obj.Shape

            if not DraftGeomUtils.isPlanar(shape):
                FreeCAD.Console.PrintError(translate("draft","The given object is not planar and cannot be converted into a sketch."))
                return None
            if rotation is None:
                #rotation = obj.Placement.Rotation
                norm = DraftGeomUtils.getNormal(shape)
                if norm:
                    rotation = FreeCAD.Rotation(FreeCAD.Vector(0,0,1),norm)
                else:
                    FreeCAD.Console.PrintWarning(translate("draft","Unable to guess the normal direction of this object"))
                    rotation = FreeCAD.Rotation()
                    norm = obj.Placement.Rotation.Axis
            if not shape.Wires:
                for e in shape.Edges:
                    # unconnected edges
                    newedge = convertBezier(e)
                    nobj.addGeometry(DraftGeomUtils.orientEdge(newedge,norm,make_arc=True))
                    addRadiusConstraint(newedge)

            # if not addTo:
                # nobj.Placement.Rotation = DraftGeomUtils.calculatePlacement(shape).Rotation

            if autoconstraints:
                for wire in shape.Wires:
                    last_count = nobj.GeometryCount
                    edges = wire.OrderedEdges
                    for edge in edges:
                        newedge = convertBezier(edge)
                        nobj.addGeometry(DraftGeomUtils.orientEdge(
                                            newedge,norm,make_arc=True))
                        addRadiusConstraint(newedge)
                    for i,g in enumerate(nobj.Geometry[last_count:]):
                        if edges[i].Closed:
                            continue
                        seg = last_count+i

                        if DraftGeomUtils.isAligned(g,"x"):
                            constraints.append(Constraint("Vertical",seg))
                        elif DraftGeomUtils.isAligned(g,"y"):
                            constraints.append(Constraint("Horizontal",seg))

                        if seg == nobj.GeometryCount-1:
                            if not wire.isClosed():
                                break
                            g2 = nobj.Geometry[last_count]
                            seg2 = last_count
                        else:
                            seg2 = seg+1
                            g2 = nobj.Geometry[seg2]

                        end1 = g.value(g.LastParameter)
                        start2 = g2.value(g2.FirstParameter)
                        if DraftVecUtils.equals(end1,start2) :
                            constraints.append(Constraint(
                                "Coincident",seg,EndPoint,seg2,StartPoint))
                            continue
                        end2 = g2.value(g2.LastParameter)
                        start1 = g.value(g.FirstParameter)
                        if DraftVecUtils.equals(end2,start1):
                            constraints.append(Constraint(
                                "Coincident",seg,StartPoint,seg2,EndPoint))
                        elif DraftVecUtils.equals(start1,start2):
                            constraints.append(Constraint(
                                "Coincident",seg,StartPoint,seg2,StartPoint))
                        elif DraftVecUtils.equals(end1,end2):
                            constraints.append(Constraint(
                                "Coincident",seg,EndPoint,seg2,EndPoint))
            else:
                for wire in shape.Wires:
                    for edge in wire.OrderedEdges:
                        newedge = convertBezier(edge)
                        nobj.addGeometry(DraftGeomUtils.orientEdge(
                                                newedge,norm,make_arc=True))
            ok = True
        formatObject(nobj,obj)
        if ok and delete and hasattr(obj,'Shape'):
            doc = obj.Document
            def delObj(obj):
                if obj.InList:
                    FreeCAD.Console.PrintWarning(translate("draft",
                        "Cannot delete object {} with dependency".format(obj.Label))+"\n")
                else:
                    doc.removeObject(obj.Name)
            try:
                if delete == 'all':
                    objs = [obj]
                    while objs:
                        obj = objs[0]
                        objs = objs[1:] + obj.OutList
                        delObj(obj)
                else:
                    delObj(obj)
            except Exception as ex:
                FreeCAD.Console.PrintWarning(translate("draft",
                    "Failed to delete object {}: {}".format(obj.Label,ex))+"\n")
    if rotation:
        nobj.Placement.Rotation = rotation
    else:
        print("-----error!!! rotation is still None...")
    nobj.addConstraint(constraints)

    return nobj


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


def mirror(objlist,p1,p2):
    """mirror(objlist,p1,p2,[clone]): creates a mirrored version of the given object(s)
    along an axis that passes through the two vectors p1 and p2."""

    if not objlist:
        FreeCAD.Console.PrintError(translate("draft","No object given")+"\n")
        return
    if p1 == p2:
        FreeCAD.Console.PrintError(translate("draft","The two points are coincident")+"\n")
        return
    if not isinstance(objlist,list):
        objlist = [objlist]

    result = []

    for obj in objlist:
        mir = FreeCAD.ActiveDocument.addObject("Part::Mirroring","mirror")
        mir.Label = "Mirror of "+obj.Label
        mir.Source = obj
        if gui:
            norm = FreeCADGui.ActiveDocument.ActiveView.getViewDirection().negative()
        else:
            norm = FreeCAD.Vector(0,0,1)
        pnorm = p2.sub(p1).cross(norm).normalize()
        mir.Base = p1
        mir.Normal = pnorm
        formatObject(mir,obj)
        result.append(mir)

    if len(result) == 1:
        result = result[0]
        select(result)
    return result


def heal(objlist=None,delete=True,reparent=True):
    """heal([objlist],[delete],[reparent]) - recreates Draft objects that are damaged,
    for example if created from an earlier version. If delete is True,
    the damaged objects are deleted (default). If ran without arguments, all the objects
    in the document will be healed if they are damaged. If reparent is True (default),
    new objects go at the very same place in the tree than their original."""

    auto = False

    if not objlist:
        objlist = FreeCAD.ActiveDocument.Objects
        print("Automatic mode: Healing whole document...")
        auto = True
    else:
        print("Manual mode: Force-healing selected objects...")

    if not isinstance(objlist,list):
        objlist = [objlist]

    dellist = []
    got = False

    for obj in objlist:
        dtype = getType(obj)
        ftype = obj.TypeId
        if ftype in ["Part::FeaturePython","App::FeaturePython","Part::Part2DObjectPython","Drawing::FeatureViewPython"]:
            proxy = obj.Proxy
            if hasattr(obj,"ViewObject"):
                if hasattr(obj.ViewObject,"Proxy"):
                    proxy = obj.ViewObject.Proxy
            if (proxy == 1) or (dtype in ["Unknown","Part"]) or (not auto):
                got = True
                dellist.append(obj.Name)
                props = obj.PropertiesList
                if ("Dimline" in props) and ("Start" in props):
                    print("Healing " + obj.Name + " of type Dimension")
                    nobj = makeCopy(obj,force="Dimension",reparent=reparent)
                elif ("Height" in props) and ("Length" in props):
                    print("Healing " + obj.Name + " of type Rectangle")
                    nobj = makeCopy(obj,force="Rectangle",reparent=reparent)
                elif ("Points" in props) and ("Closed" in props):
                    if "BSpline" in obj.Name:
                        print("Healing " + obj.Name + " of type BSpline")
                        nobj = makeCopy(obj,force="BSpline",reparent=reparent)
                    else:
                        print("Healing " + obj.Name + " of type Wire")
                        nobj = makeCopy(obj,force="Wire",reparent=reparent)
                elif ("Radius" in props) and ("FirstAngle" in props):
                    print("Healing " + obj.Name + " of type Circle")
                    nobj = makeCopy(obj,force="Circle",reparent=reparent)
                elif ("DrawMode" in props) and ("FacesNumber" in props):
                    print("Healing " + obj.Name + " of type Polygon")
                    nobj = makeCopy(obj,force="Polygon",reparent=reparent)
                elif ("FillStyle" in props) and ("FontSize" in props):
                    nobj = makeCopy(obj,force="DrawingView",reparent=reparent)
                else:
                    dellist.pop()
                    print("Object " + obj.Name + " is not healable")

    if not got:
        print("No object seems to need healing")
    else:
        print("Healed ",len(dellist)," objects")

    if dellist and delete:
        for n in dellist:
            FreeCAD.ActiveDocument.removeObject(n)


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


def calculatePlacement(globalRotation, edge, offset, RefPt, xlate, align, normal=None):
    """Orient shape to tangent at parm offset along edge."""
    import functools
    # http://en.wikipedia.org/wiki/Euler_angles
    # start with null Placement point so translate goes to right place.
    placement = FreeCAD.Placement()
    # preserve global orientation
    placement.Rotation = globalRotation

    placement.move(RefPt + xlate)

    if not align:
        return placement

    # unit +Z  Probably defined elsewhere?
    z = FreeCAD.Vector(0, 0, 1)
    # y = FreeCAD.Vector(0, 1, 0)               # unit +Y
    x = FreeCAD.Vector(1, 0, 0)                 # unit +X
    nullv = FreeCAD.Vector(0, 0, 0)

    # get local coord system - tangent, normal, binormal, if possible
    t = edge.tangentAt(getParameterFromV0(edge, offset))
    t.normalize()

    try:
        if normal:
            n = normal
        else:
            n = edge.normalAt(getParameterFromV0(edge, offset))
            n.normalize()
        b = (t.cross(n))
        b.normalize()
    # no normal defined here
    except FreeCAD.Base.FreeCADError:
        n = nullv
        b = nullv
        FreeCAD.Console.PrintLog(
            "Draft PathArray.orientShape - Cannot calculate Path normal.\n")

    lnodes = z.cross(b)

    try:
        # Can't normalize null vector.
        lnodes.normalize()
    except:
        # pathological cases:
        pass
    # 1) can't determine normal, don't align.
    if n == nullv:
        psi = 0.0
        theta = 0.0
        phi = 0.0
        FreeCAD.Console.PrintWarning(
            "Draft PathArray.orientShape - Path normal is Null. Cannot align.\n")
    elif abs(b.dot(z)) == 1.0:                                    # 2) binormal is || z
        # align shape to tangent only
        psi = math.degrees(DraftVecUtils.angle(x, t, z))
        theta = 0.0
        phi = 0.0
        FreeCAD.Console.PrintWarning(
            "Draft PathArray.orientShape - Gimbal lock. Infinite lnodes. Change Path or Base.\n")
    else:                                                        # regular case
        psi = math.degrees(DraftVecUtils.angle(x, lnodes, z))
        theta = math.degrees(DraftVecUtils.angle(z, b, lnodes))
        phi = math.degrees(DraftVecUtils.angle(lnodes, t, b))

    rotations = [placement.Rotation]

    if psi != 0.0:
        rotations.insert(0, FreeCAD.Rotation(z, psi))
    if theta != 0.0:
        rotations.insert(0, FreeCAD.Rotation(lnodes, theta))
    if phi != 0.0:
        rotations.insert(0, FreeCAD.Rotation(b, phi))

    if len(rotations) == 1:
        finalRotation = rotations[0]
    else:
        finalRotation = functools.reduce(
            lambda rot1, rot2: rot1.multiply(rot2), rotations)

    placement.Rotation = finalRotation

    return placement


def calculatePlacementsOnPath(shapeRotation, pathwire, count, xlate, align):
    """Calculates the placements of a shape along a given path so that each copy will be distributed evenly"""
    import Part
    import DraftGeomUtils

    closedpath = DraftGeomUtils.isReallyClosed(pathwire)
    normal = DraftGeomUtils.getNormal(pathwire)
    path = Part.__sortEdges__(pathwire.Edges)
    ends = []
    cdist = 0

    for e in path:                                                 # find cumulative edge end distance
        cdist += e.Length
        ends.append(cdist)

    placements = []

    # place the start shape
    pt = path[0].Vertexes[0].Point
    placements.append(calculatePlacement(
        shapeRotation, path[0], 0, pt, xlate, align, normal))

    # closed path doesn't need shape on last vertex
    if not(closedpath):
        # place the end shape
        pt = path[-1].Vertexes[-1].Point
        placements.append(calculatePlacement(
            shapeRotation, path[-1], path[-1].Length, pt, xlate, align, normal))

    if count < 3:
        return placements

    # place the middle shapes
    if closedpath:
        stop = count
    else:
        stop = count - 1
    step = float(cdist) / stop
    remains = 0
    travel = step
    for i in range(1, stop):
        # which edge in path should contain this shape?
        # avoids problems with float math travel > ends[-1]
        iend = len(ends) - 1

        for j in range(0, len(ends)):
            if travel <= ends[j]:
                iend = j
                break

        # place shape at proper spot on proper edge
        remains = ends[iend] - travel
        offset = path[iend].Length - remains
        pt = path[iend].valueAt(getParameterFromV0(path[iend], offset))

        placements.append(calculatePlacement(
            shapeRotation, path[iend], offset, pt, xlate, align, normal))

        travel += step

    return placements

#---------------------------------------------------------------------------
# Python Features definitions
#---------------------------------------------------------------------------

class _DraftObject:
    """The base class for Draft objects"""
    def __init__(self,obj,tp="Unknown"):
        if obj:
            obj.Proxy = self
        self.Type = tp

    def __getstate__(self):
        return self.Type

    def __setstate__(self,state):
        if state:
            self.Type = state

    def execute(self,obj):
        pass

    def onChanged(self, obj, prop):
        pass

class _ViewProviderDraft:
    """The base class for Draft Viewproviders"""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object
        vobj.addProperty("App::PropertyEnumeration","Pattern","Draft",QT_TRANSLATE_NOOP("App::Property","Defines a hatch pattern"))
        vobj.addProperty("App::PropertyFloat","PatternSize","Draft",QT_TRANSLATE_NOOP("App::Property","Sets the size of the pattern"))
        vobj.Pattern = ["None"]+list(svgpatterns().keys())
        vobj.PatternSize = 1

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def attach(self,vobj):
        self.texture = None
        self.texcoords = None
        self.Object = vobj.Object
        self.onChanged(vobj,"Pattern")
        return

    def updateData(self, obj, prop):
        return

    def getDisplayModes(self, vobj):
        modes=[]
        return modes

    def setDisplayMode(self, mode):
        return mode

    def onChanged(self, vobj, prop):
        # treatment of patterns and image textures
        if prop in ["TextureImage","Pattern","DiffuseColor"]:
            if hasattr(self.Object,"Shape"):
                if self.Object.Shape.Faces:
                    from pivy import coin
                    from PySide import QtCore
                    path = None
                    if hasattr(vobj,"TextureImage"):
                        if vobj.TextureImage:
                            path = vobj.TextureImage
                    if not path:
                        if hasattr(vobj,"Pattern"):
                            if str(vobj.Pattern) in list(svgpatterns().keys()):
                                path = svgpatterns()[vobj.Pattern][1]
                            else:
                                path = "None"
                    if path and vobj.RootNode:
                        if vobj.RootNode.getChildren().getLength() > 2:
                            if vobj.RootNode.getChild(2).getChildren().getLength() > 0:
                                if vobj.RootNode.getChild(2).getChild(0).getChildren().getLength() > 2:
                                    r = vobj.RootNode.getChild(2).getChild(0).getChild(2)
                                    i = QtCore.QFileInfo(path)
                                    if self.texture:
                                        r.removeChild(self.texture)
                                        self.texture = None
                                    if self.texcoords:
                                        r.removeChild(self.texcoords)
                                        self.texcoords = None
                                    if i.exists():
                                        size = None
                                        if ".SVG" in path.upper():
                                            size = getParam("HatchPatternResolution",128)
                                            if not size:
                                                size = 128
                                        im = loadTexture(path, size)
                                        if im:
                                            self.texture = coin.SoTexture2()
                                            self.texture.image = im
                                            r.insertChild(self.texture,1)
                                            if size:
                                                s =1
                                                if hasattr(vobj,"PatternSize"):
                                                    if vobj.PatternSize:
                                                        s = vobj.PatternSize
                                                self.texcoords = coin.SoTextureCoordinatePlane()
                                                self.texcoords.directionS.setValue(s,0,0)
                                                self.texcoords.directionT.setValue(0,s,0)
                                                r.insertChild(self.texcoords,2)
        elif prop == "PatternSize":
            if hasattr(self,"texcoords"):
                if self.texcoords:
                    s = 1
                    if vobj.PatternSize:
                        s = vobj.PatternSize
                    vS = FreeCAD.Vector(self.texcoords.directionS.getValue().getValue())
                    vT = FreeCAD.Vector(self.texcoords.directionT.getValue().getValue())
                    vS.Length = s
                    vT.Length = s
                    self.texcoords.directionS.setValue(vS.x,vS.y,vS.z)
                    self.texcoords.directionT.setValue(vT.x,vT.y,vT.z)
        return

    def execute(self,vobj):
        return

    def setEdit(self,vobj,mode=0):
        if mode == 0:
            FreeCADGui.runCommand("Draft_Edit")
            return True
        return False

    def unsetEdit(self,vobj,mode=0):
        if FreeCAD.activeDraftCommand:
            FreeCAD.activeDraftCommand.finish()
        FreeCADGui.Control.closeDialog()
        return False

    def getIcon(self):
        return(":/icons/Draft_Draft.svg")

    def claimChildren(self):
        objs = []
        if hasattr(self.Object,"Base"):
            objs.append(self.Object.Base)
        if hasattr(self.Object,"Objects"):
            objs.extend(self.Object.Objects)
        if hasattr(self.Object,"Components"):
            objs.extend(self.Object.Components)
        if hasattr(self.Object,"Group"):
            objs.extend(self.Object.Group)
        return objs

class _ViewProviderDraftAlt(_ViewProviderDraft):
    """a view provider that doesn't swallow its base object"""

    def __init__(self,vobj):
        _ViewProviderDraft.__init__(self,vobj)

    def claimChildren(self):
        return []

class _ViewProviderDraftPart(_ViewProviderDraftAlt):
    """a view provider that displays a Part icon instead of a Draft icon"""

    def __init__(self,vobj):
        _ViewProviderDraftAlt.__init__(self,vobj)

    def getIcon(self):
        return ":/icons/Tree_Part.svg"

class _ViewProviderDraftLink:
    "a view provider for link type object"

    def __init__(self,vobj):
        self.Object = vobj.Object
        vobj.Proxy = self

    def attach(self,vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def getIcon(self):
        tp = self.Object.Proxy.Type
        if tp == 'Array':
            return ":/icons/Draft_LinkArray.svg"
        elif tp == 'PathArray':
            return ":/icons/Draft_PathLinkArray.svg"

    def claimChildren(self):
        obj = self.Object
        if hasattr(obj,'ExpandArray'):
            expand = obj.ExpandArray
        else:
            expand = obj.ShowElement
        if not expand:
            return [obj.Base]
        else:
            return obj.ElementList

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

class _DraftLink(_DraftObject):

    def __init__(self,obj,tp):
        self.useLink = False if obj else True
        _DraftObject.__init__(self,obj,tp)
        if obj:
            self.attach(obj)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self,state):
        if isinstance(state,dict):
            self.__dict__ = state
        else:
            self.useLink = False
            _DraftObject.__setstate__(self,state)

    def attach(self,obj):
        if self.useLink:
            obj.addExtension('App::LinkExtensionPython', None)
            self.linkSetup(obj)

    def canLinkProperties(self,_obj):
        return False

    def linkSetup(self,obj):
        obj.configLinkProperty('Placement',LinkedObject='Base')
        if hasattr(obj,'ShowElement'):
            # rename 'ShowElement' property to 'ExpandArray' to avoid conflict
            # with native App::Link
            obj.configLinkProperty('ShowElement')
            showElement = obj.ShowElement
            obj.addProperty("App::PropertyBool","ExpandArray","Draft",
                    QT_TRANSLATE_NOOP("App::Property","Show array element as children object"))
            obj.ExpandArray = showElement
            obj.configLinkProperty(ShowElement='ExpandArray')
            obj.removeProperty('ShowElement')
        else:
            obj.configLinkProperty(ShowElement='ExpandArray')
        if getattr(obj,'ExpandArray',False):
            obj.setPropertyStatus('PlacementList','Immutable')
        else:
            obj.setPropertyStatus('PlacementList','-Immutable')

    def getViewProviderName(self,_obj):
        if self.useLink:
            return 'Gui::ViewProviderLinkPython'
        return ''

    def onDocumentRestored(self, obj):
        if self.useLink:
            self.linkSetup(obj)
            if obj.Shape.isNull():
                self.buildShape(obj,obj.Placement,obj.PlacementList)

    def buildShape(self,obj,pl,pls):
        import Part
        import DraftGeomUtils

        if self.useLink:
            if not getattr(obj,'ExpandArray',True) or obj.Count != len(pls):
                obj.setPropertyStatus('PlacementList','-Immutable')
                obj.PlacementList = pls
                obj.setPropertyStatus('PlacementList','Immutable')
                obj.Count = len(pls)

        if obj.Base:
            shape = Part.getShape(obj.Base)
            if shape.isNull():
                raise RuntimeError("'{}' cannot build shape of '{}'\n".format(
                        obj.Name,obj.Base.Name))
            else:
                shape = shape.copy()
                shape.Placement = FreeCAD.Placement()
                base = []
                for i,pla in enumerate(pls):
                    vis = getattr(obj,'VisibilityList',[])
                    if len(vis)>i and not vis[i]:
                        continue;
                    # 'I' is a prefix for disambiguation when mapping element names
                    base.append(shape.transformed(pla.toMatrix(),op='I{}'.format(i)))
                if getattr(obj,'Fuse',False) and len(base) > 1:
                    obj.Shape = base[0].multiFuse(base[1:]).removeSplitter()
                else:
                    obj.Shape = Part.makeCompound(base)

                if not DraftGeomUtils.isNull(pl):
                    obj.Placement = pl

        if self.useLink:
            return False # return False to call LinkExtension::execute()

    def onChanged(self, obj, prop):
        if getattr(obj,'useLink',False):
            return
        elif prop == 'Fuse':
            if obj.Fuse:
                obj.setPropertyStatus('Shape','-Transient')
            else:
                obj.setPropertyStatus('Shape','Transient')
        elif prop == 'ExpandArray':
            if hasattr(obj,'PlacementList'):
                obj.setPropertyStatus('PlacementList',
                        '-Immutable' if obj.ExpandArray else 'Immutable')


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
