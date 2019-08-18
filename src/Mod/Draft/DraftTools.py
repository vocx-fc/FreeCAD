# -*- coding: utf8 -*-

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

__title__="FreeCAD Draft Workbench GUI Tools"
__author__ = "Yorik van Havre, Werner Mayer, Martin Burbaum, Ken Cline, Dmitry Chigrin"
__url__ = "http://www.freecadweb.org"

## @package DraftTools
#  \ingroup DRAFT
#  \brief GUI Commands of the Draft workbench
#
#  This module contains all the FreeCAD commands
#  of the Draft module

#---------------------------------------------------------------------------
# Generic stuff
#---------------------------------------------------------------------------

import sys, os, FreeCAD, FreeCADGui, WorkingPlane, math, re, Draft, Draft_rc, DraftVecUtils
from FreeCAD import Vector
from PySide import QtCore,QtGui
from DraftGui import todo, translate, utf8_decode
from DraftSnap import *
from DraftTrackers import *
from pivy import coin

#---------------------------------------------------------------------------
# Commands that have been migrated to their own modules
#---------------------------------------------------------------------------

import DraftEdit
# import DraftFillet
import DraftSelectPlane

#---------------------------------------------------------------------------
# Preflight stuff
#---------------------------------------------------------------------------

# update the translation engine
FreeCADGui.updateLocale()

# sets the default working plane
plane = WorkingPlane.plane()
FreeCAD.DraftWorkingPlane = plane
defaultWP = Draft.getParam("defaultWP",1)
if defaultWP == 1: plane.alignToPointAndAxis(Vector(0,0,0), Vector(0,0,1), 0)
elif defaultWP == 2: plane.alignToPointAndAxis(Vector(0,0,0), Vector(0,1,0), 0)
elif defaultWP == 3: plane.alignToPointAndAxis(Vector(0,0,0), Vector(1,0,0), 0)

# last snapped objects, for quick intersection calculation
lastObj = [0,0]

# set modifier keys
MODS = ["shift","ctrl","alt"]
MODCONSTRAIN = MODS[Draft.getParam("modconstrain",0)]
MODSNAP = MODS[Draft.getParam("modsnap",1)]
MODALT = MODS[Draft.getParam("modalt",2)]

#---------------------------------------------------------------------------
# General functions
#---------------------------------------------------------------------------

def formatUnit(exp,unit="mm"):
    '''returns a formatting string to set a number to the correct unit'''
    return FreeCAD.Units.Quantity(exp,FreeCAD.Units.Length).UserString

def selectObject(arg):
    '''this is a scene even handler, to be called from the Draft tools
    when they need to select an object'''
    if (arg["Type"] == "SoKeyboardEvent"):
        if (arg["Key"] == "ESCAPE"):
            FreeCAD.activeDraftCommand.finish()
            # TODO : this part raises a coin3D warning about scene traversal, to be fixed.
    elif (arg["Type"] == "SoMouseButtonEvent"):
        if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
            cursor = arg["Position"]
            snapped = Draft.get3DView().getObjectInfo((cursor[0],cursor[1]))
            if snapped:
                obj = FreeCAD.ActiveDocument.getObject(snapped['Object'])
                FreeCADGui.Selection.addSelection(obj)
                FreeCAD.activeDraftCommand.component=snapped['Component']
                FreeCAD.activeDraftCommand.proceed()

def getPoint(target,args,mobile=False,sym=False,workingplane=True,noTracker=False):
    """Function used by the Draft Tools.
    returns a constrained 3d point and its original point.
    if mobile=True, the constraining occurs from the location of
    mouse cursor when Shift is pressed, otherwise from last entered
    point. If sym=True, x and y values stay always equal. If workingplane=False,
    the point won't be projected on the Working Plane. if noTracker is True, the
    tracking line will not be displayed
    """

    ui = FreeCADGui.draftToolBar

    if target.node:
        last = target.node[-1]
    else:
        last = None

    amod = hasMod(args, MODSNAP)
    cmod = hasMod(args, MODCONSTRAIN)
    point = None

    if hasattr(FreeCADGui, "Snapper"):
        point = FreeCADGui.Snapper.snap(args["Position"],lastpoint=last,active=amod,constrain=cmod,noTracker=noTracker)
        info = FreeCADGui.Snapper.snapInfo
        mask = FreeCADGui.Snapper.affinity
    if not point:
        p = FreeCADGui.ActiveDocument.ActiveView.getCursorPos()
        point = FreeCADGui.ActiveDocument.ActiveView.getPoint(p)
        info = FreeCADGui.ActiveDocument.ActiveView.getObjectInfo(p)
        mask = None

    ctrlPoint = Vector(point)
    if target.node:
        if target.featureName == "Rectangle":
            ui.displayPoint(point, target.node[0], plane=plane, mask=mask)
        else:
            ui.displayPoint(point, target.node[-1], plane=plane, mask=mask)
    else:
        ui.displayPoint(point, plane=plane, mask=mask)
    return point,ctrlPoint,info

def getSupport(mouseEvent=None):
    """returns the supporting object and sets the working plane"""
    plane.save()
    if mouseEvent:
        return setWorkingPlaneToObjectUnderCursor(mouseEvent)
    return setWorkingPlaneToSelectedObject()

def setWorkingPlaneToObjectUnderCursor(mouseEvent):
    objectUnderCursor = Draft.get3DView().getObjectInfo((
        mouseEvent["Position"][0],
        mouseEvent["Position"][1]))

    if not objectUnderCursor:
        return None

    try:
        componentUnderCursor = getattr(
            FreeCAD.ActiveDocument.getObject(
                objectUnderCursor['Object']
                ).Shape,
            objectUnderCursor["Component"])

        if not plane.weak:
            return None

        if "Face" in objectUnderCursor["Component"]:
            plane.alignToFace(componentUnderCursor)
        else:
            plane.alignToCurve(componentUnderCursor)
        plane.weak = True
        return objectUnderCursor
    except:
        pass

    return None

