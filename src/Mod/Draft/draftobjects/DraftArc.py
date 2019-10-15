
class Arc(Creator):
    """the Draft_Arc FreeCAD command definition"""

    def __init__(self):
        self.closedCircle=False
        self.featureName = "Arc"

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Arc',
                'Accel' : "A, R",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Arc", "Arc"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Arc", "Creates an arc by center point and radius. CTRL to snap, SHIFT to constrain")}

    def Activated(self):
        Creator.Activated(self,self.featureName)
        if self.ui:
            self.step = 0
            self.center = None
            self.rad = None
            self.angle = 0 # angle inscribed by arc
            self.tangents = []
            self.tanpoints = []
            if self.featureName == "Arc": self.ui.arcUi()
            else: self.ui.circleUi()
            self.altdown = False
            self.ui.sourceCmd = self
            self.linetrack = lineTracker(dotted=True)
            self.arctrack = arcTracker()
            self.call = self.view.addEventCallback("SoEvent",self.action)
            FreeCAD.Console.PrintMessage(translate("draft", "Pick center point")+"\n")

    def finish(self,closed=False,cont=False):
        """finishes the arc"""
        Creator.finish(self)
        if self.ui:
            self.linetrack.finalize()
            self.arctrack.finalize()
            self.doc.recompute()
        if self.ui:
            if self.ui.continueMode:
                self.Activated()

    def updateAngle(self, angle):
        # previous absolute angle
        lastangle = self.firstangle + self.angle
        if lastangle <= -2*math.pi: lastangle += 2*math.pi
        if lastangle >= 2*math.pi: lastangle -= 2*math.pi
        # compute delta = change in angle:
        d0 = angle-lastangle
        d1 = d0 + 2*math.pi
        d2 = d0 - 2*math.pi
        if abs(d0) < min(abs(d1), abs(d2)):
            delta = d0
        elif abs(d1) < abs(d2):
            delta = d1
        else:
            delta = d2
        newangle = self.angle + delta
        # normalize angle, preserving direction
        if newangle >= 2*math.pi: newangle -= 2*math.pi
        if newangle <= -2*math.pi: newangle += 2*math.pi
        self.angle = newangle

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
            elif (self.step == 1): # choose radius
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
                    if info:
                        ob = self.doc.getObject(info['Object'])
                        num = int(info['Component'].lstrip('Edge'))-1
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
                self.ui.setRadiusValue(self.rad, "Length")
                self.arctrack.setRadius(self.rad)
                self.linetrack.p1(self.center)
                self.linetrack.p2(self.point)
                self.linetrack.on()
            elif (self.step == 2): # choose first angle
                currentrad = DraftVecUtils.dist(self.point,self.center)
                if currentrad != 0:
                    angle = DraftVecUtils.angle(plane.u, self.point.sub(self.center), plane.axis)
                else: angle = 0
                self.linetrack.p2(DraftVecUtils.scaleTo(self.point.sub(self.center),self.rad).add(self.center))
                self.ui.setRadiusValue(math.degrees(angle),unit="Angle")
                self.firstangle = angle
            else: # choose second angle
                currentrad = DraftVecUtils.dist(self.point,self.center)
                if currentrad != 0:
                    angle = DraftVecUtils.angle(plane.u, self.point.sub(self.center), plane.axis)
                else: angle = 0
                self.linetrack.p2(DraftVecUtils.scaleTo(self.point.sub(self.center),self.rad).add(self.center))
                self.updateAngle(angle)
                self.ui.setRadiusValue(math.degrees(self.angle),unit="Angle")
                self.arctrack.setApertureAngle(self.angle)

            redraw3DView()

        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if self.point:
                    if (self.step == 0): # choose center
                        if not self.support:
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
                                    self.ui.setNextFocus()
                                    self.linetrack.on()
                                    FreeCAD.Console.PrintMessage(translate("draft", "Pick radius")+"\n")
                        else:
                            if len(self.tangents) == 1:
                                self.tanpoints.append(self.point)
                            else:
                                self.center = self.point
                                self.node = [self.point]
                                self.arctrack.setCenter(self.center)
                                self.linetrack.p1(self.center)
                                self.linetrack.p2(self.view.getPoint(arg["Position"][0],arg["Position"][1]))
                            self.arctrack.on()
                            self.ui.radiusUi()
                            self.step = 1
                            self.ui.setNextFocus()
                            self.linetrack.on()
                            FreeCAD.Console.PrintMessage(translate("draft", "Pick radius")+"\n")
                            if self.planetrack:
                                self.planetrack.set(self.point)
                    elif (self.step == 1): # choose radius
                        if self.closedCircle:
                            self.drawArc()
                        else:
                            self.ui.labelRadius.setText("Start angle")
                            self.ui.radiusValue.setText(FreeCAD.Units.Quantity(0,FreeCAD.Units.Angle).UserString)
                            self.linetrack.p1(self.center)
                            self.linetrack.on()
                            self.step = 2
                            FreeCAD.Console.PrintMessage(translate("draft", "Pick start angle")+"\n")
                    elif (self.step == 2): # choose first angle
                        self.ui.labelRadius.setText("Aperture")
                        self.step = 3
                        # scale center->point vector for proper display
                        # u = DraftVecUtils.scaleTo(self.point.sub(self.center), self.rad) obsolete?
                        self.arctrack.setStartAngle(self.firstangle)
                        FreeCAD.Console.PrintMessage(translate("draft", "Pick aperture")+"\n")
                    else: # choose second angle
                        self.step = 4
                        self.drawArc()

    def drawArc(self):
        """actually draws the FreeCAD object"""
        rot,sup,pts,fil = self.getStrings()
        if self.closedCircle:
            try:
                FreeCADGui.addModule("Draft")
                if Draft.getParam("UsePartPrimitives",False):
                    # use primitive
                    self.commit(translate("draft","Create Circle"),
                                ['circle = FreeCAD.ActiveDocument.addObject("Part::Circle","Circle")',
                                 'circle.Radius = '+str(self.rad),
                                 'pl = FreeCAD.Placement()',
                                 'pl.Rotation.Q = '+rot,
                                 'pl.Base = '+DraftVecUtils.toString(self.center),
                                 'circle.Placement = pl',
                                 'Draft.autogroup(circle)',
                                 'FreeCAD.ActiveDocument.recompute()'])
                else:
                    # building command string
                    FreeCADGui.addModule("Draft")
                    self.commit(translate("draft","Create Circle"),
                                ['pl=FreeCAD.Placement()',
                                 'pl.Rotation.Q='+rot,
                                 'pl.Base='+DraftVecUtils.toString(self.center),
                                 'circle = Draft.makeCircle(radius='+str(self.rad)+',placement=pl,face='+fil+',support='+sup+')',
                                 'Draft.autogroup(circle)',
                                 'FreeCAD.ActiveDocument.recompute()'])
            except:
                print("Draft: error delaying commit")
        else:
            sta = math.degrees(self.firstangle)
            end = math.degrees(self.firstangle+self.angle)
            if end < sta: sta,end = end,sta
            while True:
                if sta > 360:
                    sta = sta - 360
                elif end > 360:
                    end = end - 360
                else:
                    break
            try:
                FreeCADGui.addModule("Draft")
                if Draft.getParam("UsePartPrimitives",False):
                    # use primitive
                    self.commit(translate("draft","Create Arc"),
                                ['circle = FreeCAD.ActiveDocument.addObject("Part::Circle","Circle")',
                                 'circle.Radius = '+str(self.rad),
                                 'circle.Angle0 = '+str(sta),
                                 'circle.Angle1 = '+str(end),
                                 'pl = FreeCAD.Placement()',
                                 'pl.Rotation.Q = '+rot,
                                 'pl.Base = '+DraftVecUtils.toString(self.center),
                                 'circle.Placement = pl',
                                 'Draft.autogroup(circle)',
                                 'FreeCAD.ActiveDocument.recompute()'])
                else:
                    # building command string
                    self.commit(translate("draft","Create Arc"),
                                ['pl=FreeCAD.Placement()',
                                 'pl.Rotation.Q='+rot,
                                 'pl.Base='+DraftVecUtils.toString(self.center),
                                 'circle = Draft.makeCircle(radius='+str(self.rad)+',placement=pl,face='+fil+',startangle='+str(sta)+',endangle='+str(end)+',support='+sup+')',
                                 'Draft.autogroup(circle)',
                                 'FreeCAD.ActiveDocument.recompute()'])
            except:
                    print("Draft: error delaying commit")
        self.finish(cont=True)

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        self.center = Vector(numx,numy,numz)
        self.node = [self.center]
        self.arctrack.setCenter(self.center)
        self.arctrack.on()
        self.ui.radiusUi()
        self.step = 1
        self.ui.setNextFocus()
        FreeCAD.Console.PrintMessage(translate("draft", "Pick radius")+"\n")

    def numericRadius(self,rad):
        """this function gets called by the toolbar when valid radius have been entered there"""
        if (self.step == 1):
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
            if self.closedCircle:
                self.drawArc()
            else:
                self.step = 2
                self.arctrack.setCenter(self.center)
                self.ui.labelRadius.setText(translate("draft", "Start Angle"))
                self.linetrack.p1(self.center)
                self.linetrack.on()
                self.ui.radiusValue.setText("")
                self.ui.radiusValue.setFocus()
                FreeCAD.Console.PrintMessage(translate("draft", "Pick start angle")+"\n")
        elif (self.step == 2):
            self.ui.labelRadius.setText(translate("draft", "Aperture"))
            self.firstangle = math.radians(rad)
            if DraftVecUtils.equals(plane.axis, Vector(1,0,0)): u = Vector(0,self.rad,0)
            else: u = DraftVecUtils.scaleTo(Vector(1,0,0).cross(plane.axis), self.rad)
            urotated = DraftVecUtils.rotate(u, math.radians(rad), plane.axis)
            self.arctrack.setStartAngle(self.firstangle)
            self.step = 3
            self.ui.radiusValue.setText("")
            self.ui.radiusValue.setFocus()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick aperture angle")+"\n")
        else:
            self.updateAngle(rad)
            self.angle = math.radians(rad)
            self.step = 4
            self.drawArc()


