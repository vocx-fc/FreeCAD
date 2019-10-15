
def mirror(objlist,p1,p2):
    """mirror(objlist,p1,p2,[clone]): creates a mirrored version of the given object(s)
    along an axis that passes through the two vectors p1 and p2."""

    if not objlist:
        FreeCAD.Console.PrintError(translate("draft","No object given")+"\n")
        return
    if p1 == p2:
        FreeCAD.Console.PrintError(translate("draft","The two points are coincident")+"\n")
        return
    if not isinstance(objlist,list):
        objlist = [objlist]

    result = []

    for obj in objlist:
        mir = FreeCAD.ActiveDocument.addObject("Part::Mirroring","mirror")
        mir.Label = "Mirror of "+obj.Label
        mir.Source = obj
        if gui:
            norm = FreeCADGui.ActiveDocument.ActiveView.getViewDirection().negative()
        else:
            norm = FreeCAD.Vector(0,0,1)
        pnorm = p2.sub(p1).cross(norm).normalize()
        mir.Base = p1
        mir.Normal = pnorm
        formatObject(mir,obj)
        result.append(mir)

    if len(result) == 1:
        result = result[0]
        select(result)
    return result


class Mirror(Modifier):
    """The Draft_Mirror FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Mirror',
                'Accel' : "M, I",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Mirror", "Mirror"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Mirror", "Mirrors the selected objects along a line defined by two points")}

    def Activated(self):
        self.name = translate("draft","Mirror", utf8_decode=True)
        Modifier.Activated(self,self.name)
        self.ghost = None
        if self.ui:
            if not FreeCADGui.Selection.getSelection():
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Select an object to mirror")+"\n")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
            else:
                self.proceed()

    def proceed(self):
        if self.call: self.view.removeEventCallback("SoEvent",self.call)
        self.sel = FreeCADGui.Selection.getSelection()
        self.ui.pointUi(self.name)
        self.ui.modUi()
        self.ui.xValue.setFocus()
        self.ui.xValue.selectAll()
        #self.ghost = ghostTracker(self.sel) TODO: solve this (see below)
        self.call = self.view.addEventCallback("SoEvent",self.action)
        FreeCAD.Console.PrintMessage(translate("draft", "Pick start point of mirror line")+"\n")
        self.ui.isCopy.hide()

    def finish(self,closed=False,cont=False):
        if self.ghost:
            self.ghost.finalize()
        Modifier.finish(self)
        if cont and self.ui:
            if self.ui.continueMode:
                FreeCADGui.Selection.clearSelection()
                self.Activated()

    def mirror(self,p1,p2,copy=False):
        """mirroring the real shapes"""
        sel = '['
        for o in self.sel:
            if len(sel) > 1:
                sel += ','
            sel += 'FreeCAD.ActiveDocument.'+o.Name
        sel += ']'
        FreeCADGui.addModule("Draft")
        self.commit(translate("draft","Mirror"),
                    ['Draft.mirror('+sel+','+DraftVecUtils.toString(p1)+','+DraftVecUtils.toString(p2)+')',
                     'FreeCAD.ActiveDocument.recompute()'])

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            self.point,ctrlPoint,info = getPoint(self,arg)
            if (len(self.node) > 0):
                last = self.node[-1]
                if self.ghost:
                    if self.point != last:
                        # TODO : the following doesn't work at the moment
                        mu = self.point.sub(last).normalize()
                        if FreeCAD.GuiUp:
                            mv = FreeCADGui.ActiveDocument.ActiveView.getViewDirection().negative()
                        else:
                            mv = FreeCAD.Vector(0,0,1)
                        mw = mv.cross(mu)
                        import WorkingPlane
                        tm = WorkingPlane.plane(u=mu,v=mv,w=mw,pos=last).getPlacement().toMatrix()
                        m = self.ghost.getMatrix()
                        m = m.multiply(tm.inverse())
                        m.scale(FreeCAD.Vector(1,1,-1))
                        m = m.multiply(tm)
                        m.scale(FreeCAD.Vector(-1,1,1))
                        self.ghost.setMatrix(m)
            if self.extendedCopy:
                if not hasMod(arg,MODALT): self.finish()
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if self.point:
                    self.ui.redraw()
                    if (self.node == []):
                        self.node.append(self.point)
                        self.ui.isRelative.show()
                        if self.ghost:
                            self.ghost.on()
                        FreeCAD.Console.PrintMessage(translate("draft", "Pick end point of mirror line")+"\n")
                        if self.planetrack:
                            self.planetrack.set(self.point)
                    else:
                        last = self.node[0]
                        if self.ui.isCopy.isChecked() or hasMod(arg,MODALT):
                            self.mirror(last,self.point,True)
                        else:
                            self.mirror(last,self.point)
                        if hasMod(arg,MODALT):
                            self.extendedCopy = True
                        else:
                            self.finish(cont=True)

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        self.point = Vector(numx,numy,numz)
        if not self.node:
            self.node.append(self.point)
            if self.ghost:
                self.ghost.on()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick end point of mirror line")+"\n")
        else:
            last = self.node[-1]
            if self.ui.isCopy.isChecked():
                self.mirror(last,self.point,True)
            else:
                self.mirror(last,self.point)
            self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Mirror',Mirror())

