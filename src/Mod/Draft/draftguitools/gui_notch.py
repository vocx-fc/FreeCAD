"""GuiCommand for the NotchConnector."""
import FreeCAD
import FreeCADGui
import Draft_rc

True if Draft_rc.__name__ else False


class NotchConnector:
    """Definition for the NotchConnector command."""
    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
        if len(selection) < 2:
            return

        for sel in selection:
            if sel == selection[0]:
                FreeCADGui.doCommand("base = FreeCAD.ActiveDocument.getObject('%s')" % (sel.Name))
            elif sel == selection[1]:
                FreeCADGui.doCommand("tools = [FreeCAD.ActiveDocument.getObject('%s')]" % (sel.Name))
            else:
                FreeCADGui.doCommand("tools.append(FreeCAD.ActiveDocument.getObject('%s'))" % (sel.Name))

        FreeCADGui.addModule("draftobjects.notch")
        FreeCADGui.doCommand("draftobjects.notch.make_notch_connector(base, tools, cut_depth=50.0)")
        if len(selection) == 2:
            FreeCADGui.doCommand("draftobjects.notch.make_notch_connector(tools[0], [base], cut_depth=-50.0)")
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        """Here you can define if the command must be active or not (greyed) if certain conditions
        are met or not. This function is optional."""
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def GetResources(self):
        return {'Pixmap': ":/icons/Draft_Draft",
                'Accel': "",  # a default shortcut (optional)
                'MenuText': "Notch Connector",
                'ToolTip': __doc__}


FreeCADGui.addCommand('NotchConnector', NotchConnector())
