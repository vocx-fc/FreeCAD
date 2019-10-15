
class Trimex(Modifier):
    """The Draft_Trimex FreeCAD command definition.
    This tool trims or extends lines, wires and arcs,
    or extrudes single faces. SHIFT constrains to the last point
    or extrudes in direction to the face normal."""

    def GetResources(self):
        return {'Pixmap' : 'Draft_Trimex',
                'Accel' : "T, R",
                'MenuText' : QtCore.QT_TRANSLATE_NOOP("Draft_Trimex", "Trimex"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Trimex", "Trims or extends the selected object, or extrudes single faces. CTRL snaps, SHIFT constrains to current segment or to normal, ALT inverts")}

    def Activated(self):
        Modifier.Activated(self,"Trimex")
        self.edges = []
        self.placement = None
        self.ghost = []
        self.linetrack = None
        self.color = None
        self.width = None
        if self.ui:
            if not FreeCADGui.Selection.getSelection():
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Select object(s) to trim/extend")+"\n")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
            else:
                self.proceed()

    def proceed(self):
        if self.call: self.view.removeEventCallback("SoEvent",self.call)
        sel = FreeCADGui.Selection.getSelection()
        if len(sel) == 2:
            self.trimObjects(sel)
            self.finish()
            return
        self.obj = sel[0]
        self.ui.trimUi()
        self.linetrack = lineTracker()

        import DraftGeomUtils

        if not "Shape" in self.obj.PropertiesList: return
        if "Placement" in self.obj.PropertiesList:
            self.placement = self.obj.Placement
        if len(self.obj.Shape.Faces) == 1:
            # simple extrude mode, the object itself is extruded
            self.extrudeMode = True
            self.ghost = [ghostTracker([self.obj])]
            self.normal = self.obj.Shape.Faces[0].normalAt(.5,.5)
            for v in self.obj.Shape.Vertexes:
                self.ghost.append(lineTracker())
        elif len(self.obj.Shape.Faces) > 1:
            # face extrude mode, a new object is created
            ss =  FreeCADGui.Selection.getSelectionEx()[0]
            if len(ss.SubObjects) == 1:
                if ss.SubObjects[0].ShapeType == "Face":
                    self.obj = self.doc.addObject("Part::Feature","Face")
                    self.obj.Shape = ss.SubObjects[0]
                    self.extrudeMode = True
                    self.ghost = [ghostTracker([self.obj])]
                    self.normal = self.obj.Shape.Faces[0].normalAt(.5,.5)
                    for v in self.obj.Shape.Vertexes:
                        self.ghost.append(lineTracker())
        else:
            # normal wire trimex mode
            self.color = self.obj.ViewObject.LineColor
            self.width = self.obj.ViewObject.LineWidth
            #self.obj.ViewObject.Visibility = False
            self.obj.ViewObject.LineColor = (.5,.5,.5)
            self.obj.ViewObject.LineWidth = 1
            self.extrudeMode = False
            if self.obj.Shape.Wires:
                self.edges = self.obj.Shape.Wires[0].Edges
                self.edges = Part.__sortEdges__(self.edges)
            else:
                self.edges = self.obj.Shape.Edges
            self.ghost = []
            lc = self.color
            sc = (lc[0],lc[1],lc[2])
            sw = self.width
            for e in self.edges:
                if DraftGeomUtils.geomType(e) == "Line":
                    self.ghost.append(lineTracker(scolor=sc,swidth=sw))
                else:
                    self.ghost.append(arcTracker(scolor=sc,swidth=sw))
        if not self.ghost: self.finish()
        for g in self.ghost: g.on()
        self.activePoint = 0
        self.nodes = []
        self.shift = False
        self.alt = False
        self.force = None
        self.cv = None
        self.call = self.view.addEventCallback("SoEvent",self.action)
        FreeCAD.Console.PrintMessage(translate("draft", "Pick distance")+"\n")

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            self.shift = hasMod(arg,MODCONSTRAIN)
            self.alt = hasMod(arg,MODALT)
            self.ctrl = hasMod(arg,MODSNAP)
            if self.extrudeMode:
                arg["ShiftDown"] = False
            elif hasattr(FreeCADGui,"Snapper"):
                FreeCADGui.Snapper.setSelectMode(not self.ctrl)
            wp = not(self.extrudeMode and self.shift)
            self.point,cp,info = getPoint(self,arg,workingplane=wp)
            if hasMod(arg,MODSNAP): self.snapped = None
            else: self.snapped = self.view.getObjectInfo((arg["Position"][0],arg["Position"][1]))
            if self.extrudeMode:
                dist = self.extrude(self.shift)
            else:
                dist = self.redraw(self.point,self.snapped,self.shift,self.alt)
            self.ui.setRadiusValue(dist,unit="Length")
            self.ui.radiusValue.setFocus()
            self.ui.radiusValue.selectAll()
            redraw3DView()

        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                cursor = arg["Position"]
                self.shift = hasMod(arg,MODCONSTRAIN)
                self.alt = hasMod(arg,MODALT)
                if hasMod(arg,MODSNAP): self.snapped = None
                else: self.snapped = self.view.getObjectInfo((cursor[0],cursor[1]))
                self.trimObject()
                self.finish()

    def extrude(self,shift=False,real=False):
        """redraws the ghost in extrude mode"""
        self.newpoint = self.obj.Shape.Faces[0].CenterOfMass
        dvec = self.point.sub(self.newpoint)
        if not shift: delta = DraftVecUtils.project(dvec,self.normal)
        else: delta = dvec
        if self.force and delta.Length:
            ratio = self.force/delta.Length
            delta.multiply(ratio)
        if real: return delta
        self.ghost[0].trans.translation.setValue([delta.x,delta.y,delta.z])
        for i in range(1,len(self.ghost)):
            base = self.obj.Shape.Vertexes[i-1].Point
            self.ghost[i].p1(base)
            self.ghost[i].p2(base.add(delta))
        return delta.Length

    def redraw(self,point,snapped=None,shift=False,alt=False,real=None):
        """redraws the ghost"""

        # initializing
        reverse = False
        for g in self.ghost: g.off()
        if real: newedges = []

        import DraftGeomUtils

        # finding the active point
        vlist = []
        for e in self.edges: vlist.append(e.Vertexes[0].Point)
        vlist.append(self.edges[-1].Vertexes[-1].Point)
        if shift: npoint = self.activePoint
        else: npoint = DraftGeomUtils.findClosest(point,vlist)
        if npoint > len(self.edges)/2: reverse = True
        if alt: reverse = not reverse
        self.activePoint = npoint

        # sorting out directions
        if reverse and (npoint > 0): npoint = npoint-1
        if (npoint > len(self.edges)-1):
            edge = self.edges[-1]
            ghost = self.ghost[-1]
        else:
            edge = self.edges[npoint]
            ghost = self.ghost[npoint]
        if reverse:
            v1 = edge.Vertexes[-1].Point
            v2 = edge.Vertexes[0].Point
        else:
            v1 = edge.Vertexes[0].Point
            v2 = edge.Vertexes[-1].Point

        # snapping
        if snapped:
            snapped = self.doc.getObject(snapped['Object'])
            if hasattr(snapped,"Shape"):
                pts = []
                for e in snapped.Shape.Edges:
                    int = DraftGeomUtils.findIntersection(edge,e,True,True)
                    if int: pts.extend(int)
                if pts:
                    point = pts[DraftGeomUtils.findClosest(point,pts)]

        # modifying active edge
        if DraftGeomUtils.geomType(edge) == "Line":
            ve = DraftGeomUtils.vec(edge)
            chord = v1.sub(point)
            n = ve.cross(chord)
            if n.Length == 0:
                self.newpoint = point
            else:
                perp = ve.cross(n)
                proj = DraftVecUtils.project(chord,perp)
                self.newpoint = Vector.add(point,proj)
            dist = v1.sub(self.newpoint).Length
            ghost.p1(self.newpoint)
            ghost.p2(v2)
            self.ui.labelRadius.setText("Distance")
            if real:
                if self.force:
                    ray = self.newpoint.sub(v1)
                    ray.multiply(self.force/ray.Length)
                    self.newpoint = Vector.add(v1,ray)
                newedges.append(Part.LineSegment(self.newpoint,v2).toShape())
        else:
            center = edge.Curve.Center
            rad = edge.Curve.Radius
            ang1 = DraftVecUtils.angle(v2.sub(center))
            ang2 = DraftVecUtils.angle(point.sub(center))
            self.newpoint=Vector.add(center,DraftVecUtils.rotate(Vector(rad,0,0),-ang2))
            self.ui.labelRadius.setText("Angle")
            dist = math.degrees(-ang2)
            # if ang1 > ang2: ang1,ang2 = ang2,ang1
            #print("last calculated:",math.degrees(-ang1),math.degrees(-ang2))
            ghost.setEndAngle(-ang2)
            ghost.setStartAngle(-ang1)
            ghost.setCenter(center)
            ghost.setRadius(rad)
            if real:
                if self.force:
                    angle = math.radians(self.force)
                    newray = DraftVecUtils.rotate(Vector(rad,0,0),-angle)
                    self.newpoint = Vector.add(center,newray)
                chord = self.newpoint.sub(v2)
                perp = chord.cross(Vector(0,0,1))
                scaledperp = DraftVecUtils.scaleTo(perp,rad)
                midpoint = Vector.add(center,scaledperp)
                newedges.append(Part.Arc(self.newpoint,midpoint,v2).toShape())
        ghost.on()

        # resetting the visible edges
        if not reverse:
            li = list(range(npoint+1,len(self.edges)))
        else:
            li = list(range(npoint-1,-1,-1))
        for i in li:
            edge = self.edges[i]
            ghost = self.ghost[i]
            if DraftGeomUtils.geomType(edge) == "Line":
                ghost.p1(edge.Vertexes[0].Point)
                ghost.p2(edge.Vertexes[-1].Point)
            else:
                ang1 = DraftVecUtils.angle(edge.Vertexes[0].Point.sub(center))
                ang2 = DraftVecUtils.angle(edge.Vertexes[-1].Point.sub(center))
                # if ang1 > ang2: ang1,ang2 = ang2,ang1
                ghost.setEndAngle(-ang2)
                ghost.setStartAngle(-ang1)
                ghost.setCenter(edge.Curve.Center)
                ghost.setRadius(edge.Curve.Radius)
            if real: newedges.append(edge)
            ghost.on()

        # finishing
        if real: return newedges
        else: return dist

    def trimObject(self):
        """trims the actual object"""
        if self.extrudeMode:
            delta = self.extrude(self.shift,real=True)
            #print("delta",delta)
            self.doc.openTransaction("Extrude")
            obj = Draft.extrude(self.obj,delta,solid=True)
            self.doc.commitTransaction()
            self.obj = obj
        else:
            edges = self.redraw(self.point,self.snapped,self.shift,self.alt,real=True)
            newshape = Part.Wire(edges)
            self.doc.openTransaction("Trim/extend")
            if Draft.getType(self.obj) in ["Wire","BSpline"]:
                p = []
                if self.placement:
                    invpl = self.placement.inverse()
                for v in newshape.Vertexes:
                    np = v.Point
                    if self.placement:
                        np = invpl.multVec(np)
                    p.append(np)
                self.obj.Points = p
            elif Draft.getType(self.obj) == "Part::Line":
                p = []
                if self.placement:
                    invpl = self.placement.inverse()
                for v in newshape.Vertexes:
                    np = v.Point
                    if self.placement:
                        np = invpl.multVec(np)
                    p.append(np)
                if ((p[0].x == self.obj.X1) and (p[0].y == self.obj.Y1) and (p[0].z == self.obj.Z1)):
                    self.obj.X2 = p[-1].x
                    self.obj.Y2 = p[-1].y
                    self.obj.Z2 = p[-1].z
                elif ((p[-1].x == self.obj.X1) and (p[-1].y == self.obj.Y1) and (p[-1].z == self.obj.Z1)):
                    self.obj.X2 = p[0].x
                    self.obj.Y2 = p[0].y
                    self.obj.Z2 = p[0].z
                elif ((p[0].x == self.obj.X2) and (p[0].y == self.obj.Y2) and (p[0].z == self.obj.Z2)):
                    self.obj.X1 = p[-1].x
                    self.obj.Y1 = p[-1].y
                    self.obj.Z1 = p[-1].z
                else:
                    self.obj.X1 = p[0].x
                    self.obj.Y1 = p[0].y
                    self.obj.Z1 = p[0].z
            elif Draft.getType(self.obj) == "Circle":
                angles = self.ghost[0].getAngles()
                #print("original",self.obj.FirstAngle," ",self.obj.LastAngle)
                #print("new",angles)
                if angles[0] > angles[1]: angles = (angles[1],angles[0])
                self.obj.FirstAngle = angles[0]
                self.obj.LastAngle = angles[1]
            else:
                self.obj.Shape = newshape
            self.doc.commitTransaction()
        self.doc.recompute()
        for g in self.ghost: g.off()

    def trimObjects(self,objectslist):
        """attempts to trim two objects together"""
        import Part
        wires = []
        for obj in objectslist:
            if not Draft.getType(obj) in ["Wire","Circle"]:
                FreeCAD.Console.PrintError(translate("draft","Unable to trim these objects, only Draft wires and arcs are supported")+"\n")
                return
            if len (obj.Shape.Wires) > 1:
                FreeCAD.Console.PrintError(translate("draft","Unable to trim these objects, too many wires")+"\n")
                return
            if len(obj.Shape.Wires) == 1:
                wires.append(obj.Shape.Wires[0])
            else:
                wires.append(Part.Wire(obj.Shape.Edges))
        ints = []
        edge1 = None
        edge2 = None
        for i1,e1 in enumerate(wires[0].Edges):
            for i2,e2 in enumerate(wires[1].Edges):
                i = DraftGeomUtils.findIntersection(e1,e2,dts=False)
                if len(i) == 1:
                    ints.append(i[0])
                    edge1 = i1
                    edge2 = i2
        if not ints:
            FreeCAD.Console.PrintErro(translate("draft","These objects don't intersect")+"\n")
            return
        if len(ints) != 1:
            FreeCAD.Console.PrintError(translate("draft","Too many intersection points")+"\n")
            return
        v11 = wires[0].Vertexes[0].Point
        v12 = wires[0].Vertexes[-1].Point
        v21 = wires[1].Vertexes[0].Point
        v22 = wires[1].Vertexes[-1].Point
        if DraftVecUtils.closest(ints[0],[v11,v12]) == 1:
            last1 = True
        else:
            last1 = False
        if DraftVecUtils.closest(ints[0],[v21,v22]) == 1:
            last2 = True
        else:
            last2 = False
        for i,obj in enumerate(objectslist):
            if i == 0:
                ed = edge1
                la = last1
            else:
                ed = edge2
                la = last2
            if Draft.getType(obj) == "Wire":
                if la:
                    pts = obj.Points[:ed+1] + ints
                else:
                    pts = ints + obj.Points[ed+1:]
                obj.Points = pts
            else:
                vec = ints[0].sub(obj.Placement.Base)
                vec = obj.Placement.inverse().Rotation.multVec(vec)
                ang = math.degrees(-DraftVecUtils.angle(vec,obj.Placement.Rotation.multVec(FreeCAD.Vector(1,0,0)),obj.Shape.Edges[0].Curve.Axis))
                if la:
                    obj.LastAngle = ang
                else:
                    obj.FirstAngle = ang
        self.doc.recompute()


    def finish(self,closed=False):
        Modifier.finish(self)
        self.force = None
        if self.ui:
            if self.linetrack:
                self.linetrack.finalize()
            if self.ghost:
                for g in self.ghost:
                    g.finalize()
            if self.obj:
                self.obj.ViewObject.Visibility = True
                if self.color:
                    self.obj.ViewObject.LineColor = self.color
                if self.width:
                    self.obj.ViewObject.LineWidth = self.width
            Draft.select(self.obj)

    def numericRadius(self,dist):
        """this function gets called by the toolbar when valid distance have been entered there"""
        self.force = dist
        self.trimObject()
        self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Trimex',Trimex())

