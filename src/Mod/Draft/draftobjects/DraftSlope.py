
class Draft_Slope():

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Slope',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Slope", "Set Slope"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Slope", "Sets the slope of a selected Line or Wire")}

    def Activated(self):
        if not FreeCADGui.Selection.getSelection():
            return
        for obj in FreeCADGui.Selection.getSelection():
            if Draft.getType(obj) != "Wire":
                FreeCAD.Console.PrintMessage(translate("draft", "This tool only works with Wires and Lines")+"\n")
                return
        w = QtGui.QWidget()
        w.setWindowTitle(translate("Draft","Slope"))
        layout = QtGui.QHBoxLayout(w)
        label = QtGui.QLabel(w)
        label.setText(translate("Draft", "Slope")+":")
        layout.addWidget(label)
        self.spinbox = QtGui.QDoubleSpinBox(w)
        self.spinbox.setMinimum(-9999.99)
        self.spinbox.setMaximum(9999.99)
        self.spinbox.setSingleStep(0.01)
        self.spinbox.setToolTip(translate("Draft", "Slope to give selected Wires/Lines: 0 = horizontal, 1 = 45deg up, -1 = 45deg down"))
        layout.addWidget(self.spinbox)
        taskwidget = QtGui.QWidget()
        taskwidget.form = w
        taskwidget.accept = self.accept
        FreeCADGui.Control.showDialog(taskwidget)

    def accept(self):
        if hasattr(self,"spinbox"):
            pc = self.spinbox.value()
            FreeCAD.ActiveDocument.openTransaction("Change slope")
            for obj in FreeCADGui.Selection.getSelection():
                if Draft.getType(obj) == "Wire":
                    if len(obj.Points) > 1:
                        lp = None
                        np = []
                        for p in obj.Points:
                            if not lp:
                                lp = p
                            else:
                                v = p.sub(lp)
                                z = pc*FreeCAD.Vector(v.x,v.y,0).Length
                                lp = FreeCAD.Vector(p.x,p.y,lp.z+z)
                            np.append(lp)
                        obj.Points = np
            FreeCAD.ActiveDocument.commitTransaction()
        FreeCADGui.Control.closeDialog()
        FreeCAD.ActiveDocument.recompute()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Slope',Draft_Slope())

