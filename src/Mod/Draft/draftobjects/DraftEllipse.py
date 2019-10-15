
def makeEllipse(majradius,minradius,placement=None,face=True,support=None):
    """makeEllipse(majradius,minradius,[placement],[face],[support]): makes
    an ellipse with the given major and minor radius, and optionally
    a placement."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","Ellipse")
    _Ellipse(obj)
    if minradius > majradius:
        majradius,minradius = minradius,majradius
    obj.MajorRadius = majradius
    obj.MinorRadius = minradius
    obj.Support = support
    if placement:
        obj.Placement = placement
    if gui:
        _ViewProviderDraft(obj.ViewObject)
        #if not face:
        #    obj.ViewObject.DisplayMode = "Wireframe"
        formatObject(obj)
        select(obj)

    return obj


class _Ellipse(_DraftObject):
    """The Circle object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"Ellipse")
        obj.addProperty("App::PropertyAngle","FirstAngle","Draft",QT_TRANSLATE_NOOP("App::Property","Start angle of the arc"))
        obj.addProperty("App::PropertyAngle","LastAngle","Draft",QT_TRANSLATE_NOOP("App::Property","End angle of the arc (for a full circle, give it same value as First Angle)"))
        obj.addProperty("App::PropertyLength","MinorRadius","Draft",QT_TRANSLATE_NOOP("App::Property","The minor radius of the ellipse"))
        obj.addProperty("App::PropertyLength","MajorRadius","Draft",QT_TRANSLATE_NOOP("App::Property","The major radius of the ellipse"))
        obj.addProperty("App::PropertyBool","MakeFace","Draft",QT_TRANSLATE_NOOP("App::Property","Create a face"))
        obj.addProperty("App::PropertyArea","Area","Draft",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.MakeFace = getParam("fillmode",True)

    def execute(self, obj):
        import Part
        plm = obj.Placement
        if obj.MajorRadius.Value < obj.MinorRadius.Value:
            FreeCAD.Console.PrintMessage(translate("Error: Major radius is smaller than the minor radius"))
            return
        if obj.MajorRadius.Value and obj.MinorRadius.Value:
            ell = Part.Ellipse(Vector(0,0,0),obj.MajorRadius.Value,obj.MinorRadius.Value)
            shape = ell.toShape()
            if hasattr(obj,"FirstAngle"):
                if obj.FirstAngle.Value != obj.LastAngle.Value:
                    a1 = obj.FirstAngle.getValueAs(FreeCAD.Units.Radian)
                    a2 = obj.LastAngle.getValueAs(FreeCAD.Units.Radian)
                    shape = Part.ArcOfEllipse(ell,a1,a2).toShape()
            shape = Part.Wire(shape)
            if shape.isClosed():
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


class Ellipse(Creator):
    """the Draft_Ellipse FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Ellipse',
                'Accel' : "E, L",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Ellipse", "Ellipse"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Ellipse", "Creates an ellipse. CTRL to snap")}

    def Activated(self):
        name = translate("draft","Ellipse")
        Creator.Activated(self,name)
        if self.ui:
            self.refpoint = None
            self.ui.pointUi(name)
            self.ui.extUi()
            self.call = self.view.addEventCallback("SoEvent",self.action)
            self.rect = rectangleTracker()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick first point")+"\n")

    def finish(self,closed=False,cont=False):
        """terminates the operation and closes the poly if asked"""
        Creator.finish(self)
        if self.ui:
            self.rect.off()
            self.rect.finalize()
        if self.ui:
            if self.ui.continueMode:
                self.Activated()

    def createObject(self):
        """creates the final object in the current doc"""
        p1 = self.node[0]
        p3 = self.node[-1]
        diagonal = p3.sub(p1)
        halfdiag = Vector(diagonal).multiply(0.5)
        center = p1.add(halfdiag)
        p2 = p1.add(DraftVecUtils.project(diagonal, plane.v))
        p4 = p1.add(DraftVecUtils.project(diagonal, plane.u))
        r1 = (p4.sub(p1).Length)/2
        r2 = (p2.sub(p1).Length)/2
        try:
            # building command string
            rot,sup,pts,fil = self.getStrings()
            if r2 > r1:
                r1,r2 = r2,r1
                m = FreeCAD.Matrix()
                m.rotateZ(math.pi/2)
                rot1 = FreeCAD.Rotation()
                rot1.Q = eval(rot)
                rot2 = FreeCAD.Placement(m)
                rot2 = rot2.Rotation
                rot = str((rot1.multiply(rot2)).Q)
            FreeCADGui.addModule("Draft")
            if Draft.getParam("UsePartPrimitives",False):
                # Use Part Primitive
                self.commit(translate("draft","Create Ellipse"),
                            ['import Part',
                             'ellipse = FreeCAD.ActiveDocument.addObject("Part::Ellipse","Ellipse")',
                             'ellipse.MajorRadius = '+str(r1),
                             'ellipse.MinorRadius = '+str(r2),
                             'pl = FreeCAD.Placement()',
                             'pl.Rotation.Q='+rot,
                             'pl.Base = '+DraftVecUtils.toString(center),
                             'ellipse.Placement = pl',
                             'Draft.autogroup(ellipse)',
                             'FreeCAD.ActiveDocument.recompute()'])
            else:
                self.commit(translate("draft","Create Ellipse"),
                            ['pl = FreeCAD.Placement()',
                             'pl.Rotation.Q = '+rot,
                             'pl.Base = '+DraftVecUtils.toString(center),
                             'ellipse = Draft.makeEllipse('+str(r1)+','+str(r2)+',placement=pl,face='+fil+',support='+sup+')',
                             'Draft.autogroup(ellipse)',
                             'FreeCAD.ActiveDocument.recompute()'])
        except:
            print("Draft: Error: Unable to create object.")
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
    FreeCADGui.addCommand('Draft_Ellipse',Ellipse())