def setWorkingPlaneToSelectedObject():
    sel = FreeCADGui.Selection.getSelectionEx()
    if len(sel) != 1:
        return None
    sel = sel[0]
    if sel.HasSubObjects \
        and len(sel.SubElementNames) == 1 \
        and "Face" in sel.SubElementNames[0]:
        if plane.weak:
            plane.alignToFace(sel.SubObjects[0])
            plane.weak = True
        return sel.Object
    return None

def hasMod(args,mod):
    """checks if args has a specific modifier"""
    if mod == "shift":
        return args["ShiftDown"]
    elif mod == "ctrl":
        return args["CtrlDown"]
    elif mod == "alt":
        return args["AltDown"]

def setMod(args,mod,state):
    """sets a specific modifier state in args"""
    if mod == "shift":
        args["ShiftDown"] = state
    elif mod == "ctrl":
        args["CtrlDown"] = state
    elif mod == "alt":
        args["AltDown"] = state




#---------------------------------------------------------------------------
# Base Class
#---------------------------------------------------------------------------

class DraftTool:
    """The base class of all Draft Tools"""

    def __init__(self):
        self.commitList = []

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self, name="None", noplanesetup=False, is_subtool=False):
        if FreeCAD.activeDraftCommand and not is_subtool:
            FreeCAD.activeDraftCommand.finish()

        global Part, DraftGeomUtils
        import Part, DraftGeomUtils

        self.ui = None
        self.call = None
        self.support = None
        self.point = None
        self.commitList = []
        self.doc = FreeCAD.ActiveDocument
        if not self.doc:
            self.finish()
            return

        FreeCAD.activeDraftCommand = self
        self.view = Draft.get3DView()
        self.ui = FreeCADGui.draftToolBar
        self.featureName = name
        self.ui.sourceCmd = self
        self.ui.setTitle(name)
        self.ui.show()
        if not noplanesetup:
            plane.setup()
        self.node = []
        self.pos = []
        self.constrain = None
        self.obj = None
        self.extendedCopy = False
        self.ui.setTitle(name)
        self.planetrack = None
        if Draft.getParam("showPlaneTracker",False):
            self.planetrack = PlaneTracker()
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.setTrackers()

    def finish(self,close=False):
        self.node = []
        FreeCAD.activeDraftCommand = None
        if self.ui:
            self.ui.offUi()
            self.ui.sourceCmd = None
        if self.planetrack:
            self.planetrack.finalize()
        plane.restore()
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.off()
        if self.call:
            try:
                self.view.removeEventCallback("SoEvent",self.call)
            except RuntimeError:
                # the view has been deleted already
                pass
            self.call = None
        if self.commitList:
            todo.delayCommit(self.commitList)
        self.commitList = []

    def commit(self,name,func):
        """stores actions to be committed to the FreeCAD document"""
        self.commitList.append((name,func))

    def getStrings(self,addrot=None):
        """returns a couple of useful strings for building python commands"""

        # current plane rotation
        p = plane.getRotation()
        qr = p.Rotation.Q
        qr = '('+str(qr[0])+','+str(qr[1])+','+str(qr[2])+','+str(qr[3])+')'

        # support object
        if self.support and FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").GetBool("useSupport",False):
            sup = 'FreeCAD.ActiveDocument.getObject("' + self.support.Name + '")'
        else:
            sup = 'None'

        # contents of self.node
        points='['
        for n in self.node:
            if len(points) > 1:
                points += ','
            points += DraftVecUtils.toString(n)
        points += ']'

        # fill mode
        if self.ui:
            fil = str(bool(self.ui.fillmode))
        else:
            fil = "True"

        return qr,sup,points,fil

#---------------------------------------------------------------------------
# Helper tools
#---------------------------------------------------------------------------



#---------------------------------------------------------------------------
# Geometry constructors
#---------------------------------------------------------------------------

def redraw3DView():
    """redraw3DView(): forces a redraw of 3d view."""
    try:
        FreeCADGui.ActiveDocument.ActiveView.redraw()
    except AttributeError as err:
        pass

class Creator(DraftTool):
    """A generic Draft Creator Tool used by creation tools such as line or arc"""

    def __init__(self):
        DraftTool.__init__(self)

    def Activated(self,name="None",noplanesetup=False):
        DraftTool.Activated(self,name,noplanesetup)
        if not noplanesetup:
            self.support = getSupport()


class FinishLine:
    """a FreeCAD command to finish any running Line drawing operation"""

    def Activated(self):
        if (FreeCAD.activeDraftCommand != None):
            if (FreeCAD.activeDraftCommand.featureName == "Line"):
                FreeCAD.activeDraftCommand.finish(False)

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Finish',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_FinishLine", "Finish line"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_FinishLine", "Finishes a line without closing it")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False


class CloseLine:
    """a FreeCAD command to close any running Line drawing operation"""

    def Activated(self):
        if (FreeCAD.activeDraftCommand != None):
            if (FreeCAD.activeDraftCommand.featureName == "Line"):
                FreeCAD.activeDraftCommand.finish(True)

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Lock',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_CloseLine", "Close Line"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_CloseLine", "Closes the line being drawn")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False


