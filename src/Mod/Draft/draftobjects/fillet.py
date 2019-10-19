"""This module provides the object code for Draft Fillet.
"""
## @package fillet
# \ingroup DRAFT
# \brief This module provides the object code for Draft Fillet.

# ***************************************************************************
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
import DraftGeomUtils
import Part

if App.GuiUp:
    from PySide.QtCore import QT_TRANSLATE_NOOP
    from DraftGui import translate
    from draftviewproviders import view_fillet
else:
    def QT_TRANSLATE_NOOP(context, text):
        return text

    def translate(context, text):
        return text


def _msg(text, end="\n"):
    """Print message with newline"""
    App.Console.PrintMessage(text + end)


def _wrn(text, end="\n"):
    """Print warning with newline"""
    App.Console.PrintWarning(text + end)


def _err(text, end="\n"):
    """Print error with newline"""
    App.Console.PrintError(text + end)


def _tr(text):
    """Function to translate with the context set"""
    return translate("Draft", text)


def _print_obj_length(obj, edge, num=1):
    if hasattr(obj, "Label"):
        name = obj.Label
    else:
        name = num

    _msg("({0}): {1}; {2} {3}".format(num, name,
                                      _tr("length:"), edge.Length))


def _extract_edges(objs):
    """Extract the edges from the list of objects, Draft lines or Part.Edges

    objs : list of Draft Lines or Part.Edges
        The list of edges from which to create the fillet.
    """
    o1, o2 = objs
    if hasattr(o1, "PropertiesList"):
        if "Proxy" in o1.PropertiesList:
            if hasattr(o1.Proxy, "Type"):
                if o1.Proxy.Type in ("Wire", "Fillet"):
                    e1 = o1.Shape.Edges[0]
        elif "Shape" in o1.PropertiesList:
            if o1.Shape.ShapeType in ("Wire", "Edge"):
                e1 = o1.Shape
    elif hasattr(o1, "ShapeType"):
        if o1.ShapeType in "Edge":
            e1 = o1

    _print_obj_length(o1, e1, num=1)

    if hasattr(o2, "PropertiesList"):
        if "Proxy" in o2.PropertiesList:
            if hasattr(o2.Proxy, "Type"):
                if o2.Proxy.Type in ("Wire", "Fillet"):
                    e2 = o2.Shape.Edges[0]
        elif "Shape" in o2.PropertiesList:
            if o2.Shape.ShapeType in ("Wire", "Edge"):
                e2 = o2.Shape
    elif hasattr(o2, "ShapeType"):
        if o2.ShapeType in "Edge":
            e2 = o2

    _print_obj_length(o2, e2, num=2)

    return e1, e2


def make_fillet(objs, radius=100, chamfer=False, delete=False):
    """Create a fillet between two lines or edges.

    Parameters
    ----------
    objs : list
        List of two objects of type wire, or edges.

    radius : float, optional
        It defaults to 100 mm. The curvature of the fillet.

    chamfer : bool, optional
        It defaults to `False`. If it is `True` it no longer produces
        a rounded fillet but a chamfer (straight edge)
        with the value of the `radius`.

    delete : bool, optional
        It defaults to `False`. If it is `True` it will delete
        the pair of objects that are used to create the fillet.
        Otherwise, the original objects will still be there.

    Returns
    -------
    Part::Part2DObject
        The object of type `'Fillet'`.
        It returns `None` if it fails producing the object.
    """
    _msg(16 * "-")
    _msg("make_fillet")
    if len(objs) != 2:
        _err(_tr("Two elements are needed"))
        return None

    e1, e2 = _extract_edges(objs)

    edges = DraftGeomUtils.fillet([e1, e2], radius, chamfer)
    if len(edges) < 3:
        _err(_tr("Radius is too large") + ", r={}".format(radius))
        return None

    lengths = [edges[0].Length, edges[1].Length, edges[2].Length]
    _msg(_tr("Segment") + " 1, " + _tr("length:") + " {}".format(lengths[0]))
    _msg(_tr("Segment") + " 2, " + _tr("length:") + " {}".format(lengths[1]))
    _msg(_tr("Segment") + " 3, " + _tr("length:") + " {}".format(lengths[2]))

    try:
        wire = Part.Wire(edges)
    except Part.OCCError:
        return None

    obj = App.ActiveDocument.addObject("Part::Part2DObjectPython",
                                       "Fillet")
    Fillet(obj)
    obj.Shape = wire
    obj.Length = wire.Length
    obj.Start = wire.Vertexes[0].Point
    obj.End = wire.Vertexes[-1].Point
    obj.FilletRadius = radius

    if delete:
        App.ActiveDocument.removeObject(objs[0].Name)
        App.ActiveDocument.removeObject(objs[1].Name)
        _msg(_tr("Removed original objects"))
    if App.GuiUp:
        view_fillet.ViewProviderFillet(obj.ViewObject)
        Draft.formatObject(obj)
        Draft.select(obj)
    return obj


class Fillet(Draft._DraftObject):
    """The fillet object"""

    def __init__(self, obj):
        super().__init__(obj, "Fillet")
        obj.addProperty("App::PropertyVectorDistance", "Start", "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "The start point of this line"))
        obj.addProperty("App::PropertyVectorDistance", "End", "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "The end point of this line"))
        obj.addProperty("App::PropertyLength", "Length", "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "The length of this line"))
        obj.addProperty("App::PropertyLength", "FilletRadius", "Draft",
                        QT_TRANSLATE_NOOP("App::Property",
                                          "Radius to use to fillet "
                                          "the corners"))
        obj.setEditorMode("Start", 1)
        obj.setEditorMode("End", 1)
        obj.setEditorMode("Length", 1)
        # Change to 0 to make it editable
        obj.setEditorMode("FilletRadius", 1)

    def execute(self, obj):
        if hasattr(obj, "Length"):
            obj.Length = obj.Shape.Length
        if hasattr(obj, "Start"):
            obj.Start = obj.Shape.Vertexes[0].Point
        if hasattr(obj, "End"):
            obj.End = obj.Shape.Vertexes[-1].Point

    def onChanged(self, obj, prop):
        """Change the radius of fillet. NOT IMPLEMENTED"""
        if prop in "FilletRadius":
            pass
