
def calculatePlacement(globalRotation, edge, offset, RefPt, xlate, align, normal=None):
    """Orient shape to tangent at parm offset along edge."""
    import functools
    # http://en.wikipedia.org/wiki/Euler_angles
    # start with null Placement point so translate goes to right place.
    placement = FreeCAD.Placement()
    # preserve global orientation
    placement.Rotation = globalRotation

    placement.move(RefPt + xlate)

    if not align:
        return placement

    # unit +Z  Probably defined elsewhere?
    z = FreeCAD.Vector(0, 0, 1)
    # y = FreeCAD.Vector(0, 1, 0)               # unit +Y
    x = FreeCAD.Vector(1, 0, 0)                 # unit +X
    nullv = FreeCAD.Vector(0, 0, 0)

    # get local coord system - tangent, normal, binormal, if possible
    t = edge.tangentAt(getParameterFromV0(edge, offset))
    t.normalize()

    try:
        if normal:
            n = normal
        else:
            n = edge.normalAt(getParameterFromV0(edge, offset))
            n.normalize()
        b = (t.cross(n))
        b.normalize()
    # no normal defined here
    except FreeCAD.Base.FreeCADError:
        n = nullv
        b = nullv
        FreeCAD.Console.PrintLog(
            "Draft PathArray.orientShape - Cannot calculate Path normal.\n")

    lnodes = z.cross(b)

    try:
        # Can't normalize null vector.
        lnodes.normalize()
    except:
        # pathological cases:
        pass
    # 1) can't determine normal, don't align.
    if n == nullv:
        psi = 0.0
        theta = 0.0
        phi = 0.0
        FreeCAD.Console.PrintWarning(
            "Draft PathArray.orientShape - Path normal is Null. Cannot align.\n")
    elif abs(b.dot(z)) == 1.0:                                    # 2) binormal is || z
        # align shape to tangent only
        psi = math.degrees(DraftVecUtils.angle(x, t, z))
        theta = 0.0
        phi = 0.0
        FreeCAD.Console.PrintWarning(
            "Draft PathArray.orientShape - Gimbal lock. Infinite lnodes. Change Path or Base.\n")
    else:                                                        # regular case
        psi = math.degrees(DraftVecUtils.angle(x, lnodes, z))
        theta = math.degrees(DraftVecUtils.angle(z, b, lnodes))
        phi = math.degrees(DraftVecUtils.angle(lnodes, t, b))

    rotations = [placement.Rotation]

    if psi != 0.0:
        rotations.insert(0, FreeCAD.Rotation(z, psi))
    if theta != 0.0:
        rotations.insert(0, FreeCAD.Rotation(lnodes, theta))
    if phi != 0.0:
        rotations.insert(0, FreeCAD.Rotation(b, phi))

    if len(rotations) == 1:
        finalRotation = rotations[0]
    else:
        finalRotation = functools.reduce(
            lambda rot1, rot2: rot1.multiply(rot2), rotations)

    placement.Rotation = finalRotation

    return placement


def calculatePlacementsOnPath(shapeRotation, pathwire, count, xlate, align):
    """Calculates the placements of a shape along a given path so that each copy will be distributed evenly"""
    import Part
    import DraftGeomUtils

    closedpath = DraftGeomUtils.isReallyClosed(pathwire)
    normal = DraftGeomUtils.getNormal(pathwire)
    path = Part.__sortEdges__(pathwire.Edges)
    ends = []
    cdist = 0

    for e in path:                                                 # find cumulative edge end distance
        cdist += e.Length
        ends.append(cdist)

    placements = []

    # place the start shape
    pt = path[0].Vertexes[0].Point
    placements.append(calculatePlacement(
        shapeRotation, path[0], 0, pt, xlate, align, normal))

    # closed path doesn't need shape on last vertex
    if not(closedpath):
        # place the end shape
        pt = path[-1].Vertexes[-1].Point
        placements.append(calculatePlacement(
            shapeRotation, path[-1], path[-1].Length, pt, xlate, align, normal))

    if count < 3:
        return placements

    # place the middle shapes
    if closedpath:
        stop = count
    else:
        stop = count - 1
    step = float(cdist) / stop
    remains = 0
    travel = step
    for i in range(1, stop):
        # which edge in path should contain this shape?
        # avoids problems with float math travel > ends[-1]
        iend = len(ends) - 1

        for j in range(0, len(ends)):
            if travel <= ends[j]:
                iend = j
                break

        # place shape at proper spot on proper edge
        remains = ends[iend] - travel
        offset = path[iend].Length - remains
        pt = path[iend].valueAt(getParameterFromV0(path[iend], offset))

        placements.append(calculatePlacement(
            shapeRotation, path[iend], offset, pt, xlate, align, normal))

        travel += step

    return placements