class UndoLine:
    """a FreeCAD command to undo last drawn segment of a line"""

    def Activated(self):
        if (FreeCAD.activeDraftCommand != None):
            if (FreeCAD.activeDraftCommand.featureName == "Line"):
                FreeCAD.activeDraftCommand.undolast()

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Rotate',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_UndoLine", "Undo last segment"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_UndoLine", "Undoes the last drawn segment of the line being drawn")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False


#---------------------------------------------------------------------------
# Modifier functions
#---------------------------------------------------------------------------

class Modifier(DraftTool):
    """A generic Modifier Tool, used by modification tools such as move"""

    def __init__(self):
        DraftTool.__init__(self)
        self.copymode = False


class ApplyStyle(Modifier):
    """The Draft_ApplyStyle FreeCA command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Apply',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ApplyStyle", "Apply Current Style"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_ApplyStyle", "Applies current line width and color to selected objects")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        Modifier.Activated(self)
        if self.ui:
            self.sel = FreeCADGui.Selection.getSelection()
            if (len(self.sel)>0):
                FreeCADGui.addModule("Draft")
                c = []
                for ob in self.sel:
                    if (ob.Type == "App::DocumentObjectGroup"):
                        c.extend(self.formatGroup(ob))
                    else:
                        c.append('Draft.formatObject(FreeCAD.ActiveDocument.'+ob.Name+')')
                self.commit(translate("draft","Change Style"),c)

    def formatGroup(self,grpob):
        FreeCADGui.addModule("Draft")
        c=[]
        for ob in grpob.Group:
            if (ob.Type == "App::DocumentObjectGroup"):
                c.extend(self.formatGroup(ob))
            else:
                c.append('Draft.formatObject(FreeCAD.ActiveDocument.'+ob.Name+')')


class Stretch(Modifier):
    """The Draft_Stretch FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Stretch',
                'Accel' : "S, H",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Stretch", "Stretch"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Stretch", "Stretches the selected objects")}

    def Activated(self):
        Modifier.Activated(self,"Stretch")
        if self.ui:
            if not FreeCADGui.Selection.getSelection():
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Select an object to stretch")+"\n")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
            else:
                self.proceed()

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        supported = ["Rectangle","Wire","BSpline","BezCurve","Sketch"]
        self.sel = []
        for obj in FreeCADGui.Selection.getSelection():
            if Draft.getType(obj) in supported:
                self.sel.append([obj,FreeCAD.Placement()])
            elif hasattr(obj,"Base"):
                if obj.Base:
                    if Draft.getType(obj.Base) in supported:
                        self.sel.append([obj.Base,obj.Placement])

                    elif Draft.getType(obj.Base) in ["Offset2D","Array"]:
                        base = None
                        if hasattr(obj.Base,"Source") and obj.Base.Source:
                            base = obj.Base.Source
                        elif hasattr(obj.Base,"Base") and obj.Base.Base:
                            base = obj.Base.Base
                        if base:
                            if Draft.getType(base) in supported:
                                self.sel.append([base,obj.Placement.multiply(obj.Base.Placement)])
            elif Draft.getType(obj) in ["Offset2D","Array"]:
                base = None
                if hasattr(obj,"Source") and obj.Source:
                    base = obj.Source
                elif hasattr(obj,"Base") and obj.Base:
                    base = obj.Base
                if base:
                    if Draft.getType(base) in supported:
                        self.sel.append([base,obj.Placement])
        if self.ui and self.sel:
            self.step = 1
            self.refpoint = None
            self.ui.pointUi("Stretch")
            self.ui.extUi()
            self.call = self.view.addEventCallback("SoEvent",self.action)
            self.rectracker = rectangleTracker(dotted=True,scolor=(0.0,0.0,1.0),swidth=2)
            self.nodetracker = []
            self.displacement = None
            FreeCAD.Console.PrintMessage(translate("draft", "Pick first point of selection rectangle")+"\n")

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            point,ctrlPoint,info = getPoint(self,arg) #,mobile=True) #,noTracker=(self.step < 3))
            if self.step == 2:
                self.rectracker.update(point)
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if (arg["Position"] == self.pos):
                    # clicked twice on the same point
                    self.finish()
                else:
                    point,ctrlPoint,info = getPoint(self,arg) #,mobile=True) #,noTracker=(self.step < 3))
                    self.addPoint(point)

    def addPoint(self,point):
        if self.step == 1:
            # first rctangle point
            FreeCAD.Console.PrintMessage(translate("draft", "Pick opposite point of selection rectangle")+"\n")
            self.ui.setRelative()
            self.rectracker.setorigin(point)
            self.rectracker.on()
            if self.planetrack:
                self.planetrack.set(point)
            self.step = 2
        elif self.step == 2:
            # second rectangle point
            FreeCAD.Console.PrintMessage(translate("draft", "Pick start point of displacement")+"\n")
            self.rectracker.off()
            nodes = []
            self.ops = []
            for sel in self.sel:
                o = sel[0]
                vispla = sel[1]
                tp = Draft.getType(o)
                if tp in ["Wire","BSpline","BezCurve"]:
                    np = []
                    iso = False
                    for p in o.Points:
                        p = o.Placement.multVec(p)
                        p = vispla.multVec(p)
                        isi = self.rectracker.isInside(p)
                        np.append(isi)
                        if isi:
                            iso = True
                            nodes.append(p)
                    if iso:
                        self.ops.append([o,np])
                elif tp in ["Rectangle"]:
                    p1 = Vector(0,0,0)
                    p2 = Vector(o.Length.Value,0,0)
                    p3 = Vector(o.Length.Value,o.Height.Value,0)
                    p4 = Vector(0,o.Height.Value,0)
                    np = []
                    iso = False
                    for p in [p1,p2,p3,p4]:
                        p = o.Placement.multVec(p)
                        p = vispla.multVec(p)
                        isi = self.rectracker.isInside(p)
                        np.append(isi)
                        if isi:
                            iso = True
                            nodes.append(p)
                    if iso:
                        self.ops.append([o,np])
                elif tp in ["Sketch"]:
                    np = []
                    iso = False
                    for p in o.Shape.Vertexes:
                        p = vispla.multVec(p.Point)
                        isi = self.rectracker.isInside(p)
                        np.append(isi)
                        if isi:
                            iso = True
                            nodes.append(p)
                    if iso:
                        self.ops.append([o,np])
                else:
                    p = o.Placement.Base
                    p = vispla.multVec(p)
                    if self.rectracker.isInside(p):
                        self.ops.append([o])
                        nodes.append(p)
            for n in nodes:
                nt = editTracker(n,inactive=True)
                nt.on()
                self.nodetracker.append(nt)
            self.step = 3
        elif self.step == 3:
            # first point of displacement line
            FreeCAD.Console.PrintMessage(translate("draft", "Pick end point of displacement")+"\n")
            self.displacement = point
            #print "first point:",point
            self.node = [point]
            self.step = 4
        elif self.step == 4:
            #print "second point:",point
            self.displacement = point.sub(self.displacement)
            self.doStretch()
        if self.point:
            self.ui.redraw()

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        point = Vector(numx,numy,numz)
        self.addPoint(point)

    def finish(self,closed=False):
        if hasattr(self,"rectracker") and self.rectracker:
            self.rectracker.finalize()
        if hasattr(self,"nodetracker") and self.nodetracker:
            for n in self.nodetracker:
                n.finalize()
        Modifier.finish(self)

    def doStretch(self):
        """does the actual stretching"""
        commitops = []
        if self.displacement:
            if self.displacement.Length > 0:
                #print "displacement: ",self.displacement
                for ops in self.ops:
                    tp = Draft.getType(ops[0])
                    localdisp = ops[0].Placement.Rotation.inverted().multVec(self.displacement)
                    if tp in ["Wire","BSpline","BezCurve"]:
                        pts = []
                        for i in range(len(ops[1])):
                            if ops[1][i] == False:
                                pts.append(ops[0].Points[i])
                            else:
                                pts.append(ops[0].Points[i].add(localdisp))
                        pts = str(pts).replace("Vector","FreeCAD.Vector")
                        commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Points="+pts)
                    elif tp in ["Sketch"]:
                        baseverts = [ops[0].Shape.Vertexes[i].Point for i in range(len(ops[1])) if ops[1][i]]
                        for i in range(ops[0].GeometryCount):
                            j = 0
                            while True:
                                try:
                                    p = ops[0].getPoint(i,j)
                                except ValueError:
                                    break
                                else:
                                    p = ops[0].Placement.multVec(p)
                                    r = None
                                    for bv in baseverts:
                                        if DraftVecUtils.isNull(p.sub(bv)):
                                            commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".movePoint("+str(i)+","+str(j)+",FreeCAD."+str(localdisp)+",True)")
                                            r = bv
                                            break
                                    if r:
                                        baseverts.remove(r)
                                    j += 1
                    elif tp in ["Rectangle"]:
                        p1 = Vector(0,0,0)
                        p2 = Vector(ops[0].Length.Value,0,0)
                        p3 = Vector(ops[0].Length.Value,ops[0].Height.Value,0)
                        p4 = Vector(0,ops[0].Height.Value,0)
                        if ops[1] == [False,True,True,False]:
                            optype = 1
                        elif ops[1] == [False,False,True,True]:
                            optype = 2
                        elif ops[1] == [True,False,False,True]:
                            optype = 3
                        elif ops[1] == [True,True,False,False]:
                            optype = 4
                        else:
                            optype = 0
                        #print("length:",ops[0].Length,"height:",ops[0].Height," - ",ops[1]," - ",self.displacement)
                        done = False
                        if optype > 0:
                            v1 = ops[0].Placement.multVec(p2).sub(ops[0].Placement.multVec(p1))
                            a1 = round(self.displacement.getAngle(v1),4)
                            v2 = ops[0].Placement.multVec(p4).sub(ops[0].Placement.multVec(p1))
                            a2 = round(self.displacement.getAngle(v2),4)
                            # check if the displacement is along one of the rectangle directions
                            if a1 == 0:
                                if optype == 1:
                                    if ops[0].Length.Value >= 0:
                                        d = ops[0].Length.Value + self.displacement.Length
                                    else:
                                        d = ops[0].Length.Value - self.displacement.Length
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Length="+str(d))
                                    done = True
                                elif optype == 3:
                                    if ops[0].Length.Value >= 0:
                                        d = ops[0].Length.Value - self.displacement.Length
                                    else:
                                        d = ops[0].Length.Value + self.displacement.Length
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Length="+str(d))
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Placement.Base=FreeCAD."+str(ops[0].Placement.Base.add(self.displacement)))
                                    done = True
                            elif a1 == 3.1416:
                                if optype == 1:
                                    if ops[0].Length.Value >= 0:
                                        d = ops[0].Length.Value - self.displacement.Length
                                    else:
                                        d = ops[0].Length.Value + self.displacement.Length
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Length="+str(d))
                                    done = True
                                elif optype == 3:
                                    if ops[0].Length.Value >= 0:
                                        d = ops[0].Length.Value + self.displacement.Length
                                    else:
                                        d = ops[0].Length.Value - self.displacement.Length
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Length="+str(d))
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Placement.Base=FreeCAD."+str(ops[0].Placement.Base.add(self.displacement)))
                                    done = True
                            elif a2 == 0:
                                if optype == 2:
                                    if ops[0].Height.Value >= 0:
                                        d = ops[0].Height.Value + self.displacement.Length
                                    else:
                                        d = ops[0].Height.Value - self.displacement.Length
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Height="+str(d))
                                    done = True
                                elif optype == 4:
                                    if ops[0].Height.Value >= 0:
                                        d = ops[0].Height.Value - self.displacement.Length
                                    else:
                                        d = ops[0].Height.Value + self.displacement.Length
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Height="+str(d))
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Placement.Base=FreeCAD."+str(ops[0].Placement.Base.add(self.displacement)))
                                    done = True
                            elif a2 == 3.1416:
                                if optype == 2:
                                    if ops[0].Height.Value >= 0:
                                        d = ops[0].Height.Value - self.displacement.Length
                                    else:
                                        d = ops[0].Height.Value + self.displacement.Length
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Height="+str(d))
                                    done = True
                                elif optype == 4:
                                    if ops[0].Height.Value >= 0:
                                        d = ops[0].Height.Value + self.displacement.Length
                                    else:
                                        d = ops[0].Height.Value - self.displacement.Length
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Height="+str(d))
                                    commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Placement.Base=FreeCAD."+str(ops[0].Placement.Base.add(self.displacement)))
                                    done = True
                        if not done:
                            # otherwise create a wire copy and stretch it instead
                            FreeCAD.Console.PrintMessage(translate("draft","Turning one Rectangle into a Wire")+"\n")
                            pts = []
                            opts = [p1,p2,p3,p4]
                            for i in range(4):
                                if ops[1][i] == False:
                                    pts.append(opts[i])
                                else:
                                    pts.append(opts[i].add(self.displacement))
                            pts = str(pts).replace("Vector","FreeCAD.Vector")
                            commitops.append("w = Draft.makeWire("+pts+",closed=True)")
                            commitops.append("Draft.formatObject(w,FreeCAD.ActiveDocument."+ops[0].Name+")")
                            commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".ViewObject.hide()")
                            for par in ops[0].InList:
                                if hasattr(par,"Base") and par.Base == ops[0]:
                                    commitops.append("FreeCAD.ActiveDocument."+par.Name+".Base = w")
                    else:
                        commitops.append("FreeCAD.ActiveDocument."+ops[0].Name+".Placement.Base=FreeCAD."+str(ops[0].Placement.Base.add(self.displacement)))
        if commitops:
            commitops.append("FreeCAD.ActiveDocument.recompute()")
            FreeCADGui.addModule("Draft")
            self.commit(translate("draft","Stretch"),commitops)
        self.finish()


