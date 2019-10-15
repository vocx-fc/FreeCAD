
class WireToBSpline(Modifier):
    """The Draft_Wire2BSpline FreeCAD command definition"""

    def __init__(self):
        self.running = False

    def GetResources(self):
        return {'Pixmap'  : 'Draft_WireToBSpline',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_WireToBSpline", "Wire to B-spline"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_WireToBSpline", "Converts between Wire and B-spline")}

    def IsActive(self):
        if FreeCADGui.Selection.getSelection():
            return True
        else:
            return False

    def Activated(self):
        if self.running:
            self.finish()
        else:
            selection = FreeCADGui.Selection.getSelection()
            if selection:
                if (Draft.getType(selection[0]) in ['Wire','BSpline']):
                    Modifier.Activated(self,"Convert Curve Type")
                    if self.doc:
                        self.obj = FreeCADGui.Selection.getSelection()
                        if self.obj:
                            self.obj = self.obj[0]
                            self.pl = None
                            if "Placement" in self.obj.PropertiesList:
                                self.pl = self.obj.Placement
                            self.Points = self.obj.Points
                            self.closed = self.obj.Closed
                            n = None
                            if (Draft.getType(self.obj) == 'Wire'):
                                n = Draft.makeBSpline(self.Points, self.closed, self.pl)
                            elif (Draft.getType(self.obj) == 'BSpline'):
                                n = Draft.makeWire(self.Points, self.closed, self.pl)
                            if n:
                                Draft.formatObject(n,self.obj)
                        else:
                            self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_WireToBSpline',WireToBSpline())

