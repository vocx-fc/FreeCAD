# -*- coding: utf-8 -*-
## \package DraftLine
# \ingroup DRAFT
# \brief This module contains everything related to Drat Line tool.
"""\package DraftLine
\ingroup DRAFT
\brief This module contains everything related to Drat Line tool.
"""
# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2009, 2010                                              *
# *   Yorik van Havre <yorik@uncreated.net>, Ken Cline <cline@frii.com>     *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import FreeCAD
from FreeCAD import Vector
from FreeCAD import Console as FCC
import sys
import Part
from Draft import makeWire
from Draft import formatObject
from Draft import tolerance
from Draft import getParam
from DraftTools import getPoint
from DraftTools import redraw3DView
from DraftTools import getSupport
from DraftGui import todo
from DraftTools import Creator
import DraftVecUtils

if FreeCAD.GuiUp:
    import FreeCADGui
    import Draft_rc
    from PySide.QtCore import QT_TRANSLATE_NOOP
    from DraftTools import translate
else:
    def QT_TRANSLATE_NOOP(context, txt):
        return txt

    def translate(context, txt):
        return txt


def makeLine(p1, p2=None):
    """Create a line between two points.

    Parameters
    ----------
    p1 : Base::Vector3, or Part.Edge, or Part.Shape
        The first point of the line; or a Part.Edge or Part.Shape,
        as long as `p2=None`.
    p2 : Base::Vector3, optional
        It defaults to `None`. The second point.

    Returns
    -------
    Part::Part2DObjectPython
        The returned line object.

    Notes
    -----
    Internally it checks the arguments and calls `makeWire([p1, p2])`.

    If `p2=None`, the first argument should be either an `Edge`
    or a `Shape`.
    Then it will use the `StartPoint` and `EndPoint`
    of the `Edge`, or it will use the first and last vertices
    of the given `Shape`.
    ::
        obj = makeLine(Edge)
        obj = makeLine(Shape)

    """
    if not p2:
        if hasattr(p1, "StartPoint") and hasattr(p1, "EndPoint"):
            p2 = p1.EndPoint
            p1 = p1.StartPoint
        elif hasattr(p1, "Vertexes"):
            p2 = p1.Vertexes[-1].Point
            p1 = p1.Vertexes[0].Point
        else:
            FCC.PrintError("Unable to create a line from the given data\n")
            return
    obj = makeWire([p1, p2])
    return obj

# Normally there would be a _Line class defining the object.
# However, a _Line is just a _Wire with two points, so no new object
# is defined.
# class Line:
# _Line = _Wire

# Normally there would be _ViewProviderLine for the _Line object.
# However, since a _Line is just a _Wire, it uses the same ViewProvider
# as this object.
# class _ViewProviderLine:
# _ViewProviderLine = _ViewProviderWire