class Draft_Arc_3Points:
    def GetResources(self):
        return {'Pixmap'  : "Draft_Arc_3Points.svg",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Arc_3Points", "Arc 3 points"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Arc_3Points", "Creates an arc by 3 points"),
                'Accel'   : 'A,T'}

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        import DraftTrackers
        self.points = []
        self.normal = None
        self.tracker = DraftTrackers.arcTracker()
        self.tracker.autoinvert = False
        if hasattr(FreeCAD,"DraftWorkingPlane"):
            FreeCAD.DraftWorkingPlane.setup()
        FreeCADGui.Snapper.getPoint(callback=self.getPoint,movecallback=self.drawArc)

    def getPoint(self,point,info):
        if not point: # cancelled
            self.tracker.off()
            return
        if not(point in self.points): # avoid same point twice
            self.points.append(point)
        if len(self.points) < 3:
            if len(self.points) == 2:
                self.tracker.on()
            FreeCADGui.Snapper.getPoint(last=self.points[-1],callback=self.getPoint,movecallback=self.drawArc)
        else:
            import Part
            e = Part.Arc(self.points[0],self.points[1],self.points[2]).toShape()
            if Draft.getParam("UsePartPrimitives",False):
                o = FreeCAD.ActiveDocument.addObject("Part::Feature","Arc")
                o.Shape = e
            else:
                radius = e.Curve.Radius
                rot = FreeCAD.Rotation(e.Curve.XAxis,e.Curve.YAxis,e.Curve.Axis,"ZXY")
                placement = FreeCAD.Placement(e.Curve.Center,rot)
                start = e.FirstParameter
                end = e.LastParameter/math.pi*180
                Draft.makeCircle(radius,placement,startangle=start,endangle=end)
            self.tracker.off()
            FreeCAD.ActiveDocument.recompute()

    def drawArc(self,point,info):
        if len(self.points) == 2:
            if point.sub(self.points[1]).Length > 0.001:
                self.tracker.setBy3Points(self.points[0],self.points[1],point)


class CommandArcGroup:
    def GetCommands(self):
        return tuple(['Draft_Arc','Draft_Arc_3Points'])
    def GetResources(self):
        return { 'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ArcTools",'Arc tools'),
                 'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_ArcTools",'Arc tools')
               }
    def IsActive(self):
        return not FreeCAD.ActiveDocument is None


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Arc',Arc())
    FreeCADGui.addCommand('Draft_Arc_3Points',Draft_Arc_3Points())
    FreeCADGui.addCommand('Draft_ArcTools', CommandArcGroup())

