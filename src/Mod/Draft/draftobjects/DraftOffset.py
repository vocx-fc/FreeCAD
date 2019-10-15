
def offset(obj,delta,copy=False,bind=False,sym=False,occ=False):
    """offset(object,delta,[copymode],[bind]): offsets the given wire by
    applying the given delta Vector to its first vertex. If copymode is
    True, another object is created, otherwise the same object gets
    offsetted. If bind is True, and provided the wire is open, the original
    and the offsetted wires will be bound by their endpoints, forming a face
    if sym is True, bind must be true too, and the offset is made on both
    sides, the total width being the given delta length. If offsetting a
    BSpline, the delta must not be a Vector but a list of Vectors, one for
    each node of the spline."""
    import Part, DraftGeomUtils
    newwire = None
    delete = None

    if getType(obj) in ["Sketch","Part"]:
        copy = True
        print("the offset tool is currently unable to offset a non-Draft object directly - Creating a copy")

    def getRect(p,obj):
        """returns length,height,placement"""
        pl = obj.Placement.copy()
        pl.Base = p[0]
        diag = p[2].sub(p[0])
        bb = p[1].sub(p[0])
        bh = p[3].sub(p[0])
        nb = DraftVecUtils.project(diag,bb)
        nh = DraftVecUtils.project(diag,bh)
        if obj.Length.Value < 0: l = -nb.Length
        else: l = nb.Length
        if obj.Height.Value < 0: h = -nh.Length
        else: h = nh.Length
        return l,h,pl

    def getRadius(obj,delta):
        """returns a new radius for a regular polygon"""
        an = math.pi/obj.FacesNumber
        nr = DraftVecUtils.rotate(delta,-an)
        nr.multiply(1/math.cos(an))
        nr = obj.Shape.Vertexes[0].Point.add(nr)
        nr = nr.sub(obj.Placement.Base)
        nr = nr.Length
        if obj.DrawMode == "inscribed":
            return nr
        else:
            return nr * math.cos(math.pi/obj.FacesNumber)

    newwire = None
    if getType(obj) == "Circle":
        pass
    elif getType(obj) == "BSpline":
        pass
    else:
        if sym:
            d1 = Vector(delta).multiply(0.5)
            d2 = d1.negative()
            n1 = DraftGeomUtils.offsetWire(obj.Shape,d1)
            n2 = DraftGeomUtils.offsetWire(obj.Shape,d2)
        else:
            if isinstance(delta,float) and (len(obj.Shape.Edges) == 1):
                # circle
                c = obj.Shape.Edges[0].Curve
                nc = Part.Circle(c.Center,c.Axis,delta)
                if len(obj.Shape.Vertexes) > 1:
                    nc = Part.ArcOfCircle(nc,obj.Shape.Edges[0].FirstParameter,obj.Shape.Edges[0].LastParameter)
                newwire = Part.Wire(nc.toShape())
                p = []
            else:
                newwire = DraftGeomUtils.offsetWire(obj.Shape,delta)
                if DraftGeomUtils.hasCurves(newwire) and copy:
                    p = []
                else:
                    p = DraftGeomUtils.getVerts(newwire)
    if occ:
        newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
        newobj.Shape = DraftGeomUtils.offsetWire(obj.Shape,delta,occ=True)
        formatObject(newobj,obj)
        if not copy:
            delete = obj.Name
    elif bind:
        if not DraftGeomUtils.isReallyClosed(obj.Shape):
            if sym:
                s1 = n1
                s2 = n2
            else:
                s1 = obj.Shape
                s2 = newwire
            if s1 and s2:
                w1 = s1.Edges
                w2 = s2.Edges
                w3 = Part.LineSegment(s1.Vertexes[0].Point,s2.Vertexes[0].Point).toShape()
                w4 = Part.LineSegment(s1.Vertexes[-1].Point,s2.Vertexes[-1].Point).toShape()
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
                newobj.Shape = Part.Face(Part.Wire(w1+[w3]+w2+[w4]))
            else:
                print("Draft.offset: Unable to bind wires")
        else:
            newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
            newobj.Shape = Part.Face(obj.Shape.Wires[0])
        if not copy:
            delete = obj.Name
    elif copy:
        newobj = None
        if sym: return None
        if getType(obj) == "Wire":
            if p:
                newobj = makeWire(p)
                newobj.Closed = obj.Closed
            elif newwire:
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
                newobj.Shape = newwire
            else:
                print("Draft.offset: Unable to duplicate this object")
        elif getType(obj) == "Rectangle":
            if p:
                length,height,plac = getRect(p,obj)
                newobj = makeRectangle(length,height,plac)
            elif newwire:
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
                newobj.Shape = newwire
            else:
                print("Draft.offset: Unable to duplicate this object")
        elif getType(obj) == "Circle":
            pl = obj.Placement
            newobj = makeCircle(delta)
            newobj.FirstAngle = obj.FirstAngle
            newobj.LastAngle = obj.LastAngle
            newobj.Placement = pl
        elif getType(obj) == "Polygon":
            pl = obj.Placement
            newobj = makePolygon(obj.FacesNumber)
            newobj.Radius = getRadius(obj,delta)
            newobj.DrawMode = obj.DrawMode
            newobj.Placement = pl
        elif getType(obj) == "BSpline":
            newobj = makeBSpline(delta)
            newobj.Closed = obj.Closed
        else:
            # try to offset anyway
            try:
                if p:
                    newobj = makeWire(p)
                    newobj.Closed = obj.Shape.isClosed()
            except Part.OCCError:
                pass
            if not(newobj) and newwire:
                newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Offset")
                newobj.Shape = newwire
            else:
                print("Draft.offset: Unable to create an offset")
        if newobj:
            formatObject(newobj,obj)
    else:
        newobj = None
        if sym: return None
        if getType(obj) == "Wire":
            if obj.Base or obj.Tool:
                FreeCAD.Console.PrintWarning("Warning: object history removed\n")
                obj.Base = None
                obj.Tool = None
            obj.Points = p
        elif getType(obj) == "BSpline":
            #print(delta)
            obj.Points = delta
            #print("done")
        elif getType(obj) == "Rectangle":
            length,height,plac = getRect(p,obj)
            obj.Placement = plac
            obj.Length = length
            obj.Height = height
        elif getType(obj) == "Circle":
            obj.Radius = delta
        elif getType(obj) == "Polygon":
            obj.Radius = getRadius(obj,delta)
        elif getType(obj) == 'Part':
            print("unsupported object") # TODO
        newobj = obj
    if copy and getParam("selectBaseObjects",False):
        select(newobj)
    else:
        select(obj)
    if delete:
        FreeCAD.ActiveDocument.removeObject(delete)
    return newobj