class ToggleConstructionMode():
    """The Draft_ToggleConstructionMode FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Construction',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleConstructionMode", "Toggle Construction Mode"),
                'Accel' : "C, M",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleConstructionMode", "Toggles the Construction Mode for next objects.")}

    def Activated(self):
        FreeCADGui.draftToolBar.constrButton.toggle()


class ToggleContinueMode():
    """The Draft_ToggleContinueMode FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Rotate',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleContinueMode", "Toggle Continue Mode"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleContinueMode", "Toggles the Continue Mode for next commands.")}

    def Activated(self):
        FreeCADGui.draftToolBar.toggleContinue()


class ToggleDisplayMode():
    """The ToggleDisplayMode FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_SwitchMode',
                'Accel' : "Shift+Space",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleDisplayMode", "Toggle display mode"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_ToggleDisplayMode", "Swaps display mode of selected objects between wireframe and flatlines")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        for obj in FreeCADGui.Selection.getSelection():
            if obj.ViewObject.DisplayMode == "Flat Lines":
                if "Wireframe" in obj.ViewObject.listDisplayModes():
                    obj.ViewObject.DisplayMode = "Wireframe"
            elif obj.ViewObject.DisplayMode == "Wireframe":
                if "Flat Lines" in obj.ViewObject.listDisplayModes():
                    obj.ViewObject.DisplayMode = "Flat Lines"

class SubelementModify(Modifier):
    """The Draft_SubelementModify FreeCAD command definition"""

    def __init__(self):
        self.is_running = False
        self.editable_objects = []
        self.original_view_settings = {}

    def GetResources(self):
        return {'Pixmap'  : 'Draft_SubelementModify',
                'Accel' : "D, E",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_SubelementModify", "Subelement modify"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_SubelementModify",
                                                    "Allows editing the subelements "
                                                    "of the selected objects with other modification tools")}

    def Activated(self):
        if self.is_running:
            return self.finish()
        self.is_running = True
        Modifier.Activated(self, "SubelementModify")
        self.get_selection()

    def proceed(self):
        self.remove_view_callback()
        self.get_editable_objects_from_selection()
        if not self.editable_objects:
            return self.finish()
        self.call = self.view.addEventCallback("SoEvent", self.action)
        self.highlight_editable_objects()

    def finish(self):
        Modifier.finish(self)
        self.remove_view_callback()
        self.restore_editable_objects_graphics()
        self.__init__()

    def action(self, event):
        if event["Type"] == "SoKeyboardEvent" and event["Key"] == "ESCAPE":
            self.finish()

    def get_selection(self):
        if not FreeCADGui.Selection.getSelection() and self.ui:
            FreeCAD.Console.PrintMessage(translate("draft", "Select an object to edit")+"\n")
            self.call = self.view.addEventCallback("SoEvent", selectObject)
        else:
            self.proceed()

    def remove_view_callback(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)

    def get_editable_objects_from_selection(self):
        for object in FreeCADGui.Selection.getSelection():
            if object.isDerivedFrom("Part::Part2DObject"):
                self.editable_objects.append(object)
            elif hasattr(object, "Base") and object.Base.isDerivedFrom("Part::Part2DObject"):
                self.editable_objects.append(object.Base)

    def highlight_editable_objects(self):
        for object in self.editable_objects:
            self.original_view_settings[object.Name] = {
                'Visibility': object.ViewObject.Visibility,
                'PointSize': object.ViewObject.PointSize,
                'PointColor': object.ViewObject.PointColor,
                'LineColor': object.ViewObject.LineColor
            }
            object.ViewObject.Visibility = True
            object.ViewObject.PointSize = 10
            object.ViewObject.PointColor = (1., 0., 0.)
            object.ViewObject.LineColor = (1., 0., 0.)
            xray = coin.SoAnnotation()
            xray.addChild(object.ViewObject.RootNode.getChild(2).getChild(0))
            xray.setName("xray")
            object.ViewObject.RootNode.addChild(xray)

    def restore_editable_objects_graphics(self):
        for object in self.editable_objects:
            try:
                for attribute, value in self.original_view_settings[object.Name].items():
                    view_object = object.ViewObject
                    setattr(view_object, attribute, value)
                    view_object.RootNode.removeChild(view_object.RootNode.getByName("xray"))
            except:
                # This can occur if objects have had graph changing operations
                pass

class AddToGroup():
    """The AddToGroup FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_AddToGroup',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_AddToGroup", "Move to group..."),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_AddToGroup", "Moves the selected object(s) to an existing group")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        self.groups = ["Ungroup"]
        self.groups.extend(Draft.getGroupNames())
        self.labels = ["Ungroup"]
        for g in self.groups:
            o = FreeCAD.ActiveDocument.getObject(g)
            if o: self.labels.append(o.Label)
        self.ui = FreeCADGui.draftToolBar
        self.ui.sourceCmd = self
        self.ui.popupMenu(self.labels)

    def proceed(self,labelname):
        self.ui.sourceCmd = None
        if labelname == "Ungroup":
            for obj in FreeCADGui.Selection.getSelection():
                try:
                    Draft.ungroup(obj)
                except:
                    pass
        else:
            if labelname in self.labels:
                i = self.labels.index(labelname)
                g = FreeCAD.ActiveDocument.getObject(self.groups[i])
                for obj in FreeCADGui.Selection.getSelection():
                    try:
                        g.addObject(obj)
                    except:
                        pass


