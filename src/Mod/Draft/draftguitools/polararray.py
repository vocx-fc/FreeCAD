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
    import PySide.QtCore as QtCore
    import PySide.QtGui as QtGui
    # import DraftTools
    from DraftGui import translate
    # from DraftGui import displayExternal
    from pivy import coin
else:
    def QT_TRANSLATE_NOOP(context, text):
        return text

    def translate(context, text):
        return text

_Msg = App.Console.PrintMessage
_Wrn = App.Console.PrintWarning
_Quantity = App.Units.Quantity


def _tr(text):
    """Function to translate with the context set"""
    return translate("Draft", text)


# So the resource file doesn't trigger errors from code checkers (flake8)
True if Draft_rc.__name__ else False


class TaskPanel_PolarArray:
    """TaskPanel for the PolarArray command"""

    def __init__(self):
        ui_file = ":/ui/TaskPanel_PolarArray.ui"
        self.form = Gui.PySideUic.loadUi(ui_file)
        self.name = self.form.windowTitle()

        icon_name = "Draft_PolarArray"
        svg = ":/icons/" + icon_name
        pix = QtGui.QPixmap(svg)
        icon = QtGui.QIcon.fromTheme(icon_name, QtGui.QIcon(svg))
        self.form.setWindowIcon(icon)
        self.form.label_icon.setPixmap(pix.scaled(32, 32))

        start_angle = _Quantity(180.0, App.Units.Angle)
        angle_unit = start_angle.getUserPreferred()[2]
        self.form.spinbox_angle.setProperty('rawValue', start_angle.Value)
        self.form.spinbox_angle.setProperty('unit', angle_unit)
        self.form.spinbox_number.setValue(4)

        self.angle_str = self.form.spinbox_angle.text()
        self.angle = start_angle.Value
        self.number = self.form.spinbox_number.value()

        start_point = _Quantity(0.0, App.Units.Length)
        length_unit = start_point.getUserPreferred()[2]
        self.form.spinbox_c_X.setProperty('rawValue', start_point.Value)
        self.form.spinbox_c_X.setProperty('unit', length_unit)
        self.form.spinbox_c_Y.setProperty('rawValue', start_point.Value)
        self.form.spinbox_c_Y.setProperty('unit', length_unit)
        self.form.spinbox_c_Z.setProperty('rawValue', start_point.Value)
        self.form.spinbox_c_Z.setProperty('unit', length_unit)
        self.valid = True

        self.c_X_str = ""
        self.c_Y_str = ""
        self.c_Z_str = ""
        self.center = App.Vector(0, 0, 0)

        # The mask is not used at the moment, but could be used in the future
        # by a callback to restrict the coordinates of the pointer.
        self.mask = ""

        # When the checkbox changes, change the fuse value
        self.fuse = False
        QtCore.QObject.connect(self.form.checkbox_fuse,
                               QtCore.SIGNAL("stateChanged(int)"),
                               self.set_fuse)

    def accept(self):
        """Function that executes when clicking the OK button"""
        selection = Gui.Selection.getSelection()
        self.number = self.form.spinbox_number.value()
        self.valid = self.validate_input(selection, self.number)
        if self.valid:
            self.create_object(selection)
            self.print_messages(selection)
            self.finish()

    def validate_input(self, selection, number):
        """Check that the input is valid"""
        if not selection:
            _Wrn(_tr("At least one element must be selected") + "\n")
            return False
        if number < 2:
            _Wrn(_tr("Number of elements must be at least 2") + "\n")
            return False
        if selection[0].isDerivedFrom("App::FeaturePython"):
            _Wrn(_tr("Selection is not suitable for array") + "\n")
            _Wrn(_tr("Object:") + " {}\n".format(selection[0].Label))
            return False
        return True

    def create_object(self, selection):
        """Create the actual object"""
        self.angle_str = self.form.spinbox_angle.text()
        self.angle = _Quantity(self.angle_str).Value

        self.c_X_str = self.form.spinbox_c_X.text()
        self.c_Y_str = self.form.spinbox_c_Y.text()
        self.c_Z_str = self.form.spinbox_c_Z.text()
        self.center = App.Vector(_Quantity(self.c_X_str).Value,
                                 _Quantity(self.c_Y_str).Value,
                                 _Quantity(self.c_Z_str).Value)

        if len(selection) == 1:
            sel_obj = selection[0]
        else:
            # This can be changed so a compound of multiple
            # selected objects is produced
            sel_obj = selection[0]

        obj = Draft.makeArray(sel_obj,
                              self.center, self.angle, self.number)
        if obj:
            self.fuse = self.form.checkbox_fuse.isChecked()
            obj.Fuse = self.fuse

    def print_fuse_state(self):
        """Print the state translated"""
        if self.fuse:
            translated_state = _tr("True")
        else:
            translated_state = _tr("False")
        _Msg(_tr("Fuse:") + " {}\n".format(translated_state))

    def set_fuse(self):
        """This function is called when the fuse checkbox changes"""
        self.fuse = self.form.checkbox_fuse.isChecked()
        self.print_fuse_state()

    def print_messages(self, selection):
        """Print messages about the operation"""
        if len(selection) == 1:
            sel_obj = selection[0]
        else:
            # This can be changed so a compound of multiple
            # selected objects is produced
            sel_obj = selection[0]
        _Msg("{}\n".format(16*"-"))
        _Msg("{}\n".format(self.name))
        _Msg(_tr("Object:") + " {}\n".format(sel_obj.Label))
        _Msg(_tr("Start angle:") + " {}\n".format(self.angle_str))
        _Msg(_tr("Number of elements:") + " {}\n".format(self.number))
        _Msg(_tr("Center of rotation:")
             + " ({}, {}, {})\n".format(self.center.x,
                                        self.center.y,
                                        self.center.z))
        self.print_fuse_state()

    def display_point(self, point=None, plane=None, mask=None):
        """Displays the coordinates in the x, y, and z widgets.

        This function should be used in a Coin callback so that
        the coordinate values are automatically updated when the
        mouse pointer moves.
        This was copied from `DraftGui.py` but needs to be improved
        for this particular command.

        point :
            is a vector that arrives by the callback.
        plane :
            is a `WorkingPlane` instance, for example,
            `App.DraftWorkingPlane`. It is not used at the moment,
            but could be used to set up the grid.
        mask :
            is a string that specifies which coordinate is being
            edited. It is used to restrict edition of a single coordinate.
        """
        # Get the coordinates to display
        dp = None
        if point:
            dp = point

        # Set the widgets to the value of the mouse pointer.
        #
        # setText() is used if the widget is a Gui::InputField,
        # derived from a QLineEdit.
        #
        # setProperty() is used if the widget is a Gui::QuantitySpinBox
        # derived rom QAbstractSpinBox.
        #
        # The mask allows editing only one field, that is, only one coordinate.
        # sbx = self.form.spinbox_c_X
        # sby = self.form.spinbox_c_Y
        # sbz = self.form.spinbox_c_Z
        if dp:
            if self.mask in ('y', 'z'):
                # sbx.setText(displayExternal(dp.x, None, 'Length'))
                self.form.spinbox_c_X.setProperty('rawValue', dp.x)
            else:
                # sbx.setText(displayExternal(dp.x, None, 'Length'))
                self.form.spinbox_c_X.setProperty('rawValue', dp.x)
            if self.mask in ('x', 'z'):
                # sby.setText(displayExternal(dp.y, None, 'Length'))
                self.form.spinbox_c_Y.setProperty('rawValue', dp.y)
            else:
                # sby.setText(displayExternal(dp.y, None, 'Length'))
                self.form.spinbox_c_Y.setProperty('rawValue', dp.y)
            if self.mask in ('x', 'y'):
                # sbz.setText(displayExternal(dp.z, None, 'Length'))
                self.form.spinbox_c_Z.setProperty('rawValue', dp.z)
            else:
                # sbz.setText(displayExternal(dp.z, None, 'Length'))
                self.form.spinbox_c_Z.setProperty('rawValue', dp.z)

        # Set masks
        if (mask == "x") or (self.mask == "x"):
            self.form.spinbox_c_X.setEnabled(True)
            self.form.spinbox_c_Y.setEnabled(False)
            self.form.spinbox_c_Z.setEnabled(False)
            self.set_focus("x")
        elif (mask == "y") or (self.mask == "y"):
            self.form.spinbox_c_X.setEnabled(False)
            self.form.spinbox_c_Y.setEnabled(True)
            self.form.spinbox_c_Z.setEnabled(False)
            self.set_focus("y")
        elif (mask == "z") or (self.mask == "z"):
            self.form.spinbox_c_X.setEnabled(False)
            self.form.spinbox_c_Y.setEnabled(False)
            self.form.spinbox_c_Z.setEnabled(True)
            self.set_focus("z")
        else:
            self.form.spinbox_c_X.setEnabled(True)
            self.form.spinbox_c_Y.setEnabled(True)
            self.form.spinbox_c_Z.setEnabled(True)
            self.set_focus()

    def set_focus(self, key=None):
        """Set the focus on the widget that receives the key signal"""
        if key is None or key == "x":
            self.form.spinbox_c_X.setFocus()
            self.form.spinbox_c_X.selectAll()
        elif key == "y":
            self.form.spinbox_c_Y.setFocus()
            self.form.spinbox_c_Y.selectAll()
        elif key == "z":
            self.form.spinbox_c_Z.setFocus()
            self.form.spinbox_c_Z.selectAll()

    def reject(self):
        """Function that executes when clicking the Cancel button"""
        _Msg(_tr("Aborted:") + " {}\n".format(self.name))
        self.finish()

    def finish(self):
        """Function that runs at the end after OK or Cancel"""
        App.ActiveDocument.commitTransaction()
        Gui.ActiveDocument.resetEdit()
        # Runs the parent command to complete the call
        self.source_command.completed()


