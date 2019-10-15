
def moveVertex(object, vertex_index, vector):
    points = object.Points
    points[vertex_index] = points[vertex_index].add(vector)
    object.Points = points

def moveEdge(object, edge_index, vector):
    moveVertex(object, edge_index, vector)
    if isClosedEdge(edge_index, object):
        moveVertex(object, 0, vector)
    else:
        moveVertex(object, edge_index+1, vector)

def copyMovedEdges(arguments):
    copied_edges = []
    for argument in arguments:
        copied_edges.append(copyMovedEdge(argument[0], argument[1], argument[2]))
    joinWires(copied_edges)

def copyMovedEdge(object, edge_index, vector):
    vertex1 = object.Placement.multVec(object.Points[edge_index]).add(vector)
    if isClosedEdge(edge_index, object):
        vertex2 = object.Placement.multVec(object.Points[0]).add(vector)
    else:
        vertex2 = object.Placement.multVec(object.Points[edge_index+1]).add(vector)
    return makeLine(vertex1, vertex2)

def move(objectslist,vector,copy=False):
    """move(objects,vector,[copy]): Moves the objects contained
    in objects (that can be an object or a list of objects)
    in the direction and distance indicated by the given
    vector. If copy is True, the actual objects are not moved, but copies
    are created instead. The objects (or their copies) are returned."""
    typecheck([(vector,Vector), (copy,bool)], "move")
    if not isinstance(objectslist,list): objectslist = [objectslist]
    objectslist.extend(getMovableChildren(objectslist))
    newobjlist = []
    newgroups = {}
    objectslist = filterObjectsForModifiers(objectslist, copy)
    for obj in objectslist:
        if getType(obj) == "Point":
            v = Vector(obj.X,obj.Y,obj.Z)
            v = v.add(vector)
            if copy:
                newobj = makeCopy(obj)
            else:
                newobj = obj
            newobj.X = v.x
            newobj.Y = v.y
            newobj.Z = v.z
        elif (obj.isDerivedFrom("Part::Feature")):
            if copy:
                newobj = makeCopy(obj)
            else:
                newobj = obj
            pla = newobj.Placement
            pla.move(vector)
        elif getType(obj) == "Annotation":
            if copy:
                newobj = FreeCAD.ActiveDocument.addObject("App::Annotation",getRealName(obj.Name))
                newobj.LabelText = obj.LabelText
                if gui:
                    formatObject(newobj,obj)
            else:
                newobj = obj
            newobj.Position = obj.Position.add(vector)
        elif getType(obj) == "DraftText":
            if copy:
                newobj = FreeCAD.ActiveDocument.addObject("App::FeaturePython",getRealName(obj.Name))
                DraftText(newobj)
                if gui:
                    ViewProviderDraftText(newobj.ViewObject)
                    formatObject(newobj,obj)
                newobj.Text = obj.Text
                newobj.Placement = obj.Placement
                if gui:
                    formatObject(newobj,obj)
            else:
                newobj = obj
            newobj.Placement.Base = obj.Placement.Base.add(vector)
        elif getType(obj) == "Dimension":
            if copy:
                newobj = FreeCAD.ActiveDocument.addObject("App::FeaturePython",getRealName(obj.Name))
                _Dimension(newobj)
                if gui:
                    _ViewProviderDimension(newobj.ViewObject)
                    formatObject(newobj,obj)
            else:
                newobj = obj
            newobj.Start = obj.Start.add(vector)
            newobj.End = obj.End.add(vector)
            newobj.Dimline = obj.Dimline.add(vector)
        else:
            if copy and obj.isDerivedFrom("Mesh::Feature"):
                print("Mesh copy not supported at the moment") # TODO
            newobj = obj
            if "Placement" in obj.PropertiesList:
                pla = obj.Placement
                pla.move(vector)
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


