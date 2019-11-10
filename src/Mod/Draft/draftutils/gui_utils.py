"""This module provides GUI utility functions for the Draft Workbench.

This module should contain auxiliary functions which require
the graphical user interface (GUI).
"""
## @package gui_utils
# \ingroup DRAFT
# \brief This module provides utility functions for the Draft Workbench

# ***************************************************************************
# *   (c) 2009, 2010                                                        *
# *   Yorik van Havre <yorik@uncreated.net>, Ken Cline <cline@frii.com>     *
# *   (c) 2019 Eliud Cabrera Castillo <e.cabrera-castillo@tum.de>           *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   FreeCAD is distributed in the hope that it will be useful,            *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with FreeCAD; if not, write to the Free Software        *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************


import FreeCAD
import FreeCADGui
from .utils import _msg
from .utils import _wrn
# from .utils import _log
from .utils import _tr
from .utils import getParam
from pivy import coin
import math


def get_3d_view():
    """Return the current 3D view.

    Returns
    -------
    Gui::View3DInventor
        Return the current `ActiveView` in the active document,
        or the first `Gui::View3DInventor` view found.

        Return `None` if the graphical interface is not available.
    """
    if FreeCAD.GuiUp:
        v = FreeCADGui.ActiveDocument.ActiveView
        if "View3DInventor" in str(type(v)):
            return v

        # print("Debug: Draft: Warning, not working in active view")
        v = FreeCADGui.ActiveDocument.mdiViewsOfType("Gui::View3DInventor")
        if v:
            return v[0]

    _wrn(_tr("No graphical interface"))
    return None


get3DView = get_3d_view


def autogroup(obj):
    """Adds a given object to the defined Draft autogroup, if applicable.

    This function only works if the graphical interface is available.
    It checks that the `FreeCAD.draftToolBar` class is available,
    which contains the group to use to automatically store
    new created objects.

    Originally, it worked with standard groups (`App::DocumentObjectGroup`),
    and Arch Workbench containers like `'Site'`, `'Building'`, `'Floor'`,
    and `'BuildingPart'`.

    Now it works with Draft Layers.

    Parameters
    ----------
    obj : App::DocumentObject
        Any type of object that will be stored in the group.
    """
    doc = FreeCAD.ActiveDocument
    if FreeCAD.GuiUp:
        view = FreeCADGui.ActiveDocument.ActiveView
        if hasattr(FreeCADGui, "draftToolBar"):
            if (hasattr(FreeCADGui.draftToolBar, "autogroup")
                    and not FreeCADGui.draftToolBar.isConstructionMode()):
                if FreeCADGui.draftToolBar.autogroup is not None:
                    g = doc.getObject(FreeCADGui.draftToolBar.autogroup)
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
                    a = view.getActiveObject("Arch")
                    if a:
                        a.addObject(obj)


def dim_symbol(symbol=None, invert=False):
    """Return the specified dimension symbol.

    Parameters
    ----------
    symbol : int, optional
        It defaults to `None`, in which it gets the value from the parameter
        database, `get_param("dimsymbol", 0)`.

        A numerical value defines different markers
         * 0, `SoSphere`
         * 1, `SoMarkerSet` with a circle
         * 2, `SoSeparator` with a `soCone`
         * 3, `SoSeparator` with a `SoFaceSet`
         * 4, `SoSeparator` with a `SoLineSet`, calling `dim_dash`
         * Otherwise, `SoSphere`

    invert : bool, optional
        It defaults to `False`.
        If it is `True` and `symbol=2`, the cone will be rotated
        -90 degrees around the Z axis, otherwise the rotation is positive,
        +90 degrees.

    Returns
    -------
    Coin.SoNode
        A `Coin.SoSphere`, or `Coin.SoMarkerSet` (circle),
        or `Coin.SoSeparator` (cone, face, line)
        that will be used as a dimension symbol.
    """
    if symbol is None:
        symbol = getParam("dimsymbol", 0)

    if symbol == 0:
        return coin.SoSphere()
    elif symbol == 1:
        marker = coin.SoMarkerSet()
        marker.markerIndex = FreeCADGui.getMarkerIndex("circle", 9)
        return marker
    elif symbol == 2:
        marker = coin.SoSeparator()
        t = coin.SoTransform()
        t.translation.setValue((0, -2, 0))
        t.center.setValue((0, 2, 0))
        if invert:
            t.rotation.setValue(coin.SbVec3f((0, 0, 1)), -math.pi/2)
        else:
            t.rotation.setValue(coin.SbVec3f((0, 0, 1)), math.pi/2)
        c = coin.SoCone()
        c.height.setValue(4)
        marker.addChild(t)
        marker.addChild(c)
        return marker
    elif symbol == 3:
        marker = coin.SoSeparator()
        c = coin.SoCoordinate3()
        c.point.setValues([(-1, -2, 0), (0, 2, 0),
                           (1, 2, 0), (0, -2, 0)])
        f = coin.SoFaceSet()
        marker.addChild(c)
        marker.addChild(f)
        return marker
    elif symbol == 4:
        return dimDash((-1.5, -1.5, 0), (1.5, 1.5, 0))
    else:
        _wrn(_tr("Symbol not implemented. Use a default symbol."))
        return coin.SoSphere()


