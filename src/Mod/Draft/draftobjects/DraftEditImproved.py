
class EditImproved(Modifier):
    """The Draft_Edit_Improved FreeCAD command definition"""

    def __init__(self):
        self.is_running = False
        self.editable_objects = []
        self.original_view_settings = {}

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Edit',
                'Accel' : "D, E",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Edit_Improved", "Edit Improved"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Edit_Improved", "Edits the selected objects")}

    def Activated(self):
        if self.is_running:
            return self.finish()
        self.is_running = True
        Modifier.Activated(self,"Edit_Improved")
        self.get_selection()

    def proceed(self):
        self.remove_view_callback()
        self.get_editable_objects_from_selection()
        if not self.editable_objects:
            return self.finish()
        self.call = self.view.addEventCallback("SoEvent", self.action)
        self.highlight_editable_objects()

    def finish(self):
        Modifier.finish(self)
        self.remove_view_callback()
        self.restore_editable_objects_graphics()
        self.__init__()

    def action(self, event):
        if event["Type"] == "SoKeyboardEvent" and event["Key"] == "ESCAPE":
            self.finish()

    def get_selection(self):
        if not FreeCADGui.Selection.getSelection() and self.ui:
            FreeCAD.Console.PrintMessage(translate("draft", "Select an object to edit")+"\n")
            self.call = self.view.addEventCallback("SoEvent", selectObject)
        else:
            self.proceed()

    def remove_view_callback(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)

    def get_editable_objects_from_selection(self):
        for object in FreeCADGui.Selection.getSelection():
            if object.isDerivedFrom("Part::Part2DObject"):
                self.editable_objects.append(object)
            elif hasattr(object, "Base") and object.Base.isDerivedFrom("Part::Part2DObject"):
                self.editable_objects.append(object.Base)

    def highlight_editable_objects(self):
        for object in self.editable_objects:
            self.original_view_settings[object.Name] = {
                'Visibility': object.ViewObject.Visibility,
                'PointSize': object.ViewObject.PointSize,
                'PointColor': object.ViewObject.PointColor,
                'LineColor': object.ViewObject.LineColor
            }
            object.ViewObject.Visibility = True
            object.ViewObject.PointSize = 10
            object.ViewObject.PointColor = (1., 0., 0.)
            object.ViewObject.LineColor = (1., 0., 0.)
            xray = coin.SoAnnotation()
            xray.addChild(object.ViewObject.RootNode.getChild(2).getChild(0))
            xray.setName("xray")
            object.ViewObject.RootNode.addChild(xray)

    def restore_editable_objects_graphics(self):
        for object in self.editable_objects:
            try:
                for attribute, value in self.original_view_settings[object.Name].items():
                    view_object = object.ViewObject
                    setattr(view_object, attribute, value)
                    view_object.RootNode.removeChild(view_object.RootNode.getByName("xray"))
            except:
                # This can occur if objects have had graph changing operations
                pass


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Edit_Improved',EditImproved())