class Move(Modifier):
    """The Draft_Move FreeCAD command definition"""

    def __init__(self):
        Modifier.__init__(self)

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Move',
                'Accel' : "M, V",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Move", "Move"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Move", "Moves the selected objects between 2 points. CTRL to snap, SHIFT to constrain")}

    def Activated(self):
        self.name = translate("draft","Move", utf8_decode=True)
        Modifier.Activated(self, self.name, is_subtool=isinstance(FreeCAD.activeDraftCommand, EditImproved))
        if not self.ui:
            return
        self.ghosts = []
        self.get_object_selection()

    def get_object_selection(self):
        if FreeCADGui.Selection.getSelectionEx():
            return self.proceed()
        self.ui.selectUi()
        FreeCAD.Console.PrintMessage(translate("draft", "Select an object to move")+"\n")
        self.call = self.view.addEventCallback("SoEvent", selectObject)

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        self.selected_objects = FreeCADGui.Selection.getSelection()
        self.selected_objects = Draft.getGroupContents(self.selected_objects, addgroups=True, spaces=True, noarchchild=True)
        self.selected_subelements = FreeCADGui.Selection.getSelectionEx()
        self.ui.lineUi(self.name)
        self.ui.modUi()
        if self.copymode:
            self.ui.isCopy.setChecked(True)
        self.ui.xValue.setFocus()
        self.ui.xValue.selectAll()
        self.call = self.view.addEventCallback("SoEvent", self.action)
        FreeCAD.Console.PrintMessage(translate("draft", "Pick start point")+"\n")

    def finish(self,closed=False,cont=False):
        for ghost in self.ghosts:
            ghost.finalize()
        if cont and self.ui:
            if self.ui.continueMode:
                todo.delayAfter(self.Activated,[])
        Modifier.finish(self)

    def action(self,arg):
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
        self.point, ctrlPoint, info = getPoint(self,arg)
        if (len(self.node) > 0):
            last = self.node[len(self.node)-1]
            self.vector = self.point.sub(last)
            for ghost in self.ghosts:
                ghost.move(self.vector)
                ghost.on()
        if self.extendedCopy:
            if not hasMod(arg,MODALT): self.finish()
        redraw3DView()

    def handle_mouse_click_event(self, arg):
        if not self.ghosts:
            self.set_ghosts()
        if not self.point:
            return
        self.ui.redraw()
        if self.node == []:
            self.node.append(self.point)
            self.ui.isRelative.show()
            for ghost in self.ghosts:
                ghost.on()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick end point")+"\n")
            if self.planetrack:
                self.planetrack.set(self.point)
        else:
            last = self.node[0]
            self.vector = self.point.sub(last)
            self.move()
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

    def move(self):
        if self.ui.isSubelementMode.isChecked():
            self.move_subelements()
        else:
            self.move_object()

    def move_subelements(self):
        try:
            if self.ui.isCopy.isChecked():
                self.commit(translate("draft", "Copy"), self.build_copy_subelements_command())
            else:
                self.commit(translate("draft", "Move"), self.build_move_subelements_command())
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
                arguments.append('[FreeCAD.ActiveDocument.{}, {}, {}]'.format(
                    object.ObjectName,
                    int(object.SubElementNames[index][len("Edge"):])-1,
                    DraftVecUtils.toString(self.vector)))
        command.append('Draft.copyMovedEdges([{}])'.format(','.join(arguments)))
        command.append('FreeCAD.ActiveDocument.recompute()')
        return command

    def build_move_subelements_command(self):
        import Part
        command = []
        for object in self.selected_subelements:
            for index, subelement in enumerate(object.SubObjects):
                if isinstance(subelement, Part.Vertex):
                    command.append('Draft.moveVertex(FreeCAD.ActiveDocument.{}, {}, {})'.format(
                        object.ObjectName,
                        int(object.SubElementNames[index][len("Vertex"):])-1,
                        DraftVecUtils.toString(self.vector)
                        ))
                elif isinstance(subelement, Part.Edge):
                    command.append('Draft.moveEdge(FreeCAD.ActiveDocument.{}, {}, {})'.format(
                        object.ObjectName,
                        int(object.SubElementNames[index][len("Edge"):])-1,
                        DraftVecUtils.toString(self.vector)
                        ))
        command.append('FreeCAD.ActiveDocument.recompute()')
        return command

    def move_object(self):
        objects = '[' + ','.join(['FreeCAD.ActiveDocument.' + object.Name for object in self.selected_objects]) + ']'
        FreeCADGui.addModule("Draft")
        self.commit(translate("draft","Copy" if self.ui.isCopy.isChecked() else "Move"),
            ['Draft.move('+objects+','+DraftVecUtils.toString(self.vector)+',copy='+str(self.ui.isCopy.isChecked())+')', 'FreeCAD.ActiveDocument.recompute()'])

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        self.point = Vector(numx,numy,numz)
        if not self.node:
            self.node.append(self.point)
            self.ui.isRelative.show()
            self.ui.isCopy.show()
            for ghost in self.ghosts:
                ghost.on()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick end point")+"\n")
        else:
            last = self.node[-1]
            self.vector = self.point.sub(last)
            self.move()
            self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Move',Move())

