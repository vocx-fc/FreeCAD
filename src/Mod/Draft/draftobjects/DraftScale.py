def copyScaledEdges(arguments):
    copied_edges = []
    for argument in arguments:
        copied_edges.append(copyScaledEdge(argument[0], argument[1],
            argument[2], argument[3]))
    joinWires(copied_edges)

def copyScaledEdge(object, edge_index, scale, center):
    vertex1 = scaleVectorFromCenter(
        object.Placement.multVec(object.Points[edge_index]),
        scale, center)
    if isClosedEdge(edge_index, object):
        vertex2 = scaleVectorFromCenter(
            object.Placement.multVec(object.Points[0]),
            scale, center)
    else:
        vertex2 = scaleVectorFromCenter(
            object.Placement.multVec(object.Points[edge_index+1]),
            scale, center)
    return makeLine(vertex1, vertex2)

def scaleVectorFromCenter(vector, scale, center):
    return vector.sub(center).scale(scale.x, scale.y, scale.z).add(center)

def scaleVertex(object, vertex_index, scale, center):
    points = object.Points
    points[vertex_index] = object.Placement.inverse().multVec(
        scaleVectorFromCenter(
            object.Placement.multVec(points[vertex_index]),
            scale, center))
    object.Points = points

def scaleEdge(object, edge_index, scale, center):
    scaleVertex(object, edge_index, scale, center)
    if isClosedEdge(edge_index, object):
        scaleVertex(object, 0, scale, center)
    else:
        scaleVertex(object, edge_index+1, scale, center)

def scale(objectslist,scale=Vector(1,1,1),center=Vector(0,0,0),copy=False):
    """scale(objects,vector,[center,copy,legacy]): Scales the objects contained
    in objects (that can be a list of objects or an object) of the given scale
    factors defined by the given vector (in X, Y and Z directions) around
    given center. If copy is True, the actual objects are not moved, but copies
    are created instead. The objects (or their copies) are returned."""
    if not isinstance(objectslist, list):
        objectslist = [objectslist]
    newobjlist = []
    for obj in objectslist:
        if copy:
            newobj = makeCopy(obj)
        else:
            newobj = obj
        if obj.isDerivedFrom("Part::Feature"):
            scaled_shape = obj.Shape.copy()
            m = FreeCAD.Matrix()
            m.move(obj.Placement.Base.negative())
            m.move(center.negative())
            m.scale(scale.x,scale.y,scale.z)
            m.move(center)
            m.move(obj.Placement.Base)
            scaled_shape = scaled_shape.transformGeometry(m)
        if getType(obj) == "Rectangle":
            p = []
            for v in scaled_shape.Vertexes: 
                p.append(v.Point)
            pl = obj.Placement.copy()
            pl.Base = p[0]
            diag = p[2].sub(p[0])
            bb = p[1].sub(p[0])
            bh = p[3].sub(p[0])
            nb = DraftVecUtils.project(diag,bb)
            nh = DraftVecUtils.project(diag,bh)
            if obj.Length < 0: l = -nb.Length
            else: l = nb.Length
            if obj.Height < 0: h = -nh.Length
            else: h = nh.Length
            newobj.Length = l
            newobj.Height = h
            tr = p[0].sub(obj.Shape.Vertexes[0].Point)
            newobj.Placement = pl
        elif getType(obj) == "Wire" or getType(obj) == "BSpline":
            for index, point in enumerate(newobj.Points):
                scaleVertex(newobj, index, scale, center)
        elif (obj.isDerivedFrom("Part::Feature")):
            newobj.Shape = scaled_shape
        elif (obj.TypeId == "App::Annotation"):
            factor = scale.y * obj.ViewObject.FontSize
            newobj.ViewObject.FontSize = factor
            d = obj.Position.sub(center)
            newobj.Position = center.add(Vector(d.x*scale.x,d.y*scale.y,d.z*scale.z))
        if copy:
            formatObject(newobj,obj)
        newobjlist.append(newobj)
    if copy and getParam("selectBaseObjects",False):
        select(objectslist)
    else:
        select(newobjlist)
    if len(newobjlist) == 1: return newobjlist[0]
    return newobjlist


