
def rotateVertex(object, vertex_index, angle, center, axis):
    points = object.Points
    points[vertex_index] = object.Placement.inverse().multVec(
        rotateVectorFromCenter(
            object.Placement.multVec(points[vertex_index]),
            angle, axis, center))
    object.Points = points

def rotateVectorFromCenter(vector, angle, axis, center):
    rv = vector.sub(center)
    rv = DraftVecUtils.rotate(rv, math.radians(angle), axis)
    return center.add(rv)

def rotateEdge(object, edge_index, angle, center, axis):
    rotateVertex(object, edge_index, angle, center, axis)
    if isClosedEdge(edge_index, object):
        rotateVertex(object, 0, angle, center, axis)
    else:
        rotateVertex(object, edge_index+1, angle, center, axis)

def copyRotatedEdges(arguments):
    copied_edges = []
    for argument in arguments:
        copied_edges.append(copyRotatedEdge(argument[0], argument[1],
            argument[2], argument[3], argument[4]))
    joinWires(copied_edges)

def copyRotatedEdge(object, edge_index, angle, center, axis):
    vertex1 = rotateVectorFromCenter(
        object.Placement.multVec(object.Points[edge_index]),
        angle, axis, center)
    if isClosedEdge(edge_index, object):
        vertex2 = rotateVectorFromCenter(
            object.Placement.multVec(object.Points[0]),
            angle, axis, center)
    else:
        vertex2 = rotateVectorFromCenter(
            object.Placement.multVec(object.Points[edge_index+1]),
            angle, axis, center)
    return makeLine(vertex1, vertex2)


def rotate(objectslist,angle,center=Vector(0,0,0),axis=Vector(0,0,1),copy=False):
    """rotate(objects,angle,[center,axis,copy]): Rotates the objects contained
    in objects (that can be a list of objects or an object) of the given angle
    (in degrees) around the center, using axis as a rotation axis. If axis is
    omitted, the rotation will be around the vertical Z axis.
    If copy is True, the actual objects are not moved, but copies
    are created instead. The objects (or their copies) are returned."""
    import Part
    typecheck([(copy,bool)], "rotate")
    if not isinstance(objectslist,list): objectslist = [objectslist]
    objectslist.extend(getMovableChildren(objectslist))
    newobjlist = []
    newgroups = {}
    objectslist = filterObjectsForModifiers(objectslist, copy)
    for obj in objectslist:
        if copy:
            newobj = makeCopy(obj)
        else:
            newobj = obj
        if (obj.isDerivedFrom("Part::Feature")):
            shape = obj.Shape.copy()
            shape.rotate(DraftVecUtils.tup(center), DraftVecUtils.tup(axis), angle)
            newobj.Shape = shape
        elif (obj.isDerivedFrom("App::Annotation")):
            if axis.normalize() == Vector(1,0,0):
                newobj.ViewObject.RotationAxis = "X"
                newobj.ViewObject.Rotation = angle
            elif axis.normalize() == Vector(0,1,0):
                newobj.ViewObject.RotationAxis = "Y"
                newobj.ViewObject.Rotation = angle
            elif axis.normalize() == Vector(0,-1,0):
                newobj.ViewObject.RotationAxis = "Y"
                newobj.ViewObject.Rotation = -angle
            elif axis.normalize() == Vector(0,0,1):
                newobj.ViewObject.RotationAxis = "Z"
                newobj.ViewObject.Rotation = angle
            elif axis.normalize() == Vector(0,0,-1):
                newobj.ViewObject.RotationAxis = "Z"
                newobj.ViewObject.Rotation = -angle
        elif getType(obj) == "Point":
            v = Vector(obj.X,obj.Y,obj.Z)
            rv = v.sub(center)
            rv = DraftVecUtils.rotate(rv,math.radians(angle),axis)
            v = center.add(rv)
            newobj.X = v.x
            newobj.Y = v.y
            newobj.Z = v.z
        elif hasattr(obj,"Placement"):
            shape = Part.Shape()
            shape.Placement = obj.Placement
            shape.rotate(DraftVecUtils.tup(center), DraftVecUtils.tup(axis), angle)
            newobj.Placement = shape.Placement
        if copy:
            formatObject(newobj,obj)
        newobjlist.append(newobj)
        if copy:
            for p in obj.InList:
                if p.isDerivedFrom("App::DocumentObjectGroup") and (p in objectslist):
                    g = newgroups.setdefault(p.Name,FreeCAD.ActiveDocument.addObject(p.TypeId,p.Name))
                    g.addObject(newobj)
                    break
    if copy and getParam("selectBaseObjects",False):
        select(objectslist)
    else:
        select(newobjlist)
    if len(newobjlist) == 1: return newobjlist[0]
    return newobjlist


