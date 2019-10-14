"""This module provides the Draft Heal tool.
"""
## @package heal
# \ingroup DRAFT
# \brief This module provides the Draft Heal tool.

import FreeCAD as App
import FreeCADGui as Gui
import Draft
import Draft_rc

# Dummy use of the resource file just to prevent complains
# from code checkers like flake8
False if Draft_rc.__name__ else True


if App.GuiUp:
    from PySide.QtCore import QT_TRANSLATE_NOOP
    from PySide import QtCore
    from DraftGui import translate
else:
    def QT_TRANSLATE_NOOP(context, text):
        return text

    def translate(context, text):
        return text


class Heal():
    """The Draft Heal command definition"""

    def GetResources(self):
        _msg = ("Heal faulty Draft objects "
                "saved from an earlier FreeCAD version.")
        return {'Pixmap': 'Draft_Heal',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Heal", "Heal"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Heal", _msg)}

    def Activated(self):
        s = Gui.Selection.getSelection()
        App.ActiveDocument.openTransaction("Heal")
        if s:
            Draft.heal(s)
        else:
            Draft.heal()
        App.ActiveDocument.commitTransaction()


if App.GuiUp:
    Gui.addCommand('Draft_Heal', Heal())
