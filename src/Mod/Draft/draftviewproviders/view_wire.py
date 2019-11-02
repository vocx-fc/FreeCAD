"""This module provides the view provider code for Draft Wire.
"""
## @package view_wire
# \ingroup DRAFT
# \brief This module provides the view provider code for Draft Wire.

# ***************************************************************************
# *   Copyright (c) 2009, 2010 Yorik van Havre <yorik@uncreated.net>        *
# *   Copyright (c) 2009, 2010 Ken Cline <cline@frii.com>                   *
# *   Copyright (c) 2019 Eliud Cabrera Castillo <e.cabrera-castillo@tum.de> *
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

import FreeCAD as App
import Draft
import Draft_rc
import draftviewproviders.view_base

_ViewProviderDraft = draftviewproviders.view_base.ViewProviderDraft

# So the resource file doesn't trigger errors from code checkers (flake8)
True if Draft_rc.__name__ else False


class ViewProviderWire(_ViewProviderDraft):
    """A View Provider for the Wire object"""
    def __init__(self, obj):
        _ViewProviderDraft.__init__(self, obj)
        obj.addProperty("App::PropertyBool","EndArrow","Draft",QT_TRANSLATE_NOOP("App::Property","Displays a Dimension symbol at the end of the wire"))
        obj.addProperty("App::PropertyLength","ArrowSize","Draft",QT_TRANSLATE_NOOP("App::Property","Arrow size"))
        obj.addProperty("App::PropertyEnumeration","ArrowType","Draft",QT_TRANSLATE_NOOP("App::Property","Arrow type"))
        obj.ArrowSize = getParam("arrowsize",0.1)
        obj.ArrowType = arrowtypes
        obj.ArrowType = arrowtypes[getParam("dimsymbol", 0)]

    def attach(self, obj):
        from pivy import coin
        self.Object = obj.Object
        col = coin.SoBaseColor()
        col.rgb.setValue(obj.LineColor[0],obj.LineColor[1],obj.LineColor[2])
        self.coords = coin.SoTransform()
        self.pt = coin.SoSeparator()
        self.pt.addChild(col)
        self.pt.addChild(self.coords)
        self.symbol = dimSymbol()
        self.pt.addChild(self.symbol)
        _ViewProviderDraft.attach(self,obj)
        self.onChanged(obj,"EndArrow")

    def updateData(self, obj, prop):
        from pivy import coin
        if prop == "Points":
            if obj.Points:
                p = obj.Points[-1]
                if hasattr(self,"coords"):
                    self.coords.translation.setValue((p.x,p.y,p.z))
                    if len(obj.Points) >= 2:
                        v1 = obj.Points[-2].sub(obj.Points[-1])
                        if not DraftVecUtils.isNull(v1):
                            v1.normalize()
                            _rot = coin.SbRotation()
                            _rot.setValue(coin.SbVec3f(1, 0, 0), coin.SbVec3f(v1[0], v1[1], v1[2]))
                            self.coords.rotation.setValue(_rot)
        return

    def onChanged(self, vobj, prop):
        from pivy import coin
        if prop in ["EndArrow","ArrowSize","ArrowType","Visibility"]:
            rn = vobj.RootNode
            if hasattr(self,"pt") and hasattr(vobj,"EndArrow"):
                if vobj.EndArrow and vobj.Visibility:
                    self.pt.removeChild(self.symbol)
                    s = arrowtypes.index(vobj.ArrowType)
                    self.symbol = dimSymbol(s)
                    self.pt.addChild(self.symbol)
                    self.updateData(vobj.Object,"Points")
                    if hasattr(vobj,"ArrowSize"):
                        s = vobj.ArrowSize
                    else:
                        s = getParam("arrowsize",0.1)
                    self.coords.scaleFactor.setValue((s,s,s))
                    rn.addChild(self.pt)
                else:
                    if self.symbol:
                        if self.pt.findChild(self.symbol) != -1:
                            self.pt.removeChild(self.symbol)
                        if rn.findChild(self.pt) != -1:
                            rn.removeChild(self.pt)
        if prop in ["LineColor"]:
            if hasattr(self, "pt"):
                self.pt[0].rgb.setValue(vobj.LineColor[0],vobj.LineColor[1],vobj.LineColor[2])
        _ViewProviderDraft.onChanged(self,vobj,prop)
        return

    def claimChildren(self):
        if hasattr(self.Object,"Base"):
            return [self.Object.Base,self.Object.Tool]
        return []

    def setupContextMenu(self,vobj,menu):
        from PySide import QtCore,QtGui
        action1 = QtGui.QAction(QtGui.QIcon(":/icons/Draft_Edit.svg"),"Flatten this wire",menu)
        QtCore.QObject.connect(action1,QtCore.SIGNAL("triggered()"),self.flatten)
        menu.addAction(action1)

    def flatten(self):
        if hasattr(self,"Object"):
            if len(self.Object.Shape.Wires) == 1:
                import DraftGeomUtils
                fw = DraftGeomUtils.flattenWire(self.Object.Shape.Wires[0])
                points = [v.Point for v in fw.Vertexes]
                if len(points) == len(self.Object.Points):
                    if points != self.Object.Points:
                        FreeCAD.ActiveDocument.openTransaction("Flatten wire")
                        FreeCADGui.doCommand("FreeCAD.ActiveDocument."+self.Object.Name+".Points="+str(points).replace("Vector","FreeCAD.Vector").replace(" ",""))
                        FreeCAD.ActiveDocument.commitTransaction()

                    else:
                        from DraftTools import translate
                        FreeCAD.Console.PrintMessage(translate("Draft","This Wire is already flat")+"\n")