class Offset(Modifier):
    """The Draft_Offset FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Offset',
                'Accel' : "O, S",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Offset", "Offset"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Offset", "Offsets the active object. CTRL to snap, SHIFT to constrain, ALT to copy")}

    def Activated(self):
        self.running = False
        Modifier.Activated(self,"Offset")
        self.ghost = None
        self.linetrack = None
        self.arctrack = None
        if self.ui:
            if not FreeCADGui.Selection.getSelection():
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Select an object to offset")+"\n")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
            elif len(FreeCADGui.Selection.getSelection()) > 1:
                FreeCAD.Console.PrintWarning(translate("draft", "Offset only works on one object at a time")+"\n")
            else:
                self.proceed()

    def proceed(self):
        if self.call: self.view.removeEventCallback("SoEvent",self.call)
        self.sel = FreeCADGui.Selection.getSelection()[0]
        if not self.sel.isDerivedFrom("Part::Feature"):
            FreeCAD.Console.PrintWarning(translate("draft", "Cannot offset this object type")+"\n")
            self.finish()
        else:
            self.step = 0
            self.dvec = None
            self.npts = None
            self.constrainSeg = None
            self.ui.offsetUi()
            self.linetrack = lineTracker()
            self.faces = False
            self.shape = self.sel.Shape
            self.mode = None
            if Draft.getType(self.sel) in ["Circle","Arc"]:
                self.ghost = arcTracker()
                self.mode = "Circle"
                self.center = self.shape.Edges[0].Curve.Center
                self.ghost.setCenter(self.center)
                self.ghost.setStartAngle(math.radians(self.sel.FirstAngle))
                self.ghost.setEndAngle(math.radians(self.sel.LastAngle))
            elif Draft.getType(self.sel) == "BSpline":
                self.ghost = bsplineTracker(points=self.sel.Points)
                self.mode = "BSpline"
            elif Draft.getType(self.sel) == "BezCurve":
                FreeCAD.Console.PrintWarning(translate("draft", "Sorry, offset of Bezier curves is currently still not supported")+"\n")
                self.finish()
                return
            else:
                if len(self.sel.Shape.Edges) == 1:
                    import Part
                    if isinstance(self.sel.Shape.Edges[0].Curve,Part.Circle):
                        self.ghost = arcTracker()
                        self.mode = "Circle"
                        self.center = self.shape.Edges[0].Curve.Center
                        self.ghost.setCenter(self.center)
                        if len(self.sel.Shape.Vertexes) > 1:
                            self.ghost.setStartAngle(self.sel.Shape.Edges[0].FirstParameter)
                            self.ghost.setEndAngle(self.sel.Shape.Edges[0].LastParameter)
                if not self.ghost:
                    self.ghost = wireTracker(self.shape)
                    self.mode = "Wire"
            self.call = self.view.addEventCallback("SoEvent",self.action)
            FreeCAD.Console.PrintMessage(translate("draft", "Pick distance")+"\n")
            if self.planetrack:
                self.planetrack.set(self.shape.Vertexes[0].Point)
            self.running = True

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event":
            self.point,ctrlPoint,info = getPoint(self,arg)
            if hasMod(arg,MODCONSTRAIN) and self.constrainSeg:
                dist = DraftGeomUtils.findPerpendicular(self.point,self.shape,self.constrainSeg[1])
            else:
                dist = DraftGeomUtils.findPerpendicular(self.point,self.shape.Edges)
            if dist:
                self.ghost.on()
                if self.mode == "Wire":
                    d = dist[0].negative()
                    v1 = DraftGeomUtils.getTangent(self.shape.Edges[0],self.point)
                    v2 = DraftGeomUtils.getTangent(self.shape.Edges[dist[1]],self.point)
                    a = -DraftVecUtils.angle(v1,v2)
                    self.dvec = DraftVecUtils.rotate(d,a,plane.axis)
                    occmode = self.ui.occOffset.isChecked()
                    self.ghost.update(DraftGeomUtils.offsetWire(self.shape,self.dvec,occ=occmode),forceclosed=occmode)
                elif self.mode == "BSpline":
                    d = dist[0].negative()
                    e = self.shape.Edges[0]
                    basetan = DraftGeomUtils.getTangent(e,self.point)
                    self.npts = []
                    for p in self.sel.Points:
                        currtan = DraftGeomUtils.getTangent(e,p)
                        a = -DraftVecUtils.angle(currtan,basetan)
                        self.dvec = DraftVecUtils.rotate(d,a,plane.axis)
                        self.npts.append(p.add(self.dvec))
                    self.ghost.update(self.npts)
                elif self.mode == "Circle":
                    self.dvec = self.point.sub(self.center).Length
                    self.ghost.setRadius(self.dvec)
                self.constrainSeg = dist
                self.linetrack.on()
                self.linetrack.p1(self.point)
                self.linetrack.p2(self.point.add(dist[0]))
                self.ui.setRadiusValue(dist[0].Length,unit="Length")
            else:
                self.dvec = None
                self.ghost.off()
                self.constrainSeg = None
                self.linetrack.off()
                self.ui.radiusValue.setText("off")
            self.ui.radiusValue.setFocus()
            self.ui.radiusValue.selectAll()
            if self.extendedCopy:
                if not hasMod(arg,MODALT): self.finish()
            redraw3DView()

        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                copymode = False
                occmode = self.ui.occOffset.isChecked()
                if hasMod(arg,MODALT) or self.ui.isCopy.isChecked(): copymode = True
                FreeCADGui.addModule("Draft")
                if self.npts:
                    print("offset:npts=",self.npts)
                    self.commit(translate("draft","Offset"),
                                ['Draft.offset(FreeCAD.ActiveDocument.'+self.sel.Name+','+DraftVecUtils.toString(self.npts)+',copy='+str(copymode)+')',
                                 'FreeCAD.ActiveDocument.recompute()'])
                elif self.dvec:
                    if isinstance(self.dvec,float):
                        d = str(self.dvec)
                    else:
                        d = DraftVecUtils.toString(self.dvec)
                    self.commit(translate("draft","Offset"),
                                ['Draft.offset(FreeCAD.ActiveDocument.'+self.sel.Name+','+d+',copy='+str(copymode)+',occ='+str(occmode)+')',
                                 'FreeCAD.ActiveDocument.recompute()'])
                if hasMod(arg,MODALT):
                    self.extendedCopy = True
                else:
                    self.finish()

    def finish(self,closed=False):
        if self.running:
            if self.linetrack:
                self.linetrack.finalize()
            if self.ghost:
                self.ghost.finalize()
        Modifier.finish(self)

    def numericRadius(self,rad):
        '''this function gets called by the toolbar when
        valid radius have been entered there'''
        #print("dvec:",self.dvec)
        #print("rad:",rad)
        if self.dvec:
            if isinstance(self.dvec,float):
                if self.mode == "Circle":
                    r1 = self.shape.Edges[0].Curve.Radius
                    r2 = self.ghost.getRadius()
                    if r2 >= r1:
                        rad = r1 + rad
                    else:
                        rad = r1 - rad
                    d = str(rad)
                else:
                    print("Draft.Offset error: Unhandled case")
            else:
                self.dvec.normalize()
                self.dvec.multiply(rad)
                d = DraftVecUtils.toString(self.dvec)
            copymode = False
            occmode = self.ui.occOffset.isChecked()
            if self.ui.isCopy.isChecked():
                copymode = True
            FreeCADGui.addModule("Draft")
            self.commit(translate("draft","Offset"),
                        ['Draft.offset(FreeCAD.ActiveDocument.'+self.sel.Name+','+d+',copy='+str(copymode)+',occ='+str(occmode)+')',
                         'FreeCAD.ActiveDocument.recompute()'])
            self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Offset',Offset())

