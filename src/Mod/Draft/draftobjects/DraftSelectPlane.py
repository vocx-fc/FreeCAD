
class SelectPlane(DraftTool):
    """The Draft_SelectPlane FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_SelectPlane',
                'Accel' : "W, P",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_SelectPlane", "SelectPlane"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_SelectPlane", "Select a working plane for geometry creation")}

    def Activated(self):
        DraftTool.Activated(self)
        self.offset = 0
        if not self.doc:
            return
        if self.handle():
            return
        self.ui.selectPlaneUi()
        FreeCAD.Console.PrintMessage(translate("draft", "Pick a face to define the drawing plane")+"\n")
        if plane.alignToSelection(self.offset):
            FreeCADGui.Selection.clearSelection()
            self.display(plane.axis)
            self.finish()
        else:
            self.call = self.view.addEventCallback("SoEvent", self.action)

    def action(self, arg):
        if arg["Type"] == "SoKeyboardEvent" and arg["Key"] == "ESCAPE":
            self.finish()
        if arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                # coin detection happens before the selection got a chance of being updated, so we must delay
                DraftGui.todo.delay(self.checkSelection,None)

    def checkSelection(self):
        if self.handle():
            self.finish()

    def handle(self):
        sel = FreeCADGui.Selection.getSelectionEx()
        if len(sel) == 1:
            sel = sel[0]
            self.ui = FreeCADGui.draftToolBar
            if Draft.getType(sel.Object) == "Axis":
                plane.alignToEdges(sel.Object.Shape.Edges)
                self.display(plane.axis)
                return True
            elif Draft.getType(sel.Object) in ["WorkingPlaneProxy","BuildingPart"]:
                plane.setFromPlacement(sel.Object.Placement,rebase=True)
                plane.weak = False
                if hasattr(sel.Object.ViewObject,"AutoWorkingPlane"):
                    if sel.Object.ViewObject.AutoWorkingPlane:
                        plane.weak = True
                if hasattr(sel.Object.ViewObject,"CutView") and hasattr(sel.Object.ViewObject,"AutoCutView"):
                    if sel.Object.ViewObject.AutoCutView:
                        sel.Object.ViewObject.CutView = True
                if hasattr(sel.Object.ViewObject,"RestoreView"):
                    if sel.Object.ViewObject.RestoreView:
                        if hasattr(sel.Object.ViewObject,"ViewData"):
                            if len(sel.Object.ViewObject.ViewData) >= 12:
                                d = sel.Object.ViewObject.ViewData
                                camtype = "orthographic"
                                if len(sel.Object.ViewObject.ViewData) == 13:
                                    if d[12] == 1:
                                        camtype = "perspective"
                                c = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
                                from pivy import coin
                                if isinstance(c,coin.SoOrthographicCamera):
                                    if camtype == "perspective":
                                        FreeCADGui.ActiveDocument.ActiveView.setCameraType("Perspective")
                                elif isinstance(c,coin.SoPerspectiveCamera):
                                    if camtype == "orthographic":
                                        FreeCADGui.ActiveDocument.ActiveView.setCameraType("Orthographic")
                                c = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
                                c.position.setValue([d[0],d[1],d[2]])
                                c.orientation.setValue([d[3],d[4],d[5],d[6]])
                                c.nearDistance.setValue(d[7])
                                c.farDistance.setValue(d[8])
                                c.aspectRatio.setValue(d[9])
                                c.focalDistance.setValue(d[10])
                                if camtype == "orthographic":
                                    c.height.setValue(d[11])
                                else:
                                    c.heightAngle.setValue(d[11])
                if hasattr(sel.Object.ViewObject,"RestoreState"):
                    if sel.Object.ViewObject.RestoreState:
                        if hasattr(sel.Object.ViewObject,"VisibilityMap"):
                            if sel.Object.ViewObject.VisibilityMap:
                                for k,v in sel.Object.ViewObject.VisibilityMap.items():
                                    o = FreeCADGui.ActiveDocument.getObject(k)
                                    if o:
                                        if o.Visibility != (v == "True"):
                                            FreeCADGui.doCommand("FreeCADGui.ActiveDocument.getObject(\""+k+"\").Visibility = "+v)
                self.display(plane.axis)
                self.ui.wplabel.setText(sel.Object.Label)
                self.ui.wplabel.setToolTip(translate("draft", "Current working plane")+": "+self.ui.wplabel.text())
                return True
            elif Draft.getType(sel.Object) == "SectionPlane":
                plane.setFromPlacement(sel.Object.Placement,rebase=True)
                plane.weak = False
                self.display(plane.axis)
                self.ui.wplabel.setText(sel.Object.Label)
                self.ui.wplabel.setToolTip(translate("draft", "Current working plane")+": "+self.ui.wplabel.text())
                return True
            elif sel.HasSubObjects:
                if len(sel.SubElementNames) == 1:
                    if "Face" in sel.SubElementNames[0]:
                        plane.alignToFace(sel.SubObjects[0], self.offset)
                        self.display(plane.axis)
                        return True
                    elif sel.SubElementNames[0] == "Plane":
                        plane.setFromPlacement(sel.Object.Placement,rebase=True)
                        self.display(plane.axis)
                        return True
                elif len(sel.SubElementNames) == 3:
                    if ("Vertex" in sel.SubElementNames[0]) \
                    and ("Vertex" in sel.SubElementNames[1]) \
                    and ("Vertex" in sel.SubElementNames[2]):
                        plane.alignTo3Points(sel.SubObjects[0].Point,
                                             sel.SubObjects[1].Point,
                                             sel.SubObjects[2].Point,
                                             self.offset)
                        self.display(plane.axis)
                        return True
            elif sel.Object.isDerivedFrom("Part::Feature"):
                if sel.Object.Shape:
                    if len(sel.Object.Shape.Faces) == 1:
                        plane.alignToFace(sel.Object.Shape.Faces[0], self.offset)
                        self.display(plane.axis)
                        return True
        elif sel:
            subs = []
            import Part
            for s in sel:
                for so in s.SubObjects:
                    if isinstance(so,Part.Vertex):
                        subs.append(so)
            if len(subs) == 3:
                plane.alignTo3Points(subs[0].Point,
                                     subs[1].Point,
                                     subs[2].Point,
                                     self.offset)
                self.display(plane.axis)
                return True
        return False

    def getCenterPoint(self,x,y,z):
        if not self.ui.isCenterPlane:
            return "0,0,0"
        v = FreeCAD.Vector(x,y,z)
        cam1 = FreeCAD.Vector(FreeCADGui.ActiveDocument.ActiveView.getCameraNode().position.getValue().getValue())
        cam2 = FreeCADGui.ActiveDocument.ActiveView.getViewDirection()
        vcam1 = DraftVecUtils.project(cam1,v)
        a = vcam1.getAngle(cam2)
        if a < 0.0001:
            return "0,0,0"
        d = vcam1.Length
        L = d/math.cos(a)
        vcam2 = DraftVecUtils.scaleTo(cam2,L)
        cp = cam1.add(vcam2)
        return str(cp.x)+","+str(cp.y)+","+str(cp.z)

    def selectHandler(self, arg):
        try:
            self.offset = float(self.ui.offset)
        except:
            self.offset = 0
        if arg == "XY":
            FreeCADGui.doCommandGui("FreeCAD.DraftWorkingPlane.alignToPointAndAxis(FreeCAD.Vector("+self.getCenterPoint(0,0,1)+"), FreeCAD.Vector(0,0,1), "+str(self.offset)+")")
            self.display('Top')
            self.finish()
        elif arg == "XZ":
            FreeCADGui.doCommandGui("FreeCAD.DraftWorkingPlane.alignToPointAndAxis(FreeCAD.Vector("+self.getCenterPoint(0,-1,0)+"), FreeCAD.Vector(0,-1,0), "+str(self.offset)+")")
            self.display('Front')
            self.finish()
        elif arg == "YZ":
            FreeCADGui.doCommandGui("FreeCAD.DraftWorkingPlane.alignToPointAndAxis(FreeCAD.Vector("+self.getCenterPoint(1,0,0)+"), FreeCAD.Vector(1,0,0), "+str(self.offset)+")")
            self.display('Side')
            self.finish()
        elif arg == "currentView":
            d = self.view.getViewDirection().negative()
            FreeCADGui.doCommandGui("FreeCAD.DraftWorkingPlane.alignToPointAndAxis(FreeCAD.Vector("+self.getCenterPoint(d.x,d.y,d.z)+"), FreeCAD.Vector("+str(d.x)+","+str(d.y)+","+str(d.z)+"), "+str(self.offset)+")")
            self.display(d)
            self.finish()
        elif arg == "reset":
            FreeCADGui.doCommandGui("FreeCAD.DraftWorkingPlane.reset()")
            self.display('Auto')
            self.finish()
        elif arg == "alignToWP":
            c = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
            r = FreeCAD.DraftWorkingPlane.getRotation().Rotation.Q
            c.orientation.setValue(r)
            self.finish()

    def offsetHandler(self, arg):
        self.offset = arg

    def display(self,arg):
        if self.offset:
            if self.offset > 0: suffix = ' + '+str(self.offset)
            else: suffix = ' - '+str(self.offset)
        else: suffix = ''
        if type(arg).__name__  == 'str':
            self.ui.wplabel.setText(arg+suffix)
        elif type(arg).__name__ == 'Vector':
            plv = 'd('+str(arg.x)+','+str(arg.y)+','+str(arg.z)+')'
            self.ui.wplabel.setText(plv+suffix)
        self.ui.wplabel.setToolTip(translate("draft", "Current working plane:",utf8_decode=True)+self.ui.wplabel.text())
        FreeCADGui.doCommandGui("FreeCADGui.Snapper.setGrid()")


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_SelectPlane',SelectPlane())