def makePathArray(baseobject,pathobject,count,xlate=None,align=False,pathobjsubs=[],useLink=False):
    """makePathArray(docobj,path,count,xlate,align,pathobjsubs,useLink): distribute
    count copies of a document baseobject along a pathobject or subobjects of a
    pathobject. Optionally translates each copy by FreeCAD.Vector xlate direction
    and distance to adjust for difference in shape centre vs shape reference point.
    Optionally aligns baseobject to tangent/normal/binormal of path."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if useLink:
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","PathArray",_PathArray(None),None,True)
    else:
        obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","PathArray")
        _PathArray(obj)
    obj.Base = baseobject
    obj.PathObj = pathobject
    if pathobjsubs:
        sl = []
        for sub in pathobjsubs:
            sl.append((obj.PathObj,sub))
        obj.PathSubs = list(sl)
    if count > 1:
        obj.Count = count
    if xlate:
        obj.Xlate = xlate
    obj.Align = align
    if gui:
        if useLink:
            _ViewProviderDraftLink(obj.ViewObject)
        else:
            _ViewProviderDraftArray(obj.ViewObject)
            formatObject(obj,obj.Base)
            if len(obj.Base.ViewObject.DiffuseColor) > 1:
                obj.ViewObject.Proxy.resetColors(obj.ViewObject)
        baseobject.ViewObject.hide()
        select(obj)
    return obj


class _PathArray(_DraftLink):
    """The Draft Path Array object"""

    def __init__(self,obj):
        _DraftLink.__init__(self,obj,"PathArray")

    def attach(self,obj):
        obj.addProperty("App::PropertyLinkGlobal","Base","Draft",QT_TRANSLATE_NOOP("App::Property","The base object that must be duplicated"))
        obj.addProperty("App::PropertyLinkGlobal","PathObj","Draft",QT_TRANSLATE_NOOP("App::Property","The path object along which to distribute objects"))
        obj.addProperty("App::PropertyLinkSubListGlobal","PathSubs",QT_TRANSLATE_NOOP("App::Property","Selected subobjects (edges) of PathObj"))
        obj.addProperty("App::PropertyInteger","Count","Draft",QT_TRANSLATE_NOOP("App::Property","Number of copies"))
        obj.addProperty("App::PropertyVectorDistance","Xlate","Draft",QT_TRANSLATE_NOOP("App::Property","Optional translation vector"))
        obj.addProperty("App::PropertyBool","Align","Draft",QT_TRANSLATE_NOOP("App::Property","Orientation of Base along path"))
        obj.Count = 2
        obj.PathSubs = []
        obj.Xlate = FreeCAD.Vector(0,0,0)
        obj.Align = False

        if self.useLink:
            obj.addProperty("App::PropertyBool","ExpandArray","Draft",
                    QT_TRANSLATE_NOOP("App::Property","Show array element as children object"))
            obj.ExpandArray = False

        _DraftLink.attach(self,obj)

    def linkSetup(self,obj):
        _DraftLink.linkSetup(self,obj)
        obj.configLinkProperty(ElementCount='Count')

    def execute(self,obj):
        import FreeCAD
        import Part
        import DraftGeomUtils
        if obj.Base and obj.PathObj:
            pl = obj.Placement
            if obj.PathSubs:
                w = self.getWireFromSubs(obj)
            elif (hasattr(obj.PathObj.Shape,'Wires') and obj.PathObj.Shape.Wires):
                w = obj.PathObj.Shape.Wires[0]
            elif obj.PathObj.Shape.Edges:
                w = Part.Wire(obj.PathObj.Shape.Edges)
            else:
                FreeCAD.Console.PrintLog ("_PathArray.createGeometry: path " + obj.PathObj.Name + " has no edges\n")
                return
            base = calculatePlacementsOnPath(
                    obj.Base.Shape.Placement.Rotation,w,obj.Count,obj.Xlate,obj.Align)
            return _DraftLink.buildShape(self,obj,pl,base)

    def getWireFromSubs(self,obj):
        '''Make a wire from PathObj subelements'''
        import Part
        sl = []
        for sub in obj.PathSubs:
            edgeNames = sub[1]
            for n in edgeNames:
                e = sub[0].Shape.getElement(n)
                sl.append(e)
        return Part.Wire(sl)

    def pathArray(self,shape,pathwire,count,xlate,align):
        '''Distribute shapes along a path.'''
        import Part

        placements = calculatePlacementsOnPath(
            shape.Placement.Rotation, pathwire, count, xlate, align)

        base = []

        for placement in placements:
            ns = shape.copy()
            ns.Placement = placement

            base.append(ns)

        return (Part.makeCompound(base))


class PathArray(Modifier):
    """The PathArray FreeCAD command definition"""

    def __init__(self,useLink=False):
        Modifier.__init__(self)
        self.useLink = useLink

    def GetResources(self):
        return {'Pixmap'  : 'Draft_PathArray',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_PathArray", "PathArray"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_PathArray", "Creates copies of a selected object along a selected path.")}

    def Activated(self):
        Modifier.Activated(self)
        if not FreeCADGui.Selection.getSelectionEx():
            if self.ui:
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Please select base and path objects")+"\n")
#                print("Please select base and path objects")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
        else:
            self.proceed()

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        sel = FreeCADGui.Selection.getSelectionEx()
        if sel:
            base = sel[0].Object
            path = sel[1].Object
            pathsubs = list(sel[1].SubElementNames)
            defXlate = FreeCAD.Vector(0,0,0)
            defCount = 4
            defAlign = False
            FreeCAD.ActiveDocument.openTransaction("PathArray")
            Draft.makePathArray(base,path,defCount,defXlate,defAlign,pathsubs,useLink=self.useLink)
            FreeCAD.ActiveDocument.commitTransaction()
            FreeCAD.ActiveDocument.recompute()                                  # feature won't appear until recompute.
        self.finish()


class PathLinkArray(PathArray):
    "The PathLinkArray FreeCAD command definition"

    def __init__(self):
        PathArray.__init__(self,True)

    def GetResources(self):
        return {'Pixmap'  : 'Draft_PathLinkArray',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_PathLinkArray", "PathLinkArray"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_PathLinkArray", "Creates links of a selected object along a selected path.")}


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_PathArray',PathArray())
    FreeCADGui.addCommand('Draft_PathLinkArray',PathLinkArray())

