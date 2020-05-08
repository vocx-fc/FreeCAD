# ***************************************************************************
# *   (c) 2020 Eliud Cabrera Castillo <e.cabrera-castillo@tum.de>           *
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
"""Provides the functions for creating arcs with the Draft Workbench.

A simple circular arc is the same as a circle, just defined by the initial
angle and the angle of sweeping.

A circular may also be defined by three points.
"""
## @package make_arcs
# \ingroup DRAFT
# \brief Provides the functions for creating arcs with the Draft Workbench.

import FreeCAD as App
import Draft
import draftutils.utils as utils
from draftutils.messages import _msg, _err
from draftutils.translate import _tr

import draftutils.gui_utils as gui_utils


def make_arc(radius, startangle=0, endangle=45,
             placement=None, face=False,
             support=None, map_mode="Deactivated",
             primitive=False):
    """Draw a circular arc defined by the radius and the angles.

    Parameters
    ----------
    radius: int, float
        The radius of the circle.

    startangle: int, float, optional
        It defaults to 0. The start angle in degrees of the arc.

    endangle: int, float, optional
        It defaults to 45. The end angle in degrees of the arc.
        If `startangle` and `endangle` are equal, a circle is created,
        otherwise an arc is created.
        However, internally, they are the same `Circle` object.

    placement: Base::Placement, optional
        It defaults to `None`.
        It is a placement, comprised of a `Base` (`Base::Vector3`),
        and a `Rotation` (`Base::Rotation`).
        If it exists it moves the center of the new object to the point
        indicated by `placement.Base`, while `placement.Rotation`
        is ignored so that the arc keeps the same orientation
        with which it was created.

        If both `support` and `placement` are given,
        `placement.Base` is used for the `AttachmentOffset.Base`,
        and again `placement.Rotation` is ignored.

    face: bool, optional
        It defaults to `False`.
        If it is `True` it will create a face in the closed arc.
        Otherwise only the circumference edge will be shown.

    support: App::PropertyLinkSubList, optional
        It defaults to `None`.
        It is a list containing tuples to define the attachment
        of the new object.

        A tuple in the list needs two elements;
        the first is an external object, and the second is another tuple
        with the names of sub-elements on that external object
        likes vertices or faces.
        ::
            support = [(obj, ("Face1"))]
            support = [(obj, ("Vertex1", "Vertex5", "Vertex8"))]

        This parameter sets the `Support` property but it only really affects
        the position of the new object when the `map_mode`
        is set to other than `'Deactivated'`.

    map_mode: str, optional
        It defaults to `'Deactivated'`.
        It defines the type of `'MapMode'` of the new object.
        This parameter only works when a `support` is also provided.

        Example: place the new object on a face or another object.
        ::
            support = [(obj, ("Face1"))]
            map_mode = 'FlatFace'

        Example: place the new object on a plane created by three vertices
        of an object.
        ::
            support = [(obj, ("Vertex1", "Vertex5", "Vertex8"))]
            map_mode = 'ThreePointsPlane'

    primitive: bool, optional
        It defaults to `False`. If it is `True`, it will create a Part
        primitive instead of a Draft object.
        In this case, `placement`, `face`, `support`, and `map_mode`
        are ignored.

    Returns
    -------
    Part::Part2DObject or Part::Feature
        The new arc object.
        Normally it returns a parametric Draft object (`Part::Part2DObject`).
        If `primitive` is `True`, it returns a basic `Part::Feature`.

    None
        Returns `None` if there is a problem.
    """
    _name = "make_arc"
    utils.print_header(_name, "Arc by radius")

    try:
        utils.type_check([(radius, (int, float))], name=_name)
    except TypeError:
        _err(_tr("Radius: ") + "{}".format(radius))
        _err(_tr("Wrong input: must be a number."))
        return None
    try:
        utils.type_check([(startangle, (int, float)),
                          (endangle, (int, float))], name=_name)
    except TypeError:
        _err(_tr("Wrong input: angle must be a number."))
        return None

    if placement is not None:
        try:
            utils.type_check([(placement, App.Placement)], name=_name)
        except TypeError:
            _err(_tr("Placement: ") + "{}".format(placement))
            _err(_tr("Wrong input: incorrect type of placement."))
            return None

    _msg(_tr("Radius: ") + "{}".format(radius))
    _msg(_tr("Start angle: ") + "{}".format(startangle))
    _msg(_tr("End angle: ") + "{}".format(endangle))
    _msg(_tr("Placement: ") + "{}".format(placement))

    obj = Draft.makeCircle(radius,
                           placement=placement, face=face,
                           startangle=startangle, endangle=endangle,
                           support=support)

    if primitive:
        _msg(_tr("Create primitive object"))
        nobj = App.ActiveDocument.addObject("Part::Feature", "Arc")
        nobj.Shape = obj
        App.ActiveDocument.removeObject(obj.Name)
        return nobj

    if App.GuiUp:
        gui_utils.autogroup(obj)

    original_placement = obj.Placement

    if placement and not support:
        obj.Placement.Base = placement.Base
        _msg(_tr("Final placement: ") + "{}".format(obj.Placement))
    if face:
        _msg(_tr("Face: True"))
    if support:
        _msg(_tr("Support: ") + "{}".format(support))
        _msg(_tr("Map mode: " + "{}".format(map_mode)))
        obj.MapMode = map_mode
        if placement:
            obj.AttachmentOffset.Base = placement.Base
            obj.AttachmentOffset.Rotation = original_placement.Rotation
            _msg(_tr("Attachment offset: {}".format(obj.AttachmentOffset)))
        _msg(_tr("Final placement: ") + "{}".format(obj.Placement))

    return obj