class Line(Creator):
    "The Line FreeCAD command definition"

    def __init__(self, wiremode=False):
        Creator.__init__(self)
        self.isWire = wiremode

    def GetResources(self):
        return {'Pixmap': 'Draft_Line',
                'Accel': "L,I",
                'MenuText': QT_TRANSLATE_NOOP("Draft_Line", "Line"),
                'ToolTip': QT_TRANSLATE_NOOP("Draft_Line", "Creates a 2-point line. CTRL to snap, SHIFT to constrain")}

    def Activated(self, name=translate("draft", "Line")):
        Creator.Activated(self, name)
        if not self.doc:
            return
        self.obj = None  # stores the temp shape
        self.oldWP = None  # stores the WP if we modify it
        if self.isWire:
            self.ui.wireUi(name)
        else:
            self.ui.lineUi(name)
        self.ui.setTitle(translate("draft", "Line"))
        if sys.version_info.major < 3:
            if isinstance(self.featureName, unicode):
                self.featureName = self.featureName.encode("utf8")
        self.obj = self.doc.addObject("Part::Feature", self.featureName)
        formatObject(self.obj)
        self.call = self.view.addEventCallback("SoEvent", self.action)
        FreeCAD.Console.PrintMessage(translate("draft", "Pick first point")+"\n")

    def action(self, arg):
        "scene event handler"
        if arg["Type"] == "SoKeyboardEvent" and arg["Key"] == "ESCAPE":
            self.finish()
        elif arg["Type"] == "SoLocation2Event":
            self.point, ctrlPoint, info = getPoint(self, arg)
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent" and \
            arg["State"] == "DOWN" and \
            arg["Button"] == "BUTTON1":
                if (arg["Position"] == self.pos):
                    return self.finish(False, cont=True)
                if (not self.node) and (not self.support):
                    getSupport(arg)
                    self.point, ctrlPoint, info = getPoint(self, arg)
                if self.point:
                    self.ui.redraw()
                    self.pos = arg["Position"]
                    self.node.append(self.point)
                    self.drawSegment(self.point)
                    if (not self.isWire and len(self.node) == 2):
                        self.finish(False, cont=True)
                    if (len(self.node) > 2):
                        if ((self.point-self.node[0]).Length < tolerance()):
                            self.undolast()
                            self.finish(True, cont=True)

    def finish(self, closed=False, cont=False):
        "terminates the operation and closes the poly if asked"
        self.removeTemporaryObject()
        if self.oldWP:
            FreeCAD.DraftWorkingPlane = self.oldWP
            if hasattr(FreeCADGui, "Snapper"):
                FreeCADGui.Snapper.setGrid()
                FreeCADGui.Snapper.restack()
        self.oldWP = None
        if (len(self.node) > 1):
            FreeCADGui.addModule("Draft")
            if (len(self.node) == 2) and getParam("UsePartPrimitives", False):
                # use Part primitive
                p1 = self.node[0]
                p2 = self.node[-1]
                self.commit(translate("draft", "Create Line"),
                            ['line = FreeCAD.ActiveDocument.addObject("Part::Line","Line")',
                             'line.X1 = '+str(p1.x),
                             'line.Y1 = '+str(p1.y),
                             'line.Z1 = '+str(p1.z),
                             'line.X2 = '+str(p2.x),
                             'line.Y2 = '+str(p2.y),
                             'line.Z2 = '+str(p2.z),
                             'Draft.autogroup(line)',
                             'FreeCAD.ActiveDocument.recompute()'])
            else:
                # building command string
                rot, sup, pts, fil = self.getStrings()
                self.commit(translate("draft","Create Wire"),
                            ['pl = FreeCAD.Placement()',
                             'pl.Rotation.Q = '+rot,
                             'pl.Base = '+DraftVecUtils.toString(self.node[0]),
                             'points = '+pts,
                             'line = Draft.makeWire(points,placement=pl,closed='+str(closed)+',face='+fil+',support='+sup+')',
                             'Draft.autogroup(line)',
                             'FreeCAD.ActiveDocument.recompute()'])
        Creator.finish(self)
        if self.ui and self.ui.continueMode:
            self.Activated()

    def removeTemporaryObject(self):
        if self.obj:
            try:
                old = self.obj.Name
            except ReferenceError:
                # object already deleted, for some reason
                pass
            else:
                todo.delay(self.doc.removeObject, old)
        self.obj = None

    def undolast(self):
        "undoes last line segment"
        if (len(self.node) > 1):
            self.node.pop()
            last = self.node[-1]
            if self.obj.Shape.Edges:
                edges = self.obj.Shape.Edges
                if len(edges) > 1:
                    newshape = Part.makePolygon(self.node)
                    self.obj.Shape = newshape
                else:
                    self.obj.ViewObject.hide()
                # DNC: report on removal
                #FreeCAD.Console.PrintMessage(translate("draft", "Removing last point")+"\n")
                FCC.PrintMessage(translate("draft", "Pick next point")+"\n")

    def drawSegment(self, point):
        "draws a new segment"
        if self.planetrack and self.node:
            self.planetrack.set(self.node[-1])
        if (len(self.node) == 1):
            FCC.PrintMessage(translate("draft", "Pick next point")+"\n")
        elif (len(self.node) == 2):
            last = self.node[len(self.node)-2]
            newseg = Part.LineSegment(last, point).toShape()
            self.obj.Shape = newseg
            self.obj.ViewObject.Visibility = True
            if self.isWire:
                FCC.PrintMessage(translate("draft", "Pick next point")+"\n")
        else:
            currentshape = self.obj.Shape.copy()
            last = self.node[len(self.node)-2]
            if not DraftVecUtils.equals(last, point):
                newseg = Part.LineSegment(last, point).toShape()
                newshape = currentshape.fuse(newseg)
                self.obj.Shape = newshape
            FCC.PrintMessage(translate("draft", "Pick next point")+"\n")

    def wipe(self):
        "removes all previous segments and starts from last point"
        if len(self.node) > 1:
            # self.obj.Shape.nullify() - for some reason this fails
            self.obj.ViewObject.Visibility = False
            self.node = [self.node[-1]]
            if self.planetrack:
                self.planetrack.set(self.node[0])
            FCC.PrintMessage(translate("draft", "Pick next point")+"\n")

    def orientWP(self):
        if hasattr(FreeCAD, "DraftWorkingPlane"):
            if (len(self.node) > 1) and self.obj:
                import DraftGeomUtils
                n = DraftGeomUtils.getNormal(self.obj.Shape)
                if not n:
                    n = FreeCAD.DraftWorkingPlane.axis
                p = self.node[-1]
                v = self.node[-2].sub(self.node[-1])
                v = v.negative()
                if not self.oldWP:
                    self.oldWP = FreeCAD.DraftWorkingPlane.copy()
                FreeCAD.DraftWorkingPlane.alignToPointAndAxis(p, n, upvec=v)
                if hasattr(FreeCADGui, "Snapper"):
                    FreeCADGui.Snapper.setGrid()
                    FreeCADGui.Snapper.restack()
                if self.planetrack:
                    self.planetrack.set(self.node[-1])

    def numericInput(self, numx, numy, numz):
        "this function gets called by the toolbar when valid x, y, and z have been entered there"
        self.point = Vector(numx, numy, numz)
        self.node.append(self.point)
        self.drawSegment(self.point)
        if (not self.isWire and len(self.node) == 2):
            self.finish(False, cont=True)
        self.ui.setNextFocus()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Line', Line())
