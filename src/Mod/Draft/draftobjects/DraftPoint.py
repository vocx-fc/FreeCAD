
def makePoint(X=0, Y=0, Z=0,color=None,name = "Point", point_size= 5):
    """ makePoint(x,y,z ,[color(r,g,b),point_size]) or
        makePoint(Vector,color(r,g,b),point_size]) -
        creates a Point in the current document.
        example usage:
        p1 = makePoint()
        p1.ViewObject.Visibility= False # make it invisible
        p1.ViewObject.Visibility= True  # make it visible
        p1 = makePoint(-1,0,0) #make a point at -1,0,0
        p1 = makePoint(1,0,0,(1,0,0)) # color = red
        p1.X = 1 #move it in x
        p1.ViewObject.PointColor =(0.0,0.0,1.0) #change the color-make sure values are floats
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    if isinstance(X,FreeCAD.Vector):
        Z = X.z
        Y = X.y
        X = X.x
    _Point(obj,X,Y,Z)
    obj.X = X
    obj.Y = Y
    obj.Z = Z
    if gui:
        _ViewProviderPoint(obj.ViewObject)
        if hasattr(FreeCADGui,"draftToolBar") and (not color):
            color = FreeCADGui.draftToolBar.getDefaultColor('ui')
        obj.ViewObject.PointColor = (float(color[0]), float(color[1]), float(color[2]))
        obj.ViewObject.PointSize = point_size
        obj.ViewObject.Visibility = True
    select(obj)

    return obj


class _Point(_DraftObject):
    """The Draft Point object"""
    def __init__(self, obj,x=0,y=0,z=0):
        _DraftObject.__init__(self,obj,"Point")
        obj.addProperty("App::PropertyDistance","X","Draft",QT_TRANSLATE_NOOP("App::Property","X Location")).X = x
        obj.addProperty("App::PropertyDistance","Y","Draft",QT_TRANSLATE_NOOP("App::Property","Y Location")).Y = y
        obj.addProperty("App::PropertyDistance","Z","Draft",QT_TRANSLATE_NOOP("App::Property","Z Location")).Z = z
        mode = 2
        obj.setEditorMode('Placement',mode)

    def execute(self, obj):
        import Part
        shape = Part.Vertex(Vector(0,0,0))
        obj.Shape = shape
        obj.Placement.Base = FreeCAD.Vector(obj.X.Value,obj.Y.Value,obj.Z.Value)


class _ViewProviderPoint(_ViewProviderDraft):
    """A viewprovider for the Draft Point object"""
    def __init__(self, obj):
        _ViewProviderDraft.__init__(self,obj)

    def onChanged(self, vobj, prop):
        mode = 2
        vobj.setEditorMode('LineColor',mode)
        vobj.setEditorMode('LineWidth',mode)
        vobj.setEditorMode('BoundingBox',mode)
        vobj.setEditorMode('Deviation',mode)
        vobj.setEditorMode('DiffuseColor',mode)
        vobj.setEditorMode('DisplayMode',mode)
        vobj.setEditorMode('Lighting',mode)
        vobj.setEditorMode('LineMaterial',mode)
        vobj.setEditorMode('ShapeColor',mode)
        vobj.setEditorMode('ShapeMaterial',mode)
        vobj.setEditorMode('Transparency',mode)

    def getIcon(self):
        return ":/icons/Draft_Dot.svg"


class Point(Creator):
    """this class will create a vertex after the user clicks a point on the screen"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Point',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Point", "Point"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Point", "Creates a point object")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        Creator.Activated(self)
        self.view = Draft.get3DView()
        self.stack = []
        rot = self.view.getCameraNode().getField("orientation").getValue()
        upv = Vector(rot.multVec(coin.SbVec3f(0,1,0)).getValue())
        plane.setup(self.view.getViewDirection().negative(), Vector(0,0,0), upv)
        self.point = None
        if self.ui:
            self.ui.pointUi()
            self.ui.continueCmd.show()
        # adding 2 callback functions
        self.callbackClick = self.view.addEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(),self.click)
        self.callbackMove = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(),self.move)

    def move(self,event_cb):
        event = event_cb.getEvent()
        mousepos = event.getPosition().getValue()
        ctrl = event.wasCtrlDown()
        self.point = FreeCADGui.Snapper.snap(mousepos,active=ctrl)
        if self.ui:
            self.ui.displayPoint(self.point)

    def numericInput(self,numx,numy,numz):
        """called when a numeric value is entered on the toolbar"""
        self.point = FreeCAD.Vector(numx,numy,numz)
        self.click()

    def click(self,event_cb=None):
        if event_cb:
            event = event_cb.getEvent()
            if event.getState() != coin.SoMouseButtonEvent.DOWN:
                return
        if self.point:
            self.stack.append(self.point)
            if len(self.stack) == 1:
                self.view.removeEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(),self.callbackClick)
                self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(),self.callbackMove)
                commitlist = []
                if Draft.getParam("UsePartPrimitives",False):
                    # using
                    commitlist.append((translate("draft","Create Point"),
                                        ['point = FreeCAD.ActiveDocument.addObject("Part::Vertex","Point")',
                                         'point.X = '+str(self.stack[0][0]),
                                         'point.Y = '+str(self.stack[0][1]),
                                         'point.Z = '+str(self.stack[0][2]),
                                         'Draft.autogroup(point)',
                                         'FreeCAD.ActiveDocument.recompute()']))
                else:
                    # building command string
                    FreeCADGui.addModule("Draft")
                    commitlist.append((translate("draft","Create Point"),
                                        ['point = Draft.makePoint('+str(self.stack[0][0])+','+str(self.stack[0][1])+','+str(self.stack[0][2])+')',
                                         'Draft.autogroup(point)',
                                         'FreeCAD.ActiveDocument.recompute()']))
                todo.delayCommit(commitlist)
                FreeCADGui.Snapper.off()
            self.finish()

    def finish(self,cont=False):
        """terminates the operation and restarts if needed"""
        Creator.finish(self)
        if self.ui:
            if self.ui.continueMode:
                self.Activated()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Point',Point())

