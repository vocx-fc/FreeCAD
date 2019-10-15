
def downgrade(objects,delete=False,force=None):
    """downgrade(objects,delete=False,force=None): Downgrades the given object(s) (can be
    an object or a list of objects). If delete is True, old objects are deleted.
    The force attribute can be used to
    force a certain way of downgrading. It can be: explode, shapify, subtr,
    splitFaces, cut2, getWire, splitWires, splitCompounds.
    Returns a dictionary containing two lists, a list of new objects and a list
    of objects to be deleted"""

    import Part, DraftGeomUtils

    if not isinstance(objects,list):
        objects = [objects]

    global deleteList, addList
    deleteList = []
    addList = []

    # actions definitions

    def explode(obj):
        """explodes a Draft block"""
        pl = obj.Placement
        newobj = []
        for o in obj.Components:
            o.ViewObject.Visibility = True
            o.Placement = o.Placement.multiply(pl)
        if newobj:
            deleteList(obj)
            return newobj
        return None

    def cut2(objects):
        """cuts first object from the last one"""
        newobj = cut(objects[0],objects[1])
        if newobj:
            addList.append(newobj)
            return newobj
        return None

    def splitCompounds(objects):
        """split solids contained in compound objects into new objects"""
        result = False
        for o in objects:
            if o.Shape.Solids:
                for s in o.Shape.Solids:
                    newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Solid")
                    newobj.Shape = s
                    addList.append(newobj)
                result = True
                deleteList.append(o)
        return result

    def splitFaces(objects):
        """split faces contained in objects into new objects"""
        result = False
        params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft")
        preserveFaceColor = params.GetBool("preserveFaceColor") # True
        preserveFaceNames = params.GetBool("preserveFaceNames") # True
        for o in objects:
            voDColors = o.ViewObject.DiffuseColor if (preserveFaceColor and hasattr(o,'ViewObject')) else None
            oLabel = o.Label if hasattr(o,'Label') else ""
            if o.Shape.Faces:
                for ind, f in enumerate(o.Shape.Faces):
                    newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Face")
                    newobj.Shape = f
                    if preserveFaceNames:
                        newobj.Label = "{} {}".format(oLabel, newobj.Label)
                    if preserveFaceColor:
                        """ At this point, some single-color objects might have
                        just a single entry in voDColors for all their faces; handle that"""
                        tcolor = voDColors[ind] if ind<len(voDColors) else voDColors[0]
                        newobj.ViewObject.DiffuseColor[0] = tcolor # does is not applied visually on its own; left just in case
                        newobj.ViewObject.ShapeColor = tcolor # this gets applied, works by itself too
                    addList.append(newobj)
                result = True
                deleteList.append(o)
        return result

    def subtr(objects):
        """subtracts objects from the first one"""
        faces = []
        for o in objects:
            if o.Shape.Faces:
                faces.extend(o.Shape.Faces)
                deleteList.append(o)
        u = faces.pop(0)
        for f in faces:
            u = u.cut(f)
        if not u.isNull():
            newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Subtraction")
            newobj.Shape = u
            addList.append(newobj)
            return newobj
        return None

    def getWire(obj):
        """gets the wire from a face object"""
        result = False
        for w in obj.Shape.Faces[0].Wires:
            newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Wire")
            newobj.Shape = w
            addList.append(newobj)
            result = True
        deleteList.append(obj)
        return result

    def splitWires(objects):
        """splits the wires contained in objects into edges"""
        result = False
        for o in objects:
            if o.Shape.Edges:
                for e in o.Shape.Edges:
                    newobj = FreeCAD.ActiveDocument.addObject("Part::Feature","Edge")
                    newobj.Shape = e
                    addList.append(newobj)
                deleteList.append(o)
                result = True
        return result

    # analyzing objects

    faces = []
    edges = []
    onlyedges = True
    parts = []
    solids = []
    result = None

    for o in objects:
        if o.isDerivedFrom("Part::Feature"):
            for s in o.Shape.Solids:
                solids.append(s)
            for f in o.Shape.Faces:
                faces.append(f)
            for e in o.Shape.Edges:
                edges.append(e)
            if o.Shape.ShapeType != "Edge":
                onlyedges = False
            parts.append(o)
    objects = parts

    if force:
        if force in ["explode","shapify","subtr","splitFaces","cut2","getWire","splitWires"]:
            result = eval(force)(objects)
        else:
            FreeCAD.Console.PrintMessage(translate("Upgrade: Unknown force method:")+" "+force)
            result = None

    else:

        # applying transformation automatically

        # we have a block, we explode it
        if (len(objects) == 1) and (getType(objects[0]) == "Block"):
            result = explode(objects[0])
            if result:
                FreeCAD.Console.PrintMessage(translate("draft", "Found 1 block: exploding it")+"\n")

        # we have one multi-solids compound object: extract its solids
        elif (len(objects) == 1) and (getType(objects[0]) == "Part") and (len(solids) > 1):
            result = splitCompounds(objects)
            #print(result)
            if result:
                FreeCAD.Console.PrintMessage(translate("draft", "Found 1 multi-solids compound: exploding it")+"\n")

        # special case, we have one parametric object: we "de-parametrize" it
        elif (len(objects) == 1) and (objects[0].isDerivedFrom("Part::Feature")) and ("Base" in objects[0].PropertiesList):
            result = shapify(objects[0])
            if result:
                FreeCAD.Console.PrintMessage(translate("draft", "Found 1 parametric object: breaking its dependencies")+"\n")
                addList.append(result)
                #deleteList.append(objects[0])

        # we have only 2 objects: cut 2nd from 1st
        elif len(objects) == 2:
            result = cut2(objects)
            if result:
                FreeCAD.Console.PrintMessage(translate("draft", "Found 2 objects: subtracting them")+"\n")

        elif (len(faces) > 1):

            # one object with several faces: split it
            if len(objects) == 1:
                result = splitFaces(objects)
                if result:
                    FreeCAD.Console.PrintMessage(translate("draft", "Found several faces: splitting them")+"\n")

            # several objects: remove all the faces from the first one
            else:
                result = subtr(objects)
                if result:
                    FreeCAD.Console.PrintMessage(translate("draft", "Found several objects: subtracting them from the first one")+"\n")

        # only one face: we extract its wires
        elif (len(faces) > 0):
            result = getWire(objects[0])
            if result:
                FreeCAD.Console.PrintMessage(translate("draft", "Found 1 face: extracting its wires")+"\n")

        # no faces: split wire into single edges
        elif not onlyedges:
            result = splitWires(objects)
            if result:
                FreeCAD.Console.PrintMessage(translate("draft", "Found only wires: extracting their edges")+"\n")

        # no result has been obtained
        if not result:
            FreeCAD.Console.PrintMessage(translate("draft", "No more downgrade possible")+"\n")

    if delete:
        names = []
        for o in deleteList:
            names.append(o.Name)
        deleteList = []
        for n in names:
            FreeCAD.ActiveDocument.removeObject(n)
    select(addList)
    return [addList,deleteList]


class Downgrade(Modifier):
    '''The Draft_Downgrade FreeCAD command definition.'''

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Downgrade',
                'Accel' : "D, N",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Downgrade", "Downgrade"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Downgrade", "Explodes the selected objects into simpler objects, or subtracts faces")}

    def Activated(self):
        Modifier.Activated(self,"Downgrade")
        if self.ui:
            if not FreeCADGui.Selection.getSelection():
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Select an object to upgrade")+"\n")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
            else:
                self.proceed()

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        if FreeCADGui.Selection.getSelection():
            FreeCADGui.addModule("Draft")
            self.commit(translate("draft","Downgrade"),
                        ['Draft.downgrade(FreeCADGui.Selection.getSelection(),delete=True)',
                         'FreeCAD.ActiveDocument.recompute()'])
        self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Downgrade',Downgrade())