class Scale(Modifier):
    '''The Draft_Scale FreeCAD command definition.
    This tool scales the selected objects from a base point.'''

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Scale',
                'Accel' : "S, C",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Scale", "Scale"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Scale", "Scales the selected objects from a base point. CTRL to snap, SHIFT to constrain, ALT to copy")}

    def Activated(self):
        self.name = translate("draft","Scale", utf8_decode=True)
        Modifier.Activated(self,self.name)
        if not self.ui:
            return
        self.ghosts = []
        self.get_object_selection()

    def get_object_selection(self):
        if FreeCADGui.Selection.getSelection():
            return self.proceed()
        self.ui.selectUi()
        FreeCAD.Console.PrintMessage(translate("draft", "Select an object to scale")+"\n")
        self.call = self.view.addEventCallback("SoEvent",selectObject)

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent", self.call)
        self.selected_objects = FreeCADGui.Selection.getSelection()
        self.selected_objects = Draft.getGroupContents(self.selected_objects)
        self.selected_subelements = FreeCADGui.Selection.getSelectionEx()
        self.refs = []
        self.ui.pointUi(self.name)
        self.ui.modUi()
        self.ui.xValue.setFocus()
        self.ui.xValue.selectAll()
        self.pickmode = False
        self.task = None
        self.call = self.view.addEventCallback("SoEvent", self.action)
        FreeCAD.Console.PrintMessage(translate("draft", "Pick base point")+"\n")

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

    def pickRef(self):
        self.pickmode = True
        if self.node:
            self.node = self.node[:1] # remove previous picks
        FreeCAD.Console.PrintMessage(translate("draft", "Pick reference distance from base point")+"\n")
        self.call = self.view.addEventCallback("SoEvent",self.action)

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent" and arg["Key"] == "ESCAPE":
            self.finish()
        elif arg["Type"] == "SoLocation2Event":
            self.handle_mouse_move_event(arg)
        elif arg["Type"] == "SoMouseButtonEvent" \
            and arg["State"] == "DOWN" \
            and (arg["Button"] == "BUTTON1") \
            and self.point:
            self.handle_mouse_click_event()

    def handle_mouse_move_event(self, arg):
        for ghost in self.ghosts:
            ghost.off()
        self.point, ctrlPoint, info = getPoint(self, arg, sym=True)

    def handle_mouse_click_event(self):
        if not self.ghosts:
            self.set_ghosts()
        self.numericInput(self.point.x, self.point.y, self.point.z)

    def scale(self):
        self.delta = Vector(self.task.xValue.value(), self.task.yValue.value(), self.task.zValue.value())
        self.center = self.node[0]
        if self.task.isSubelementMode.isChecked():
            self.scale_subelements()
        elif self.task.isClone.isChecked():
            self.scale_with_clone()
        else:
            self.scale_object()
        self.finish()

    def scale_subelements(self):
        try:
            if self.task.isCopy.isChecked():
                self.commit(translate("draft", "Copy"), self.build_copy_subelements_command())
            else:
                self.commit(translate("draft", "Scale"), self.build_scale_subelements_command())
        except:
            FreeCAD.Console.PrintError(translate("draft", "Some subelements could not be scaled."))

    def scale_with_clone(self):
        if self.task.relative.isChecked():
            self.delta = FreeCAD.DraftWorkingPlane.getGlobalCoords(self.delta)
        objects = '[' + ','.join(['FreeCAD.ActiveDocument.' + object.Name for object in self.selected_objects]) + ']'
        FreeCADGui.addModule("Draft")
        self.commit(translate("draft","Copy") if self.task.isCopy.isChecked() else translate("draft","Scale"),
                    ['clone = Draft.clone('+objects+',forcedraft=True)',
                     'clone.Scale = '+DraftVecUtils.toString(self.delta),
                     'FreeCAD.ActiveDocument.recompute()'])

    def build_copy_subelements_command(self):
        import Part
        command = []
        arguments = []
        for object in self.selected_subelements:
            for index, subelement in enumerate(object.SubObjects):
                if not isinstance(subelement, Part.Edge):
                    continue
                arguments.append('[FreeCAD.ActiveDocument.{}, {}, {}, {}]'.format(
                    object.ObjectName,
                    int(object.SubElementNames[index][len("Edge"):])-1,
                    DraftVecUtils.toString(self.delta),
                    DraftVecUtils.toString(self.center)))
        command.append('Draft.copyScaledEdges([{}])'.format(','.join(arguments)))
        command.append('FreeCAD.ActiveDocument.recompute()')
        return command

    def build_scale_subelements_command(self):
        import Part
        command = []
        for object in self.selected_subelements:
            for index, subelement in enumerate(object.SubObjects):
                if isinstance(subelement, Part.Vertex):
                    command.append('Draft.scaleVertex(FreeCAD.ActiveDocument.{}, {}, {}, {})'.format(
                        object.ObjectName,
                        int(object.SubElementNames[index][len("Vertex"):])-1,
                        DraftVecUtils.toString(self.delta),
                        DraftVecUtils.toString(self.center)))
                elif isinstance(subelement, Part.Edge):
                    command.append('Draft.scaleEdge(FreeCAD.ActiveDocument.{}, {}, {}, {})'.format(
                        object.ObjectName,
                        int(object.SubElementNames[index][len("Edge"):])-1,
                        DraftVecUtils.toString(self.delta),
                        DraftVecUtils.toString(self.center)))
        command.append('FreeCAD.ActiveDocument.recompute()')
        return command

    def scale_object(self):
        if self.task.relative.isChecked():
            self.delta = FreeCAD.DraftWorkingPlane.getGlobalCoords(self.delta)
        objects = '[' + ','.join(['FreeCAD.ActiveDocument.' + object.Name for object in self.selected_objects]) + ']'
        FreeCADGui.addModule("Draft")
        self.commit(translate("draft","Copy" if self.task.isCopy.isChecked() else "Scale"),
                    ['Draft.scale('+objects+',scale='+DraftVecUtils.toString(self.delta)+',center='+DraftVecUtils.toString(self.center)+',copy='+str(self.task.isCopy.isChecked())+')',
                     'FreeCAD.ActiveDocument.recompute()'])

    def scaleGhost(self,x,y,z,rel):
        delta = Vector(x,y,z)
        if rel:
            delta = FreeCAD.DraftWorkingPlane.getGlobalCoords(delta)
        for ghost in self.ghosts:
            ghost.scale(delta)
        # calculate a correction factor depending on the scaling center
        corr = Vector(self.node[0].x,self.node[0].y,self.node[0].z)
        corr.scale(delta.x,delta.y,delta.z)
        corr = (corr.sub(self.node[0])).negative()
        for ghost in self.ghosts:
            ghost.move(corr)
            ghost.on()

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when a valid base point has been entered"""
        self.point = Vector(numx,numy,numz)
        self.node.append(self.point)
        if not self.pickmode:
            if not self.ghosts:
                self.set_ghosts()
            self.ui.offUi()
            if self.call:
                self.view.removeEventCallback("SoEvent",self.call)
            self.task = DraftGui.ScaleTaskPanel()
            self.task.sourceCmd = self
            DraftGui.todo.delay(FreeCADGui.Control.showDialog,self.task)
            DraftGui.todo.delay(self.task.xValue.selectAll,None)
            DraftGui.todo.delay(self.task.xValue.setFocus,None)
            for ghost in self.ghosts:
                ghost.on()
        elif len(self.node) == 2:
            FreeCAD.Console.PrintMessage(translate("draft", "Pick new distance from base point")+"\n")
        elif len(self.node) == 3:
            if hasattr(FreeCADGui,"Snapper"):
                FreeCADGui.Snapper.off()
            if self.call:
                self.view.removeEventCallback("SoEvent",self.call)
            d1 = (self.node[1].sub(self.node[0])).Length
            d2 = (self.node[2].sub(self.node[0])).Length
            #print d2,"/",d1,"=",d2/d1
            if hasattr(self,"task"):
                if self.task:
                    self.task.lock.setChecked(True)
                    self.task.setValue(d2/d1)

    def finish(self,closed=False,cont=False):
        Modifier.finish(self)
        for ghost in self.ghosts:
            ghost.finalize()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Scale',Scale())

