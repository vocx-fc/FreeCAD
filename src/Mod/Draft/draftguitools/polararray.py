"""This module provides the Draft PolarArray tool.
"""
## @package draft_polararray
# \ingroup DRAFT
# \brief This module provides the Draft PolarArray tool.

import FreeCAD as App
import FreeCADGui as Gui
import Draft
import Draft_rc

if App.GuiUp:
    from PySide.QtCore import QT_TRANSLATE_NOOP
    import DraftTools
    from DraftGui import translate
else:
    def QT_TRANSLATE_NOOP(context, text):
        return text

    def translate(context, text):
        return text

_Msg = App.Console.PrintMessage
_Wrn = App.Console.PrintWarning
_Quantity = App.Units.Quantity

# So the resource file is used at least once
True if Draft_rc.__name__ else False


class TaskPanel_PolarArray:
    """TaskPanel for the PolarArray command"""

    def __init__(self):
        ui_file = ":/ui/TaskPanel_PolarArray.ui"
        self.form = Gui.PySideUic.loadUi(ui_file)
        self.name = self.form.windowTitle()

        start_angle = _Quantity(180.0, App.Units.Angle)
        angle_unit = start_angle.getUserPreferred()[2]
        self.form.spinbox_angle.setProperty('rawValue', start_angle.Value)
        self.form.spinbox_angle.setProperty('unit', angle_unit)
        self.form.spinbox_number.setValue(4)

        start_point = _Quantity(0.0, App.Units.Length)
        length_unit = start_point.getUserPreferred()[2]
        self.form.spinbox_c_X.setProperty('rawValue', start_point.Value)
        self.form.spinbox_c_X.setProperty('unit', length_unit)
        self.form.spinbox_c_Y.setProperty('rawValue', start_point.Value)
        self.form.spinbox_c_Y.setProperty('unit', length_unit)
        self.form.spinbox_c_Z.setProperty('rawValue', start_point.Value)
        self.form.spinbox_c_Z.setProperty('unit', length_unit)
        self.valid = True

        self.angle_str = ""
        self.angle = start_angle.Value
        self.number = int(2)
        self.c_X_str = ""
        self.c_Y_str = ""
        self.c_Z_str = ""
        self.center = App.Vector(0, 0, 0)
        self.fuse = False

    def accept(self):
        """Function that executes when clicking OK"""
        selection = Gui.Selection.getSelection()
        if not selection:
            _Wrn("At least one element must be selected\n")
            return False
        self.create_object(selection)
        if self.valid:
            self.print_messages(selection)
            self.finish()

    def create_object(self, selection):
        """Create the actual array"""
        self.number = self.form.spinbox_number.value()
        if self.number < 2:
            _Wrn("Number must be at least 2\n")
            self.valid = False
            return False

        self.valid = True
        self.angle_str = self.form.spinbox_angle.text()
        self.angle = _Quantity(self.angle_str).Value

        self.c_X_str = self.form.spinbox_c_X.text()
        self.c_Y_str = self.form.spinbox_c_Y.text()
        self.c_Z_str = self.form.spinbox_c_Z.text()
        self.center = App.Vector(_Quantity(self.c_X_str).Value,
                                 _Quantity(self.c_Y_str).Value,
                                 _Quantity(self.c_Z_str).Value)

        self.fuse = self.form.checkbox_fuse.isChecked()

        obj = Draft.makeArray(selection[0],
                              self.center, self.angle, self.number)
        obj.Fuse = self.fuse

    def print_messages(self, selection):
        """Print messages about the operation"""
        if not self.valid:
            return False
        _Msg("{}\n".format(16*"-"))
        _Msg("{0}\n".format(self.name))
        _Msg("Object: {0}\n".format(selection[0].Label))
        _Msg("Start angle: {}\n".format(self.angle_str))
        _Msg("Number of elements: {}\n".format(self.number))
        _Msg("Center of rotation: ({}, {}, {})\n".format(self.center.x,
                                                         self.center.y,
                                                         self.center.z))
        _Msg("Fuse: {}\n".format(self.fuse))

    def reject(self):
        """Function that executes when clicking Cancel"""
        _Msg("Aborted: {}\n".format(self.name))
        Gui.Control.closeDialog()

    def finish(self):
        Gui.Control.closeDialog()
        App.ActiveDocument.commitTransaction()
        App.ActiveDocument.recompute()


class CommandPolarArray(DraftTools.Creator):
    """Polar array command"""

    def __init__(self):
        super().__init__()
        self.featureName = "PolarArray"

    def GetResources(self):
        d = {'Pixmap': 'Draft_PolarArray',
             'MenuText': QT_TRANSLATE_NOOP("Draft_PolarArray", "PolarArray"),
             'ToolTip': QT_TRANSLATE_NOOP("Draft_PolarArray",
                                          "Creates copies of a selected object in a polar pattern.")}
        return d

    def Activated(self):
        panel = TaskPanel_PolarArray()
        Gui.Control.showDialog(panel)


if App.GuiUp:
    Gui.addCommand('Draft_PolarArray', CommandPolarArray())