class AddPoint(Modifier):
    """The Draft_AddPoint FreeCAD command definition"""

    def __init__(self):
        self.running = False

    def GetResources(self):
        return {'Pixmap'  : 'Draft_AddPoint',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_AddPoint", "Add Point"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_AddPoint", "Adds a point to an existing Wire or B-spline")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
        if selection:
            if (Draft.getType(selection[0]) in ['Wire','BSpline']):
                FreeCADGui.runCommand("Draft_Edit")
                FreeCADGui.draftToolBar.vertUi(True)


class DelPoint(Modifier):
    """The Draft_DelPoint FreeCAD command definition"""

    def __init__(self):
        self.running = False

    def GetResources(self):
        return {'Pixmap'  : 'Draft_DelPoint',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_DelPoint", "Remove Point"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_DelPoint", "Removes a point from an existing Wire or B-spline")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
        if selection:
            if (Draft.getType(selection[0]) in ['Wire','BSpline']):
                FreeCADGui.runCommand("Draft_Edit")
                FreeCADGui.draftToolBar.vertUi(False)


class WireToBSpline(Modifier):
    """The Draft_Wire2BSpline FreeCAD command definition"""

    def __init__(self):
        self.running = False

    def GetResources(self):
        return {'Pixmap'  : 'Draft_WireToBSpline',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_WireToBSpline", "Wire to B-spline"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_WireToBSpline", "Converts between Wire and B-spline")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        if self.running:
            self.finish()
        else:
            selection = FreeCADGui.Selection.getSelection()
            if selection:
                if (Draft.getType(selection[0]) in ['Wire','BSpline']):
                    Modifier.Activated(self,"Convert Curve Type")
                    if self.doc:
                        self.obj = FreeCADGui.Selection.getSelection()
                        if self.obj:
                            self.obj = self.obj[0]
                            self.pl = None
                            if "Placement" in self.obj.PropertiesList:
                                self.pl = self.obj.Placement
                            self.Points = self.obj.Points
                            self.closed = self.obj.Closed
                            n = None
                            if (Draft.getType(self.obj) == 'Wire'):
                                n = Draft.makeBSpline(self.Points, self.closed, self.pl)
                            elif (Draft.getType(self.obj) == 'BSpline'):
                                n = Draft.makeWire(self.Points, self.closed, self.pl)
                            if n:
                                Draft.formatObject(n,self.obj)
                                self.doc.recompute()
                        else:
                            self.finish()


