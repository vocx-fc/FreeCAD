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
# from .utils import _msg
from .utils import _wrn
# from .utils import _log
from .utils import _tr


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
