# ***************************************************************************
# *   (c) 2009 Yorik van Havre <yorik@uncreated.net>                        *
# *   (c) 2010 Ken Cline <cline@frii.com>                                   *
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
"""Provide the Base object for all Draft Gui commands."""
## @package gui_base
# \ingroup DRAFT
# \brief This module provides the Base object for all Draft Gui commands.

import FreeCAD as App
import FreeCADGui as Gui
import draftutils.todo as todo
import DraftTrackers


class GuiCommandBase:
    """Generic class that is the basis of all Gui commands.

    This class should eventually replace `DraftTools.DraftTool`,
    once all functionality in that class is merged here.

    Attributes
    ----------
    commit_list : list of 2-element tuples
        Each tuple is made of a string, and a list of strings.
        ::
            commit_list = [(string1, list1), (string2, list2), ...]

        The string is a simple header, for example, a command name,
        that indicates what is being executed.

        Each string in the list of strings represents a Python instruction
        which will be executed in a delayed fashion
        by `todo.ToDo.delayCommit()`
        ::
            list1 = ["a = FreeCAD.Vector()",
                     "pl = FreeCAD.Placement()",
                     "Draft.autogroup(obj)"]

            commit_list = [("Something", list1)]

        This is used when the 3D view has event callbacks that crash
        Coin3D.
        If this is not needed, those commands could be called in the
        body of the command without problem.
        ::
            >>> a = FreeCAD.Vector()
            >>> pl = FreeCAD.Placement()
            >>> Draft.autogroup(obj)
    """

    def __init__(self):
        self.call = None
        self.commit_list = []
        self.doc = None
        App.activeDraftCommand = None
        self.view = None
        self.planetrack = None

    def IsActive(self):
        """Return True when this command should be available."""
        if App.ActiveDocument:
            return True
        else:
            return False

    def Activated(self, name="None", no_plane_setup=False, is_subtool=False):
        if App.activeDraftCommand and not is_subtool:
            App.activeDraftCommand.finish()

        self.doc = App.ActiveDocument
        if not self.doc:
            self.finish()
            return

        App.activeDraftCommand = self
        self.view = Draft.get3DView()

        if Draft.getParam("showPlaneTracker", False):
            self.planetrack = DraftTrackers.PlaneTracker()
        if hasattr(Gui, "Snapper"):
            Gui.Snapper.setTrackers()

    def finish(self):
        """Terminate the active command by committing the list of commands.

        It also perform some other tasks like terminating
        the plane tracker and the snapper.
        """
        App.activeDraftCommand = None
        if self.planetrack:
            self.planetrack.finalize()
        if hasattr(Gui, "Snapper"):
            Gui.Snapper.off()
        if self.call:
            try:
                self.view.removeEventCallback("SoEvent", self.call)
            except RuntimeError:
                # the view has been deleted already
                pass
            self.call = None
        if self.commit_list:
            todo.ToDo.delayCommit(self.commit_list)
        self.commit_list = []

    def commit(self, name, func):
        """Store actions to be committed to the document.

        Parameters
        ----------
        name : str
            A string that indicates what is being committed.

        func : list of strings
            Each element of the list should be a Python command
            that will be executed.
        """
        self.commit_list.append((name, func))


class Creator(GuiCommandBase):
    """Generic class for tools that create shapes, such as line or arc"""

    def __init__(self):
        super().__init__()

    def Activated(self, name="None", no_plane_setup=False):
        super().Activated(name, no_plane_setup)
        if not no_plane_setup:
            # self.support = getSupport()
            pass


class Modifier(GuiCommandBase):
    """Generic class for tools that are modifiers, such as move and rotate

    Attribute
    ---------
    copy_mode : bool
        Defaults to `False`. Defines whether the tool will copies or not.
    """
    def __init__(self):
        super().__init__()
        self.copy_mode = False