class Rotate(Modifier):
    """The Draft_Rotate FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Rotate',
                'Accel' : "R, O",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Rotate", "Rotate"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Rotate", "Rotates the selected objects. CTRL to snap, SHIFT to constrain, ALT creates a copy")}

    def Activated(self):
        Modifier.Activated(self,"Rotate")
        if not self.ui:
            return
        self.ghosts = []
        self.arctrack = None
        self.get_object_selection()

    def get_object_selection(self):
        if FreeCADGui.Selection.getSelection():
            return self.proceed()
        self.ui.selectUi()
        FreeCAD.Console.PrintMessage(translate("draft", "Select an object to rotate")+"\n")
        self.call = self.view.addEventCallback("SoEvent", selectObject)

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent", self.call)
        self.selected_objects = FreeCADGui.Selection.getSelection()
        self.selected_objects = Draft.getGroupContents(self.selected_objects, addgroups=True, spaces=True, noarchchild=True)
        self.selected_subelements = FreeCADGui.Selection.getSelectionEx()
        self.step = 0
        self.center = None
        self.ui.arcUi()
        self.ui.modUi()
        self.ui.setTitle(translate("draft","Rotate"))
        self.arctrack = arcTracker()
        self.call = self.view.addEventCallback("SoEvent",self.action)
        FreeCAD.Console.PrintMessage(translate("draft", "Pick rotation center")+"\n")

    def action(self, arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent" and arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event":
            self.handle_mouse_move_event(arg)
        elif arg["Type"] == "SoMouseButtonEvent" \
            and arg["State"] == "DOWN" \
            and arg["Button"] == "BUTTON1":
            self.handle_mouse_click_event(arg)

    def handle_mouse_move_event(self, arg):
        for ghost in self.ghosts:
            ghost.off()
        self.point,ctrlPoint,info = getPoint(self,arg)
        # this is to make sure radius is what you see on screen
        if self.center and DraftVecUtils.dist(self.point,self.center):
            viewdelta = DraftVecUtils.project(self.point.sub(self.center), plane.axis)
            if not DraftVecUtils.isNull(viewdelta):
                self.point = self.point.add(viewdelta.negative())
        if self.extendedCopy:
            if not hasMod(arg,MODALT):
                self.step = 3
                self.finish()
        if (self.step == 0):
            pass
        elif (self.step == 1):
            currentrad = DraftVecUtils.dist(self.point,self.center)
            if (currentrad != 0):
                angle = DraftVecUtils.angle(plane.u, self.point.sub(self.center), plane.axis)
            else: angle = 0
            self.ui.setRadiusValue(math.degrees(angle),unit="Angle")
            self.firstangle = angle
            self.ui.radiusValue.setFocus()
            self.ui.radiusValue.selectAll()
        elif (self.step == 2):
            currentrad = DraftVecUtils.dist(self.point,self.center)
            if (currentrad != 0):
                angle = DraftVecUtils.angle(plane.u, self.point.sub(self.center), plane.axis)
            else: angle = 0
            if (angle < self.firstangle):
                sweep = (2*math.pi-self.firstangle)+angle
            else:
                sweep = angle - self.firstangle
            self.arctrack.setApertureAngle(sweep)
            for ghost in self.ghosts:
                ghost.rotate(plane.axis,sweep)
                ghost.on()
            self.ui.setRadiusValue(math.degrees(sweep), 'Angle')
            self.ui.radiusValue.setFocus()
            self.ui.radiusValue.selectAll()
        redraw3DView()

    def handle_mouse_click_event(self, arg):
        if not self.point:
            return
        if self.step == 0:
            self.set_center()
        elif self.step == 1:
            self.set_start_point()
        else:
            self.set_rotation_angle(arg)

    def set_center(self):
        if not self.ghosts:
            self.set_ghosts()
        self.center = self.point
        self.node = [self.point]
        self.ui.radiusUi()
        self.ui.radiusValue.setText(FreeCAD.Units.Quantity(0,FreeCAD.Units.Angle).UserString)
        self.ui.hasFill.hide()
        self.ui.labelRadius.setText(translate("draft","Base angle"))
        self.arctrack.setCenter(self.center)
        for ghost in self.ghosts:
            ghost.center(self.center)
        self.step = 1
        FreeCAD.Console.PrintMessage(translate("draft", "Pick base angle")+"\n")
        if self.planetrack:
            self.planetrack.set(self.point)

    def set_start_point(self):
        self.ui.labelRadius.setText(translate("draft","Rotation"))
        self.rad = DraftVecUtils.dist(self.point,self.center)
        self.arctrack.on()
        self.arctrack.setStartPoint(self.point)
        for ghost in self.ghosts:
            ghost.on()
        self.step = 2
        FreeCAD.Console.PrintMessage(translate("draft", "Pick rotation angle")+"\n")

    def set_rotation_angle(self, arg):
        currentrad = DraftVecUtils.dist(self.point,self.center)
        angle = self.point.sub(self.center).getAngle(plane.u)
        if DraftVecUtils.project(self.point.sub(self.center), plane.v).getAngle(plane.v) > 1:
            angle = -angle
        if (angle < self.firstangle):
            self.angle = (2*math.pi-self.firstangle)+angle
        else:
            self.angle = angle - self.firstangle
        self.rotate(self.ui.isCopy.isChecked() or hasMod(arg,MODALT))
        if hasMod(arg,MODALT):
            self.extendedCopy = True
        else:
            self.finish(cont=True)

    def set_ghosts(self):
        if self.ui.isSubelementMode.isChecked():
            return self.set_subelement_ghosts()
        self.ghosts = [ghostTracker(self.selected_objects)]

    def set_subelement_ghosts(self):
        import Part
        for object in self.selected_subelements:
            for subelement in object.SubObjects:
                if isinstance(subelement, Part.Vertex) \
                    or isinstance(subelement, Part.Edge):
                    self.ghosts.append(ghostTracker(subelement))

    def finish(self, closed=False, cont=False):
        """finishes the arc"""
        if self.arctrack:
            self.arctrack.finalize()
        for ghost in self.ghosts:
            ghost.finalize()
        if cont and self.ui:
            if self.ui.continueMode:
                todo.delayAfter(self.Activated,[])
        Modifier.finish(self)
        if self.doc:
            self.doc.recompute()

    def rotate(self, is_copy=False):
        if self.ui.isSubelementMode.isChecked():
            self.rotate_subelements(is_copy)
        else:
            self.rotate_object(is_copy)

    def rotate_subelements(self, is_copy):
        try:
            if is_copy:
                self.commit(translate("draft", "Copy"), self.build_copy_subelements_command())
            else:
                self.commit(translate("draft", "Rotate"), self.build_rotate_subelements_command())
        except:
            FreeCAD.Console.PrintError(translate("draft", "Some subelements could not be moved."))

    def build_copy_subelements_command(self):
        import Part
        command = []
        arguments = []
        for object in self.selected_subelements:
            for index, subelement in enumerate(object.SubObjects):
                if not isinstance(subelement, Part.Edge):
                    continue
                arguments.append('[FreeCAD.ActiveDocument.{}, {}, {}, {}, {}]'.format(
                    object.ObjectName,
                    int(object.SubElementNames[index][len("Edge"):])-1,
                    math.degrees(self.angle),
                    DraftVecUtils.toString(self.center),
                    DraftVecUtils.toString(plane.axis)))
        command.append('Draft.copyRotatedEdges([{}])'.format(','.join(arguments)))
        command.append('FreeCAD.ActiveDocument.recompute()')
        return command

    def build_rotate_subelements_command(self):
        import Part
        command = []
        for object in self.selected_subelements:
            for index, subelement in enumerate(object.SubObjects):
                if isinstance(subelement, Part.Vertex):
                    command.append('Draft.rotateVertex(FreeCAD.ActiveDocument.{}, {}, {}, {}, {})'.format(
                        object.ObjectName,
                        int(object.SubElementNames[index][len("Vertex"):])-1,
                        math.degrees(self.angle),
                        DraftVecUtils.toString(self.center),
                        DraftVecUtils.toString(plane.axis)))
                elif isinstance(subelement, Part.Edge):
                    command.append('Draft.rotateEdge(FreeCAD.ActiveDocument.{}, {}, {}, {}, {})'.format(
                        object.ObjectName,
                        int(object.SubElementNames[index][len("Edge"):])-1,
                        math.degrees(self.angle),
                        DraftVecUtils.toString(self.center),
                        DraftVecUtils.toString(plane.axis)))
        command.append('FreeCAD.ActiveDocument.recompute()')
        return command

    def rotate_object(self, is_copy):
        objects = '[' + ','.join(['FreeCAD.ActiveDocument.' + object.Name for object in self.selected_objects]) + ']'
        FreeCADGui.addModule("Draft")
        self.commit(translate("draft","Copy" if is_copy else "Rotate"),
            ['Draft.rotate({},{},{},axis={},copy={})'.format(
                objects,
                math.degrees(self.angle),
                DraftVecUtils.toString(self.center),
                DraftVecUtils.toString(plane.axis),
                is_copy
            ),
            'FreeCAD.ActiveDocument.recompute()'])

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        self.center = Vector(numx,numy,numz)
        self.node = [self.center]
        self.arctrack.setCenter(self.center)
        for ghost in self.ghosts:
            ghost.center(self.center)
        self.ui.radiusUi()
        self.ui.hasFill.hide()
        self.ui.labelRadius.setText(translate("draft","Base angle"))
        self.step = 1
        FreeCAD.Console.PrintMessage(translate("draft", "Pick base angle")+"\n")

    def numericRadius(self,rad):
        """this function gets called by the toolbar when valid radius have been entered there"""
        if (self.step == 1):
            self.ui.labelRadius.setText(translate("draft","Rotation"))
            self.firstangle = math.radians(rad)
            self.arctrack.setStartAngle(self.firstangle)
            self.arctrack.on()
            for ghost in self.ghosts:
                ghost.on()
            self.step = 2
            FreeCAD.Console.PrintMessage(translate("draft", "Pick rotation angle")+"\n")
        else:
            self.angle = math.radians(rad)
            self.rotate(self.ui.isCopy.isChecked())
            self.finish(cont=True)


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Rotate',Rotate())

