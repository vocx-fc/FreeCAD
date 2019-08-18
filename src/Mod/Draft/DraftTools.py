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





#---------------------------------------------------------------------------
# Modifier functions
#---------------------------------------------------------------------------







#---------------------------------------------------------------------------
# Snap tools
#---------------------------------------------------------------------------











#---------------------------------------------------------------------------
# Adds the icons & commands to the FreeCAD command manager, and sets defaults
#---------------------------------------------------------------------------

# drawing commands


















# modification commands





















# context commands










# snap commands






# a global place to look for active draft Command
FreeCAD.activeDraftCommand = None
