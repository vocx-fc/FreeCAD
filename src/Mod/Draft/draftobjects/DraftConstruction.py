
class Draft_AddConstruction():

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Construction',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_AddConstruction", "Add to Construction group"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_AddConstruction", "Adds the selected objects to the Construction group")}

    def Activated(self):
        import FreeCADGui
        if hasattr(FreeCADGui,"draftToolBar"):
            col = FreeCADGui.draftToolBar.getDefaultColor("constr")
            col = (float(col[0]),float(col[1]),float(col[2]),0.0)
            gname = Draft.getParam("constructiongroupname","Construction")
            grp = FreeCAD.ActiveDocument.getObject(gname)
            if not grp:
                grp = FreeCAD.ActiveDocument.addObject("App::DocumentObjectGroup",gname)
            for obj in FreeCADGui.Selection.getSelection():
                grp.addObject(obj)
                obrep = obj.ViewObject
                if "TextColor" in obrep.PropertiesList:
                    obrep.TextColor = col
                if "PointColor" in obrep.PropertiesList:
                    obrep.PointColor = col
                if "LineColor" in obrep.PropertiesList:
                    obrep.LineColor = col
                if "ShapeColor" in obrep.PropertiesList:
                    obrep.ShapeColor = col
                if hasattr(obrep,"Transparency"):
                    obrep.Transparency = 80


class ToggleConstructionMode():
    """The Draft_ToggleConstructionMode FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Construction',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleConstructionMode", "Toggle Construction Mode"),
                'Accel' : "C, M",
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleConstructionMode", "Toggles the Construction Mode for next objects.")}

    def Activated(self):
        FreeCADGui.draftToolBar.constrButton.toggle()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_AddConstruction',Draft_AddConstruction())
    FreeCADGui.addCommand('Draft_ToggleConstructionMode',ToggleConstructionMode())