class SelectGroup():
    """The SelectGroup FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_SelectGroup',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_SelectGroup", "Select group"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_SelectGroup", "Selects all objects with the same parents as this group")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        sellist = []
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            if sel[0].isDerivedFrom("App::DocumentObjectGroup"):
                cts = Draft.getGroupContents(FreeCADGui.Selection.getSelection())
                for o in cts:
                    FreeCADGui.Selection.addSelection(o)
                return
        for ob in sel:
            for child in ob.OutList:
                FreeCADGui.Selection.addSelection(child)
            for parent in ob.InList:
                FreeCADGui.Selection.addSelection(parent)
                for child in parent.OutList:
                    FreeCADGui.Selection.addSelection(child)


class ShowSnapBar():
    """The ShowSnapBar FreeCAD command definition"""

    def GetResources(self):
        return {'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ShowSnapBar", "Show Snap Bar"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_ShowSnapBar", "Shows Draft snap toolbar")}

    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.show()


class ToggleGrid():
    """The Draft ToggleGrid command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Grid',
                'Accel' : "G,R",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleGrid", "Toggle Grid"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_ToggleGrid", "Toggles the Draft grid on/off")}

    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.setTrackers()
            if FreeCADGui.Snapper.grid:
                if FreeCADGui.Snapper.grid.Visible:
                    FreeCADGui.Snapper.grid.off()
                    FreeCADGui.Snapper.forceGridOff=True
                else:
                    FreeCADGui.Snapper.grid.on()
                    FreeCADGui.Snapper.forceGridOff=False


