
def makePolygon(nfaces,radius=1,inscribed=True,placement=None,face=None,support=None):
    """makePolgon(nfaces,[radius],[inscribed],[placement],[face]): Creates a
    polygon object with the given number of faces and the radius.
    if inscribed is False, the polygon is circumscribed around a circle
    with the given radius, otherwise it is inscribed. If face is True,
    the resulting shape is displayed as a face, otherwise as a wireframe.
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if nfaces < 3: return None
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","Polygon")
    _Polygon(obj)
    obj.FacesNumber = nfaces
    obj.Radius = radius
    if face != None:
        obj.MakeFace = face
    if inscribed:
        obj.DrawMode = "inscribed"
    else:
        obj.DrawMode = "circumscribed"
    obj.Support = support
    if placement: obj.Placement = placement
    if gui:
        _ViewProviderDraft(obj.ViewObject)
        formatObject(obj)
        select(obj)

    return obj


class _Polygon(_DraftObject):
    """The Polygon object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"Polygon")
        obj.addProperty("App::PropertyInteger","FacesNumber","Draft",QT_TRANSLATE_NOOP("App::Property","Number of faces"))
        obj.addProperty("App::PropertyLength","Radius","Draft",QT_TRANSLATE_NOOP("App::Property","Radius of the control circle"))
        obj.addProperty("App::PropertyEnumeration","DrawMode","Draft",QT_TRANSLATE_NOOP("App::Property","How the polygon must be drawn from the control circle"))
        obj.addProperty("App::PropertyLength","FilletRadius","Draft",QT_TRANSLATE_NOOP("App::Property","Radius to use to fillet the corners"))
        obj.addProperty("App::PropertyLength","ChamferSize","Draft",QT_TRANSLATE_NOOP("App::Property","Size of the chamfer to give to the corners"))
        obj.addProperty("App::PropertyBool","MakeFace","Draft",QT_TRANSLATE_NOOP("App::Property","Create a face"))
        obj.addProperty("App::PropertyArea","Area","Draft",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.MakeFace = getParam("fillmode",True)
        obj.DrawMode = ['inscribed','circumscribed']
        obj.FacesNumber = 0
        obj.Radius = 1

    def execute(self, obj):
        if (obj.FacesNumber >= 3) and (obj.Radius.Value > 0):
            import Part, DraftGeomUtils
            plm = obj.Placement
            angle = (math.pi*2)/obj.FacesNumber
            if obj.DrawMode == 'inscribed':
                delta = obj.Radius.Value
            else:
                delta = obj.Radius.Value/math.cos(angle/2.0)
            pts = [Vector(delta,0,0)]
            for i in range(obj.FacesNumber-1):
                ang = (i+1)*angle
                pts.append(Vector(delta*math.cos(ang),delta*math.sin(ang),0))
            pts.append(pts[0])
            shape = Part.makePolygon(pts)
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


class Polygon(Creator):
    """the Draft_Polygon FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Polygon',
                'Accel' : "P, G",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Polygon", "Polygon"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Polygon", "Creates a regular polygon. CTRL to snap, SHIFT to constrain")}

    def Activated(self):
        name = translate("draft","Polygon")
        Creator.Activated(self,name)
        if self.ui:
            self.step = 0
            self.center = None
            self.rad = None
            self.tangents = []
            self.tanpoints = []
            self.ui.pointUi(name)
            self.ui.extUi()
            self.ui.numFaces.show()
            self.ui.numFacesLabel.show()
            self.altdown = False
            self.ui.sourceCmd = self
            self.arctrack = arcTracker()
            self.call = self.view.addEventCallback("SoEvent",self.action)
            FreeCAD.Console.PrintMessage(translate("draft", "Pick center point")+"\n")

    def finish(self,closed=False,cont=False):
        """finishes the arc"""
        Creator.finish(self)
        if self.ui:
            self.arctrack.finalize()
            self.doc.recompute()
            if self.ui.continueMode:
                self.Activated()

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event":
            self.point,ctrlPoint,info = getPoint(self,arg)
            # this is to make sure radius is what you see on screen
            if self.center and DraftVecUtils.dist(self.point,self.center) > 0:
                viewdelta = DraftVecUtils.project(self.point.sub(self.center), plane.axis)
                if not DraftVecUtils.isNull(viewdelta):
                    self.point = self.point.add(viewdelta.negative())
            if (self.step == 0): # choose center
                if hasMod(arg,MODALT):
                    if not self.altdown:
                        self.altdown = True
                        self.ui.switchUi(True)
                else:
                    if self.altdown:
                        self.altdown = False
                        self.ui.switchUi(False)
            else: # choose radius
                if len(self.tangents) == 2:
                    cir = DraftGeomUtils.circleFrom2tan1pt(self.tangents[0], self.tangents[1], self.point)
                    self.center = DraftGeomUtils.findClosestCircle(self.point,cir).Center
                    self.arctrack.setCenter(self.center)
                elif self.tangents and self.tanpoints:
                    cir = DraftGeomUtils.circleFrom1tan2pt(self.tangents[0], self.tanpoints[0], self.point)
                    self.center = DraftGeomUtils.findClosestCircle(self.point,cir).Center
                    self.arctrack.setCenter(self.center)
                if hasMod(arg,MODALT):
                    if not self.altdown:
                        self.altdown = True
                    snapped = self.view.getObjectInfo((arg["Position"][0],arg["Position"][1]))
                    if snapped:
                        ob = self.doc.getObject(snapped['Object'])
                        num = int(snapped['Component'].lstrip('Edge'))-1
                        ed = ob.Shape.Edges[num]
                        if len(self.tangents) == 2:
                            cir = DraftGeomUtils.circleFrom3tan(self.tangents[0], self.tangents[1], ed)
                            cl = DraftGeomUtils.findClosestCircle(self.point,cir)
                            self.center = cl.Center
                            self.rad = cl.Radius
                            self.arctrack.setCenter(self.center)
                        else:
                            self.rad = self.center.add(DraftGeomUtils.findDistance(self.center,ed).sub(self.center)).Length
                    else:
                        self.rad = DraftVecUtils.dist(self.point,self.center)
                else:
                    if self.altdown:
                        self.altdown = False
                    self.rad = DraftVecUtils.dist(self.point,self.center)
                self.ui.setRadiusValue(self.rad,'Length')
                self.arctrack.setRadius(self.rad)

            redraw3DView()

        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if self.point:
                    if (self.step == 0): # choose center
                        if (not self.node) and (not self.support):
                            getSupport(arg)
                            self.point,ctrlPoint,info = getPoint(self,arg)
                        if hasMod(arg,MODALT):
                            snapped=self.view.getObjectInfo((arg["Position"][0],arg["Position"][1]))
                            if snapped:
                                ob = self.doc.getObject(snapped['Object'])
                                num = int(snapped['Component'].lstrip('Edge'))-1
                                ed = ob.Shape.Edges[num]
                                self.tangents.append(ed)
                                if len(self.tangents) == 2:
                                    self.arctrack.on()
                                    self.ui.radiusUi()
                                    self.step = 1
                                    FreeCAD.Console.PrintMessage(translate("draft", "Pick radius")+"\n")
                        else:
                            if len(self.tangents) == 1:
                                self.tanpoints.append(self.point)
                            else:
                                self.center = self.point
                                self.node = [self.point]
                                self.arctrack.setCenter(self.center)
                            self.arctrack.on()
                            self.ui.radiusUi()
                            self.step = 1
                            FreeCAD.Console.PrintMessage(translate("draft", "Pick radius")+"\n")
                            if self.planetrack:
                                self.planetrack.set(self.point)
                    elif (self.step == 1): # choose radius
                        self.drawPolygon()

    def drawPolygon(self):
        """actually draws the FreeCAD object"""
        rot,sup,pts,fil = self.getStrings()
        FreeCADGui.addModule("Draft")
        if Draft.getParam("UsePartPrimitives",False):
            FreeCADGui.addModule("Part")
            self.commit(translate("draft","Create Polygon"),
                        ['pl=FreeCAD.Placement()',
                         'pl.Rotation.Q=' + rot,
                         'pl.Base=' + DraftVecUtils.toString(self.center),
                         'pol = FreeCAD.ActiveDocument.addObject("Part::RegularPolygon","RegularPolygon")',
                         'pol.Polygon = ' + str(self.ui.numFaces.value()),
                         'pol.Circumradius = ' + str(self.rad),
                         'pol.Placement = pl',
                         'Draft.autogroup(pol)',
                         'FreeCAD.ActiveDocument.recompute()'])
        else:
            # building command string
            self.commit(translate("draft","Create Polygon"),
                        ['pl=FreeCAD.Placement()',
                         'pl.Rotation.Q = ' + rot,
                         'pl.Base = ' + DraftVecUtils.toString(self.center),
                         'pol = Draft.makePolygon(' + str(self.ui.numFaces.value()) + ',radius=' + str(self.rad) + ',inscribed=True,placement=pl,face=' + fil + ',support=' + sup + ')',
                         'Draft.autogroup(pol)',
                         'FreeCAD.ActiveDocument.recompute()'])
        self.finish(cont=True)

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        self.center = Vector(numx,numy,numz)
        self.node = [self.center]
        self.arctrack.setCenter(self.center)
        self.arctrack.on()
        self.ui.radiusUi()
        self.step = 1
        self.ui.radiusValue.setFocus()
        FreeCAD.Console.PrintMessage(translate("draft", "Pick radius")+"\n")

    def numericRadius(self,rad):
        """this function gets called by the toolbar when valid radius have been entered there"""
        self.rad = rad
        if len(self.tangents) == 2:
            cir = DraftGeomUtils.circleFrom2tan1rad(self.tangents[0], self.tangents[1], rad)
            if self.center:
                self.center = DraftGeomUtils.findClosestCircle(self.center,cir).Center
            else:
                self.center = cir[-1].Center
        elif self.tangents and self.tanpoints:
            cir = DraftGeomUtils.circleFrom1tan1pt1rad(self.tangents[0],self.tanpoints[0],rad)
            if self.center:
                self.center = DraftGeomUtils.findClosestCircle(self.center,cir).Center
            else:
                self.center = cir[-1].Center
        self.drawPolygon()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Polygon',Polygon())