class CommandPolarArray:
    """Polar array command"""

    def __init__(self):
        self.command_name = "PolarArray"

    def GetResources(self):
        _msg = ("Creates copies of a selected object, "
                "and places the copies in a polar pattern.\n"
                "The properties of the array can be further modified after "
                "the new object is created, including turning it into "
                "a different type of array.")
        d = {'Pixmap': 'Draft_PolarArray',
             'MenuText': QT_TRANSLATE_NOOP("Draft", "Polar array"),
             'ToolTip': QT_TRANSLATE_NOOP("Draft", _msg)}
        return d

    def Activated(self):
        """This is called when the command is executed.

        We add callbacks that connect the 3D view with
        the widgets of the task panel.
        """
        self.location = coin.SoLocation2Event.getClassTypeId()
        self.mouse_event = coin.SoMouseButtonEvent.getClassTypeId()
        self.view = Draft.get3DView()
        self.callback_move = \
            self.view.addEventCallbackPivy(self.location, self.move)
        self.callback_click = \
            self.view.addEventCallbackPivy(self.mouse_event, self.click)

        self.ui = TaskPanel_PolarArray()
        # The calling class (this one) is saved in the object
        # of the interface, to be able to call a function from within it.
        self.ui.source_command = self
        Gui.Control.showDialog(self.ui)

    def move(self, event_cb):
        """This is a callback for when the mouse pointer moves in the 3D view.

        It should automatically update the coordinates in the widgets
        of the task panel.
        """
        event = event_cb.getEvent()
        mousepos = event.getPosition().getValue()
        ctrl = event.wasCtrlDown()
        self.point = Gui.Snapper.snap(mousepos, active=ctrl)
        if self.ui:
            self.ui.display_point(self.point)

    def click(self, event_cb=None):
        """This is a callback for when the mouse pointer clicks on the 3D view.

        It should act as if the Enter key was pressed, or the OK button
        was pressed in the task panel.
        """
        if event_cb:
            event = event_cb.getEvent()
            if event.getState() != coin.SoMouseButtonEvent.DOWN:
                return
        if self.ui and self.point:
            # The accept function of the interface
            # should call the completed function
            # of the calling class (this one).
            self.ui.accept()

    def completed(self):
        """This is called when the command is terminated.

        We should remove the callbacks that were added to the widgets
        and then close the task panel.
        """
        self.view.removeEventCallbackPivy(self.location,
                                          self.callback_move)
        self.view.removeEventCallbackPivy(self.mouse_event,
                                          self.callback_click)
        if Gui.Control.activeDialog():
            Gui.Snapper.off()
            Gui.Control.closeDialog()
            App.ActiveDocument.recompute()


if App.GuiUp:
    Gui.addCommand('Draft_PolarArray', CommandPolarArray())