class Draft_FlipDimension():
    def GetResources(self):
        return {'Pixmap'  : 'Draft_FlipDimension',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_FlipDimension", "Flip Dimension"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_FlipDimension", "Flip the normal direction of a dimension")}

    def Activated(self):
        for o in FreeCADGui.Selection.getSelection():
            if Draft.getType(o) in ["Dimension","AngularDimension"]:
                FreeCAD.ActiveDocument.openTransaction("Flip dimension")
                FreeCADGui.doCommand("FreeCAD.ActiveDocument."+o.Name+".Normal = FreeCAD.ActiveDocument."+o.Name+".Normal.negative()")
                FreeCAD.ActiveDocument.commitTransaction()
                FreeCAD.ActiveDocument.recompute()


class Draft_Slope():

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Slope',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Slope", "Set Slope"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Slope", "Sets the slope of a selected Line or Wire")}

    def Activated(self):
        if not FreeCADGui.Selection.getSelection():
            return
        for obj in FreeCADGui.Selection.getSelection():
            if Draft.getType(obj) != "Wire":
                FreeCAD.Console.PrintMessage(translate("draft", "This tool only works with Wires and Lines")+"\n")
                return
        w = QtGui.QWidget()
        w.setWindowTitle(translate("Draft","Slope"))
        layout = QtGui.QHBoxLayout(w)
        label = QtGui.QLabel(w)
        label.setText(translate("Draft", "Slope")+":")
        layout.addWidget(label)
        self.spinbox = QtGui.QDoubleSpinBox(w)
        self.spinbox.setMinimum(-9999.99)
        self.spinbox.setMaximum(9999.99)
        self.spinbox.setSingleStep(0.01)
        self.spinbox.setToolTip(translate("Draft", "Slope to give selected Wires/Lines: 0 = horizontal, 1 = 45deg up, -1 = 45deg down"))
        layout.addWidget(self.spinbox)
        taskwidget = QtGui.QWidget()
        taskwidget.form = w
        taskwidget.accept = self.accept
        FreeCADGui.Control.showDialog(taskwidget)

    def accept(self):
        if hasattr(self,"spinbox"):
            pc = self.spinbox.value()
            FreeCAD.ActiveDocument.openTransaction("Change slope")
            for obj in FreeCADGui.Selection.getSelection():
                if Draft.getType(obj) == "Wire":
                    if len(obj.Points) > 1:
                        lp = None
                        np = []
                        for p in obj.Points:
                            if not lp:
                                lp = p
                            else:
                                v = p.sub(lp)
                                z = pc*FreeCAD.Vector(v.x,v.y,0).Length
                                lp = FreeCAD.Vector(p.x,p.y,lp.z+z)
                            np.append(lp)
                        obj.Points = np
            FreeCAD.ActiveDocument.commitTransaction()
        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()


