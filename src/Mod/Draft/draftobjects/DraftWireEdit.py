
class FinishLine:
    """a FreeCAD command to finish any running Line drawing operation"""

    def Activated(self):
        if (FreeCAD.activeDraftCommand != None):
            if (FreeCAD.activeDraftCommand.featureName == "Line"):
                FreeCAD.activeDraftCommand.finish(False)

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Finish',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_FinishLine", "Finish line"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_FinishLine", "Finishes a line without closing it")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False


class CloseLine:
    """a FreeCAD command to close any running Line drawing operation"""

    def Activated(self):
        if (FreeCAD.activeDraftCommand != None):
            if (FreeCAD.activeDraftCommand.featureName == "Line"):
                FreeCAD.activeDraftCommand.finish(True)

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Lock',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_CloseLine", "Close Line"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_CloseLine", "Closes the line being drawn")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False


class UndoLine:
    """a FreeCAD command to undo last drawn segment of a line"""

    def Activated(self):
        if (FreeCAD.activeDraftCommand != None):
            if (FreeCAD.activeDraftCommand.featureName == "Line"):
                FreeCAD.activeDraftCommand.undolast()

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Rotate',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_UndoLine", "Undo last segment"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_UndoLine", "Undoes the last drawn segment of the line being drawn")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False


class AddPoint(Modifier):
    """The Draft_AddPoint FreeCAD command definition"""

    def __init__(self):
        self.running = False

    def GetResources(self):
        return {'Pixmap'  : 'Draft_AddPoint',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_AddPoint", "Add Point"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_AddPoint", "Adds a point to an existing Wire or B-spline")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
        if selection:
            if (Draft.getType(selection[0]) in ['Wire','BSpline']):
                FreeCADGui.runCommand("Draft_Edit")
                FreeCADGui.draftToolBar.vertUi(True)


class DelPoint(Modifier):
    """The Draft_DelPoint FreeCAD command definition"""

    def __init__(self):
        self.running = False

    def GetResources(self):
        return {'Pixmap'  : 'Draft_DelPoint',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_DelPoint", "Remove Point"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_DelPoint", "Removes a point from an existing Wire or B-spline")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()
        if selection:
            if (Draft.getType(selection[0]) in ['Wire','BSpline']):
                FreeCADGui.runCommand("Draft_Edit")
                FreeCADGui.draftToolBar.vertUi(False)


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_FinishLine',FinishLine())
    FreeCADGui.addCommand('Draft_CloseLine',CloseLine())
    FreeCADGui.addCommand('Draft_UndoLine',UndoLine())
    FreeCADGui.addCommand('Draft_AddPoint',AddPoint())
    FreeCADGui.addCommand('Draft_DelPoint',DelPoint())