dimSymbol = dim_symbol


def dim_dash(p1, p2):
    """Return a SoSeparator with a line used to make dimension dashes.

    It is used by `dim_symbol` to create line end symbols
    like `'Tick-2'`, `'DimOvershoot'`, and `'ExtOvershoot'` dashes.

    Parameters
    ----------
    p1 : tuple of three floats or Base::Vector3
        A point to define a line vertex.

    p2 : tuple of three floats or Base::Vector3
        A point to define a line vertex.

    Returns
    -------
    Coin.SoSeparator
        A Coin object with a `SoLineSet` created from `p1` and `p2`
        as vertices.
    """
    dash = coin.SoSeparator()
    v = coin.SoVertexProperty()
    v.vertex.set1Value(0, p1)
    v.vertex.set1Value(1, p2)
    line = coin.SoLineSet()
    line.vertexProperty = v
    dash.addChild(line)
    return dash


dimDash = dim_dash


def remove_hidden(objectslist):
    """Return only the visible objects in the list.

    This function only works if the graphical interface is available
    as the `Visibility` attribute is a property of the view provider
    (`obj.ViewObject`).

    Parameters
    ----------
    objectslist : list of App::DocumentObject
        List of any type of object.

    Returns
    -------
    list
        Return a copy of the input list without those objects
        for which `obj.ViewObject.Visibility` is `False`.

        If the graphical interface is not loaded
        the returned list is just a copy of the input list.
    """
    newlist = objectslist[:]
    for obj in objectslist:
        if obj.ViewObject:
            if not obj.ViewObject.isVisible():
                newlist.remove(obj)
                _msg(_tr("Visibility off; removed from list: ") + obj.Label)
    return newlist


removeHidden = remove_hidden


def format_object(target, origin=None):
    """Apply visual properties from the Draft toolbar or another object.

    This function only works if the graphical interface is available
    as the visual properties are attributes of the view provider
    (`obj.ViewObject`).

    Parameters
    ----------
    target : App::DocumentObject
        Any type of scripted object.

        This object will adopt the applicable visual properties,
        `FontSize`, `TextColor`, `LineWidth`, `PointColor`, `LineColor`,
        and `ShapeColor`, defined in the Draft toolbar
        (`FreeCADGui.draftToolBar`) or will adopt
        the properties from the `origin` object.

        The `target` is also placed in the construction group
        if the construction mode in the Draft toolbar is active.

    origin : App::DocumentObject, optional
        It defaults to `None`.
        If it exists, it will provide the visual properties to assign
        to `target`, with the exception of `BoundingBox`, `Proxy`,
        `RootNode` and `Visibility`.
    """
    if not target:
        return
    obrep = target.ViewObject
    if not obrep:
        return
    ui = None
    if FreeCAD.GuiUp:
        if hasattr(FreeCADGui, "draftToolBar"):
            ui = FreeCADGui.draftToolBar
    if ui:
        doc = FreeCAD.ActiveDocument
        if ui.isConstructionMode():
            col = fcol = ui.getDefaultColor("constr")
            gname = getParam("constructiongroupname", "Construction")
            grp = doc.getObject(gname)
            if not grp:
                grp = doc.addObject("App::DocumentObjectGroup", gname)
            grp.addObject(target)
            if hasattr(obrep, "Transparency"):
                obrep.Transparency = 80
        else:
            col = ui.getDefaultColor("ui")
            fcol = ui.getDefaultColor("face")
        col = (float(col[0]), float(col[1]), float(col[2]), 0.0)
        fcol = (float(fcol[0]), float(fcol[1]), float(fcol[2]), 0.0)
        lw = ui.linewidth
        fs = ui.fontsize
        if not origin or not hasattr(origin, 'ViewObject'):
            if "FontSize" in obrep.PropertiesList:
                obrep.FontSize = fs
            if "TextColor" in obrep.PropertiesList:
                obrep.TextColor = col
            if "LineWidth" in obrep.PropertiesList:
                obrep.LineWidth = lw
            if "PointColor" in obrep.PropertiesList:
                obrep.PointColor = col
            if "LineColor" in obrep.PropertiesList:
                obrep.LineColor = col
            if "ShapeColor" in obrep.PropertiesList:
                obrep.ShapeColor = fcol
        else:
            matchrep = origin.ViewObject
            for p in matchrep.PropertiesList:
                if p not in ("DisplayMode", "BoundingBox",
                             "Proxy", "RootNode", "Visibility"):
                    if p in obrep.PropertiesList:
                        if not obrep.getEditorMode(p):
                            if hasattr(getattr(matchrep, p), "Value"):
                                val = getattr(matchrep, p).Value
                            else:
                                val = getattr(matchrep, p)
                            try:
                                setattr(obrep, p, val)
                            except Exception:
                                pass
            if matchrep.DisplayMode in obrep.listDisplayModes():
                obrep.DisplayMode = matchrep.DisplayMode
            if (hasattr(matchrep, "DiffuseColor")
                    and hasattr(obrep, "DiffuseColor")):
                obrep.DiffuseColor = matchrep.DiffuseColor


formatObject = format_object