class SetAutoGroup():
    """The SetAutoGroup FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_AutoGroup',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_AutoGroup", "AutoGroup"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_AutoGroup", "Select a group to automatically add all Draft & Arch objects to")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        if hasattr(FreeCADGui,"draftToolBar"):
            self.ui = FreeCADGui.draftToolBar
            s = FreeCADGui.Selection.getSelection()
            if len(s) == 1:
                if (Draft.getType(s[0]) == "Layer") or \
                ( FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/BIM").GetBool("AutogroupAddGroups",False) and \
                (s[0].isDerivedFrom("App::DocumentObjectGroup") or (Draft.getType(s[0]) in ["Site","Building","Floor","BuildingPart",]))):
                    self.ui.setAutoGroup(s[0].Name)
                    return
            self.groups = ["None"]
            gn = [o.Name for o in FreeCAD.ActiveDocument.Objects if Draft.getType(o) == "Layer"]
            if FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/BIM").GetBool("AutogroupAddGroups",False):
                gn.extend(Draft.getGroupNames())
            if gn:
                self.groups.extend(gn)
                self.labels = [translate("draft","None")]
                self.icons = [self.ui.getIcon(":/icons/button_invalid.svg")]
                for g in gn:
                    o = FreeCAD.ActiveDocument.getObject(g)
                    if o:
                        self.labels.append(o.Label)
                        self.icons.append(o.ViewObject.Icon)
                self.labels.append(translate("draft","Add new Layer"))
                self.icons.append(self.ui.getIcon(":/icons/document-new.svg"))
                self.ui.sourceCmd = self
                from PySide import QtCore
                pos = self.ui.autoGroupButton.mapToGlobal(QtCore.QPoint(0,self.ui.autoGroupButton.geometry().height()))
                self.ui.popupMenu(self.labels,self.icons,pos)

    def proceed(self,labelname):
        self.ui.sourceCmd = None
        if labelname in self.labels:
            if labelname == self.labels[0]:
                self.ui.setAutoGroup(None)
            elif labelname == self.labels[-1]:
                FreeCADGui.runCommand("Draft_Layer")
            else:
                i = self.labels.index(labelname)
                self.ui.setAutoGroup(self.groups[i])


class Draft_AddConstruction():

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Construction',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_AddConstruction", "Add to Construction group"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_AddConstruction", "Adds the selected objects to the Construction group")}

    def Activated(self):
        import FreeCADGui
        if hasattr(FreeCADGui,"draftToolBar"):
            col = FreeCADGui.draftToolBar.getDefaultColor("constr")
            col = (float(col[0]),float(col[1]),float(col[2]),0.0)
            gname = Draft.getParam("constructiongroupname","Construction")
            grp = FreeCAD.ActiveDocument.getObject(gname)
            if not grp:
                grp = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup",gname)
            for obj in FreeCADGui.Selection.getSelection():
                grp.addObject(obj)
                obrep = obj.ViewObject
                if "TextColor" in obrep.PropertiesList:
                    obrep.TextColor = col
                if "PointColor" in obrep.PropertiesList:
                    obrep.PointColor = col
                if "LineColor" in obrep.PropertiesList:
                    obrep.LineColor = col
                if "ShapeColor" in obrep.PropertiesList:
                    obrep.ShapeColor = col
                if hasattr(obrep,"Transparency"):
                    obrep.Transparency = 80



#---------------------------------------------------------------------------
# Snap tools
#---------------------------------------------------------------------------








class Draft_Snap_Endpoint():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Endpoint',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Endpoint", "Endpoint"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Endpoint", "Snaps to endpoints of edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonendpoint":
                        b.toggle()

class Draft_Snap_Angle():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Angle',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Angle", "Angles"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Angle", "Snaps to 45 and 90 degrees points on arcs and circles")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonangle":
                        b.toggle()

class Draft_Snap_Center():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Center',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Center", "Center"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Center", "Snaps to center of circles and arcs")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtoncenter":
                        b.toggle()

class Draft_Snap_Extension():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Extension',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Extension", "Extension"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Extension", "Snaps to extension of edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonextension":
                        b.toggle()

class Draft_Snap_Near():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Near',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Near", "Nearest"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Near", "Snaps to nearest point on edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonpassive":
                        b.toggle()

class Draft_Snap_Ortho():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Ortho',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Ortho", "Ortho"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Ortho", "Snaps to orthogonal and 45 degrees directions")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonortho":
                        b.toggle()

class Draft_Snap_Special():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Special',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Special", "Special"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Special", "Snaps to special locations of objects")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonspecial":
                        b.toggle()

class Draft_Snap_Dimensions():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Dimensions',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Dimensions", "Dimensions"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Dimensions", "Shows temporary dimensions when snapping to Arch objects")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonDimensions":
                        b.toggle()

class Draft_Snap_WorkingPlane():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_WorkingPlane',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_WorkingPlane", "Working Plane"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_WorkingPlane", "Restricts the snapped point to the current working plane")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonWorkingPlane":
                        b.toggle()

#---------------------------------------------------------------------------
# Adds the icons & commands to the FreeCAD command manager, and sets defaults
#---------------------------------------------------------------------------

# drawing commands


















# modification commands










FreeCADGui.addCommand('Draft_Edit_Improved',EditImproved())
FreeCADGui.addCommand('Draft_AddPoint',AddPoint())
FreeCADGui.addCommand('Draft_DelPoint',DelPoint())
FreeCADGui.addCommand('Draft_WireToBSpline',WireToBSpline())







FreeCADGui.addCommand('Draft_Slope',Draft_Slope())
FreeCADGui.addCommand('Draft_Stretch',Stretch())

# context commands
FreeCADGui.addCommand('Draft_FinishLine',FinishLine())
FreeCADGui.addCommand('Draft_CloseLine',CloseLine())
FreeCADGui.addCommand('Draft_UndoLine',UndoLine())
FreeCADGui.addCommand('Draft_ToggleConstructionMode',ToggleConstructionMode())
FreeCADGui.addCommand('Draft_ToggleContinueMode',ToggleContinueMode())
FreeCADGui.addCommand('Draft_ApplyStyle',ApplyStyle())
FreeCADGui.addCommand('Draft_ToggleDisplayMode',ToggleDisplayMode())
FreeCADGui.addCommand('Draft_AddToGroup',AddToGroup())
FreeCADGui.addCommand('Draft_SelectGroup',SelectGroup())

FreeCADGui.addCommand('Draft_ShowSnapBar',ShowSnapBar())
FreeCADGui.addCommand('Draft_ToggleGrid',ToggleGrid())
FreeCADGui.addCommand('Draft_FlipDimension',Draft_FlipDimension())
FreeCADGui.addCommand('Draft_AutoGroup',SetAutoGroup())

FreeCADGui.addCommand('Draft_AddConstruction',Draft_AddConstruction())

# snap commands


FreeCADGui.addCommand('Draft_Snap_Endpoint',Draft_Snap_Endpoint())
FreeCADGui.addCommand('Draft_Snap_Angle',Draft_Snap_Angle())
FreeCADGui.addCommand('Draft_Snap_Center',Draft_Snap_Center())
FreeCADGui.addCommand('Draft_Snap_Extension',Draft_Snap_Extension())
FreeCADGui.addCommand('Draft_Snap_Near',Draft_Snap_Near())
FreeCADGui.addCommand('Draft_Snap_Ortho',Draft_Snap_Ortho())
FreeCADGui.addCommand('Draft_Snap_Special',Draft_Snap_Special())
FreeCADGui.addCommand('Draft_Snap_Dimensions',Draft_Snap_Dimensions())
FreeCADGui.addCommand('Draft_Snap_WorkingPlane',Draft_Snap_WorkingPlane())

# a global place to look for active draft Command
FreeCAD.activeDraftCommand = None
