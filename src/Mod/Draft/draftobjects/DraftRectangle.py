
def makeRectangle(length, height, placement=None, face=None, support=None):
    """makeRectangle(length,width,[placement],[face]): Creates a Rectangle
    object with length in X direction and height in Y direction.
    If a placement is given, it is used. If face is False, the
    rectangle is shown as a wireframe, otherwise as a face."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if placement: typecheck([(placement,FreeCAD.Placement)], "makeRectangle")
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","Rectangle")
    _Rectangle(obj)

    obj.Length = length
    obj.Height = height
    obj.Support = support
    if face != None:
        obj.MakeFace = face
    if placement: obj.Placement = placement
    if gui:
        _ViewProviderRectangle(obj.ViewObject)
        formatObject(obj)
        select(obj)

    return obj


class _Rectangle(_DraftObject):
    """The Rectangle object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"Rectangle")
        obj.addProperty("App::PropertyDistance","Length","Draft",QT_TRANSLATE_NOOP("App::Property","Length of the rectangle"))
        obj.addProperty("App::PropertyDistance","Height","Draft",QT_TRANSLATE_NOOP("App::Property","Height of the rectangle"))
        obj.addProperty("App::PropertyLength","FilletRadius","Draft",QT_TRANSLATE_NOOP("App::Property","Radius to use to fillet the corners"))
        obj.addProperty("App::PropertyLength","ChamferSize","Draft",QT_TRANSLATE_NOOP("App::Property","Size of the chamfer to give to the corners"))
        obj.addProperty("App::PropertyBool","MakeFace","Draft",QT_TRANSLATE_NOOP("App::Property","Create a face"))
        obj.addProperty("App::PropertyInteger","Rows","Draft",QT_TRANSLATE_NOOP("App::Property","Horizontal subdivisions of this rectangle"))
        obj.addProperty("App::PropertyInteger","Columns","Draft",QT_TRANSLATE_NOOP("App::Property","Vertical subdivisions of this rectangle"))
        obj.addProperty("App::PropertyArea","Area","Draft",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.MakeFace = getParam("fillmode",True)
        obj.Length=1
        obj.Height=1
        obj.Rows=1
        obj.Columns=1

    def execute(self, obj):
        if (obj.Length.Value != 0) and (obj.Height.Value != 0):
            import Part, DraftGeomUtils
            plm = obj.Placement
            shape = None
            if hasattr(obj,"Rows") and hasattr(obj,"Columns"):
                if obj.Rows > 1:
                    rows = obj.Rows
                else:
                    rows = 1
                if obj.Columns > 1:
                    columns = obj.Columns
                else:
                    columns = 1
                if (rows > 1) or (columns > 1):
                    shapes = []
                    l = obj.Length.Value/columns
                    h = obj.Height.Value/rows
                    for i in range(columns):
                        for j in range(rows):
                            p1 = Vector(i*l,j*h,0)
                            p2 = Vector(p1.x+l,p1.y,p1.z)
                            p3 = Vector(p1.x+l,p1.y+h,p1.z)
                            p4 = Vector(p1.x,p1.y+h,p1.z)
                            p = Part.makePolygon([p1,p2,p3,p4,p1])
                            if "ChamferSize" in obj.PropertiesList:
                                if obj.ChamferSize.Value != 0:
                                    w = DraftGeomUtils.filletWire(p,obj.ChamferSize.Value,chamfer=True)
                                    if w:
                                        p = w
                            if "FilletRadius" in obj.PropertiesList:
                                if obj.FilletRadius.Value != 0:
                                    w = DraftGeomUtils.filletWire(p,obj.FilletRadius.Value)
                                    if w:
                                        p = w
                            if hasattr(obj,"MakeFace"):
                                if obj.MakeFace:
                                    p = Part.Face(p)
                            shapes.append(p)
                    if shapes:
                        shape = Part.makeCompound(shapes)
            if not shape:
                p1 = Vector(0,0,0)
                p2 = Vector(p1.x+obj.Length.Value,p1.y,p1.z)
                p3 = Vector(p1.x+obj.Length.Value,p1.y+obj.Height.Value,p1.z)
                p4 = Vector(p1.x,p1.y+obj.Height.Value,p1.z)
                shape = Part.makePolygon([p1,p2,p3,p4,p1])
                if "ChamferSize" in obj.PropertiesList:
                    if obj.ChamferSize.Value != 0:
                        w = DraftGeomUtils.filletWire(shape,obj.ChamferSize.Value,chamfer=True)
                        if w:
                            shape = w
                if "FilletRadius" in obj.PropertiesList:
                    if obj.FilletRadius.Value != 0:
                        w = DraftGeomUtils.filletWire(shape,obj.FilletRadius.Value)
                        if w:
                            shape = w
                if hasattr(obj,"MakeFace"):
                    if obj.MakeFace:
                        shape = Part.Face(shape)
                else:
                    shape = Part.Face(shape)
            obj.Shape = shape
            if hasattr(obj,"Area") and hasattr(shape,"Area"):
                obj.Area = shape.Area
            obj.Placement = plm
        obj.positionBySupport()


class _ViewProviderRectangle(_ViewProviderDraft):
    def __init__(self,vobj):
        _ViewProviderDraft.__init__(self,vobj)
        vobj.addProperty("App::PropertyFile","TextureImage","Draft",QT_TRANSLATE_NOOP("App::Property","Defines a texture image (overrides hatch patterns)"))


class Rectangle(Creator):
    """the Draft_Rectangle FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Rectangle',
                'Accel' : "R, E",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Rectangle", "Rectangle"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Rectangle", "Creates a 2-point rectangle. CTRL to snap")}

    def Activated(self):
        name = translate("draft","Rectangle")
        Creator.Activated(self,name)
        if self.ui:
            self.refpoint = None
            self.ui.pointUi(name)
            self.ui.extUi()
            if Draft.getParam("UsePartPrimitives",False):
                self.fillstate = self.ui.hasFill.isChecked()
                self.ui.hasFill.setChecked(True)
            self.call = self.view.addEventCallback("SoEvent",self.action)
            self.rect = rectangleTracker()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick first point")+"\n")

    def finish(self,closed=False,cont=False):
        """terminates the operation and closes the poly if asked"""
        Creator.finish(self)
        if self.ui:
            if hasattr(self,"fillstate"):
                self.ui.hasFill.setChecked(self.fillstate)
                del self.fillstate
            self.rect.off()
            self.rect.finalize()
            if self.ui.continueMode:
                self.Activated()

    def createObject(self):
        """creates the final object in the current doc"""
        p1 = self.node[0]
        p3 = self.node[-1]
        diagonal = p3.sub(p1)
        p2 = p1.add(DraftVecUtils.project(diagonal, plane.v))
        p4 = p1.add(DraftVecUtils.project(diagonal, plane.u))
        length = p4.sub(p1).Length
        if abs(DraftVecUtils.angle(p4.sub(p1),plane.u,plane.axis)) > 1: length = -length
        height = p2.sub(p1).Length
        if abs(DraftVecUtils.angle(p2.sub(p1),plane.v,plane.axis)) > 1: height = -height
        try:
            # building command string
            rot,sup,pts,fil = self.getStrings()
            base = p1
            if length < 0:
                length = -length
                base = base.add((p1.sub(p4)).negative())
            if height < 0:
                height = -height
                base = base.add((p1.sub(p2)).negative())
            FreeCADGui.addModule("Draft")
            if Draft.getParam("UsePartPrimitives",False):
                # Use Part Primitive
                self.commit(translate("draft","Create Plane"),
                            ['plane = FreeCAD.ActiveDocument.addObject("Part::Plane","Plane")',
                             'plane.Length = '+str(length),
                             'plane.Width = '+str(height),
                             'pl = FreeCAD.Placement()',
                             'pl.Rotation.Q='+rot,
                             'pl.Base = '+DraftVecUtils.toString(base),
                             'plane.Placement = pl',
                             'Draft.autogroup(plane)',
                             'FreeCAD.ActiveDocument.recompute()'])
            else:
                self.commit(translate("draft","Create Rectangle"),
                            ['pl = FreeCAD.Placement()',
                             'pl.Rotation.Q = '+rot,
                             'pl.Base = '+DraftVecUtils.toString(base),
                             'rec = Draft.makeRectangle(length='+str(length)+',height='+str(height)+',placement=pl,face='+fil+',support='+sup+')',
                             'Draft.autogroup(rec)',
                             'FreeCAD.ActiveDocument.recompute()'])
        except:
            print("Draft: error delaying commit")
        self.finish(cont=True)

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            self.point,ctrlPoint,info = getPoint(self,arg,mobile=True,noTracker=True)
            self.rect.update(self.point)
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if (arg["Position"] == self.pos):
                    self.finish()
                else:
                    if (not self.node) and (not self.support):
                        getSupport(arg)
                        self.point,ctrlPoint,info = getPoint(self,arg,mobile=True,noTracker=True)
                    if self.point:
                        self.ui.redraw()
                        self.appendPoint(self.point)

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        self.point = Vector(numx,numy,numz)
        self.appendPoint(self.point)

    def appendPoint(self,point):
        self.node.append(point)
        if (len(self.node) > 1):
            self.rect.update(point)
            self.createObject()
        else:
            FreeCAD.Console.PrintMessage(translate("draft", "Pick opposite point")+"\n")
            self.ui.setRelative()
            self.rect.setorigin(point)
            self.rect.on()
            if self.planetrack:
                self.planetrack.set(point)


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Rectangle',Rectangle())

