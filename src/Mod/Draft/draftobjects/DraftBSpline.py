

def makeBSpline(pointslist,closed=False,placement=None,face=None,support=None):
    """makeBSpline(pointslist,[closed],[placement]): Creates a B-Spline object
    from the given list of vectors. If closed is True or first
    and last points are identical, the wire is closed. If face is
    true (and wire is closed), the wire will appear filled. Instead of
    a pointslist, you can also pass a Part Wire."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if not isinstance(pointslist,list):
        nlist = []
        for v in pointslist.Vertexes:
            nlist.append(v.Point)
        pointslist = nlist
    if len(pointslist) < 2:
        FreeCAD.Console.PrintError(translate("draft","Draft.makeBSpline: not enough points")+"\n")
        return
    if (pointslist[0] == pointslist[-1]):
        if len(pointslist) > 2:
            closed = True
            pointslist.pop()
            FreeCAD.Console.PrintWarning(translate("draft","Draft.makeBSpline: Equal endpoints forced Closed")+"\n")
        else:                                                                            # len == 2 and first == last   GIGO
            FreeCAD.Console.PrintError(translate("draft","Draft.makeBSpline: Invalid pointslist")+"\n")
            return
    # should have sensible parms from here on
    if placement: typecheck([(placement,FreeCAD.Placement)], "makeBSpline")
    if len(pointslist) == 2: fname = "Line"
    else: fname = "BSpline"
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython",fname)
    _BSpline(obj)
    obj.Closed = closed
    obj.Points = pointslist
    obj.Support = support
    if face != None:
        obj.MakeFace = face
    if placement: obj.Placement = placement
    if gui:
        _ViewProviderWire(obj.ViewObject)
        formatObject(obj)
        select(obj)

    return obj


class _BSpline(_DraftObject):
    """The BSpline object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"BSpline")
        obj.addProperty("App::PropertyVectorList","Points","Draft", QT_TRANSLATE_NOOP("App::Property","The points of the B-spline"))
        obj.addProperty("App::PropertyBool","Closed","Draft",QT_TRANSLATE_NOOP("App::Property","If the B-spline is closed or not"))
        obj.addProperty("App::PropertyBool","MakeFace","Draft",QT_TRANSLATE_NOOP("App::Property","Create a face if this spline is closed"))
        obj.addProperty("App::PropertyArea","Area","Draft",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.MakeFace = getParam("fillmode",True)
        obj.Closed = False
        obj.Points = []
        self.assureProperties(obj)

    def assureProperties(self, obj): # for Compatibility with older versions
        if not hasattr(obj, "Parameterization"):
            obj.addProperty("App::PropertyFloat","Parameterization","Draft",QT_TRANSLATE_NOOP("App::Property","Parameterization factor"))
            obj.Parameterization = 1.0
            self.knotSeq = []

    def parameterization (self, pts, a, closed):
        # Computes a knot Sequence for a set of points
        # fac (0-1) : parameterization factor
        # fac=0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length
        if closed: # we need to add the first point as the end point
            pts.append(pts[0])
        params = [0]
        for i in range(1,len(pts)):
            p = pts[i].sub(pts[i-1])
            pl = pow(p.Length,a)
            params.append(params[-1] + pl)
        return params

    def onChanged(self, fp, prop):
        if prop == "Parameterization":
            if fp.Parameterization < 0.:
                fp.Parameterization = 0.
            if fp.Parameterization > 1.0:
                fp.Parameterization = 1.0

    def execute(self, obj):
        import Part
        self.assureProperties(obj)
        if obj.Points:
            self.knotSeq = self.parameterization(obj.Points, obj.Parameterization, obj.Closed)
            plm = obj.Placement
            if obj.Closed and (len(obj.Points) > 2):
                if obj.Points[0] == obj.Points[-1]:  # should not occur, but OCC will crash
                    FreeCAD.Console.PrintError(translate('draft',  "_BSpline.createGeometry: Closed with same first/last Point. Geometry not updated.")+"\n")
                    return
                spline = Part.BSplineCurve()
                spline.interpolate(obj.Points, PeriodicFlag = True, Parameters = self.knotSeq)
                # DNC: bug fix: convert to face if closed
                shape = Part.Wire(spline.toShape())
                # Creating a face from a closed spline cannot be expected to always work
                # Usually, if the spline is not flat the call of Part.Face() fails
                try:
                    if hasattr(obj,"MakeFace"):
                        if obj.MakeFace:
                            shape = Part.Face(shape)
                    else:
                        shape = Part.Face(shape)
                except Part.OCCError:
                    pass
                obj.Shape = shape
                if hasattr(obj,"Area") and hasattr(shape,"Area"):
                    obj.Area = shape.Area
            else:
                spline = Part.BSplineCurve()
                spline.interpolate(obj.Points, PeriodicFlag = False, Parameters = self.knotSeq)
                shape = spline.toShape()
                obj.Shape = shape
                if hasattr(obj,"Area") and hasattr(shape,"Area"):
                    obj.Area = shape.Area
            obj.Placement = plm
        obj.positionBySupport()

# for compatibility with older versions
_ViewProviderBSpline = _ViewProviderWire


class BSpline(Line):
    """a FreeCAD command for creating a B-spline"""

    def __init__(self):
        Line.__init__(self,wiremode=True)

    def GetResources(self):
        return {'Pixmap'  : 'Draft_BSpline',
                'Accel' : "B, S",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_BSpline", "B-spline"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_BSpline", "Creates a multiple-point B-spline. CTRL to snap, SHIFT to constrain")}

    def Activated(self):
        Line.Activated(self,name=translate("draft","BSpline"))
        if self.doc:
            self.bsplinetrack = bsplineTracker()

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            self.point,ctrlPoint,info = getPoint(self,arg,noTracker=True)
            self.bsplinetrack.update(self.node + [self.point])
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if (arg["Position"] == self.pos):
                    self.finish(False,cont=True)
                else:
                    if (not self.node) and (not self.support):
                        getSupport(arg)
                        self.point,ctrlPoint,info = getPoint(self,arg,noTracker=True)
                    if self.point:
                        self.ui.redraw()
                        self.pos = arg["Position"]
                        self.node.append(self.point)
                        self.drawUpdate(self.point)
                        if (not self.isWire and len(self.node) == 2):
                            self.finish(False,cont=True)
                        if (len(self.node) > 2):
                            # DNC: allows to close the curve
                            # by placing ends close to each other
                            # with tol = Draft tolerance
                            # old code has been to insensitive
                            if ((self.point-self.node[0]).Length < Draft.tolerance()):
                                self.undolast()
                                self.finish(True,cont=True)
                                FreeCAD.Console.PrintMessage(translate("draft", "Spline has been closed")+"\n")

    def undolast(self):
        """undoes last line segment"""
        if (len(self.node) > 1):
            self.node.pop()
            self.bsplinetrack.update(self.node)
            spline = Part.BSplineCurve()
            spline.interpolate(self.node, False)
            self.obj.Shape = spline.toShape()
            FreeCAD.Console.PrintMessage(translate("draft", "Last point has been removed")+"\n")

    def drawUpdate(self,point):
        if (len(self.node) == 1):
            self.bsplinetrack.on()
            if self.planetrack:
                self.planetrack.set(self.node[0])
            FreeCAD.Console.PrintMessage(translate("draft", "Pick next point")+"\n")
        else:
            spline = Part.BSplineCurve()
            spline.interpolate(self.node, False)
            self.obj.Shape = spline.toShape()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick next point, or Finish (shift-F) or close (o)")+"\n")

    def finish(self,closed=False,cont=False):
        """terminates the operation and closes the poly if asked"""
        if self.ui:
            self.bsplinetrack.finalize()
        if not Draft.getParam("UiMode",1):
            FreeCADGui.Control.closeDialog()
        if self.obj:
            # remove temporary object, if any
            old = self.obj.Name
            todo.delay(self.doc.removeObject,old)
        if (len(self.node) > 1):
            try:
                # building command string
                rot,sup,pts,fil = self.getStrings()
                FreeCADGui.addModule("Draft")
                self.commit(translate("draft","Create B-spline"),
                            ['points = '+pts,
                             'spline = Draft.makeBSpline(points,closed='+str(closed)+',face='+fil+',support='+sup+')',
                             'Draft.autogroup(spline)',
                             'FreeCAD.ActiveDocument.recompute()'])
            except:
                print("Draft: error delaying commit")
        Creator.finish(self)
        if self.ui:
            if self.ui.continueMode:
                self.Activated()

if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_BSpline',BSpline())

