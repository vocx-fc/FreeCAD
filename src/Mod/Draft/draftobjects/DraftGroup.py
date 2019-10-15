
class AddToGroup():
    """The AddToGroup FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_AddToGroup',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_AddToGroup", "Move to group..."),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_AddToGroup", "Moves the selected object(s) to an existing group")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        self.groups = ["Ungroup"]
        self.groups.extend(Draft.getGroupNames())
        self.labels = ["Ungroup"]
        for g in self.groups:
            o = FreeCAD.ActiveDocument.getObject(g)
            if o: self.labels.append(o.Label)
        self.ui = FreeCADGui.draftToolBar
        self.ui.sourceCmd = self
        self.ui.popupMenu(self.labels)

    def proceed(self,labelname):
        self.ui.sourceCmd = None
        if labelname == "Ungroup":
            for obj in FreeCADGui.Selection.getSelection():
                try:
                    Draft.ungroup(obj)
                except:
                    pass
        else:
            if labelname in self.labels:
                i = self.labels.index(labelname)
                g = FreeCAD.ActiveDocument.getObject(self.groups[i])
                for obj in FreeCADGui.Selection.getSelection():
                    try:
                        g.addObject(obj)
                    except:
                        pass


class SelectGroup():
    """The SelectGroup FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_SelectGroup',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_SelectGroup", "Select group"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_SelectGroup", "Selects all objects with the same parents as this group")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        sellist = []
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 1:
            if sel[0].isDerivedFrom("App::DocumentObjectGroup"):
                cts = Draft.getGroupContents(FreeCADGui.Selection.getSelection())
                for o in cts:
                    FreeCADGui.Selection.addSelection(o)
                return
        for ob in sel:
            for child in ob.OutList:
                FreeCADGui.Selection.addSelection(child)
            for parent in ob.InList:
                FreeCADGui.Selection.addSelection(parent)
                for child in parent.OutList:
                    FreeCADGui.Selection.addSelection(child)


class SetAutoGroup():
    """The SetAutoGroup FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_AutoGroup',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_AutoGroup", "AutoGroup"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_AutoGroup", "Select a group to automatically add all Draft & Arch objects to")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        if hasattr(FreeCADGui,"draftToolBar"):
            self.ui = FreeCADGui.draftToolBar
            s = FreeCADGui.Selection.getSelection()
            if len(s) == 1:
                if (Draft.getType(s[0]) == "Layer") or \
                ( FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/BIM").GetBool("AutogroupAddGroups",False) and \
                (s[0].isDerivedFrom("App::DocumentObjectGroup") or (Draft.getType(s[0]) in ["Site","Building","Floor","BuildingPart",]))):
                    self.ui.setAutoGroup(s[0].Name)
                    return
            self.groups = ["None"]
            gn = [o.Name for o in FreeCAD.ActiveDocument.Objects if Draft.getType(o) == "Layer"]
            if FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/BIM").GetBool("AutogroupAddGroups",False):
                gn.extend(Draft.getGroupNames())
            if gn:
                self.groups.extend(gn)
                self.labels = [translate("draft","None")]
                self.icons = [self.ui.getIcon(":/icons/button_invalid.svg")]
                for g in gn:
                    o = FreeCAD.ActiveDocument.getObject(g)
                    if o:
                        self.labels.append(o.Label)
                        self.icons.append(o.ViewObject.Icon)
                self.labels.append(translate("draft","Add new Layer"))
                self.icons.append(self.ui.getIcon(":/icons/document-new.svg"))
                self.ui.sourceCmd = self
                from PySide import QtCore
                pos = self.ui.autoGroupButton.mapToGlobal(QtCore.QPoint(0,self.ui.autoGroupButton.geometry().height()))
                self.ui.popupMenu(self.labels,self.icons,pos)

    def proceed(self,labelname):
        self.ui.sourceCmd = None
        if labelname in self.labels:
            if labelname == self.labels[0]:
                self.ui.setAutoGroup(None)
            elif labelname == self.labels[-1]:
                FreeCADGui.runCommand("Draft_Layer")
            else:
                i = self.labels.index(labelname)
                self.ui.setAutoGroup(self.groups[i])


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_AddToGroup',AddToGroup())
    FreeCADGui.addCommand('Draft_SelectGroup',SelectGroup())
    FreeCADGui.addCommand('Draft_AutoGroup',SetAutoGroup())

