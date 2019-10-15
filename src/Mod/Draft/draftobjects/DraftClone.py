
def clone(obj,delta=None,forcedraft=False):
    """clone(obj,[delta,forcedraft]): makes a clone of the given object(s). The clone is an exact,
    linked copy of the given object. If the original object changes, the final object
    changes too. Optionally, you can give a delta Vector to move the clone from the
    original position. If forcedraft is True, the resulting object is a Draft clone
    even if the input object is an Arch object."""

    prefix = getParam("ClonePrefix","")
    cl = None
    if prefix:
        prefix = prefix.strip()+" "
    if not isinstance(obj,list):
        obj = [obj]
    if (len(obj) == 1) and obj[0].isDerivedFrom("Part::Part2DObject"):
        cl = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","Clone2D")
        cl.Label = prefix + obj[0].Label + " (2D)"
    elif (len(obj) == 1) and (hasattr(obj[0],"CloneOf") or (getType(obj[0]) == "BuildingPart")) and (not forcedraft):
        # arch objects can be clones
        import Arch
        if getType(obj[0]) == "BuildingPart":
            cl = Arch.makeComponent()
        else:
            try:
                clonefunc = getattr(Arch,"make"+obj[0].Proxy.Type)
            except:
                pass # not a standard Arch object... Fall back to Draft mode
            else:
                cl = clonefunc()
        if cl:
            base = getCloneBase(obj[0])
            cl.Label = prefix + base.Label
            cl.CloneOf = base
            if hasattr(cl,"Material") and hasattr(obj[0],"Material"):
                cl.Material = obj[0].Material
            if getType(obj[0]) != "BuildingPart":
                cl.Placement = obj[0].Placement
            try:
                cl.Role = base.Role
                cl.Description = base.Description
                cl.Tag = base.Tag
            except:
                pass
            if gui:
                formatObject(cl,base)
                cl.ViewObject.DiffuseColor = base.ViewObject.DiffuseColor
                if getType(obj[0]) in ["Window","BuildingPart"]:
                    from DraftGui import todo
                    todo.delay(Arch.recolorize,cl)
            select(cl)
            return cl
    # fall back to Draft clone mode
    if not cl:
        cl = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Clone")
        cl.addExtension("Part::AttachExtensionPython", None)
        cl.Label = prefix + obj[0].Label
    _Clone(cl)
    if gui:
        _ViewProviderClone(cl.ViewObject)
    cl.Objects = obj
    if delta:
        cl.Placement.move(delta)
    elif (len(obj) == 1) and hasattr(obj[0],"Placement"):
        cl.Placement = obj[0].Placement
    formatObject(cl,obj[0])
    if hasattr(cl,"LongName") and hasattr(obj[0],"LongName"):
        cl.LongName = obj[0].LongName
    if gui and (len(obj) > 1):
        cl.ViewObject.Proxy.resetColors(cl.ViewObject)
    select(cl)
    return cl


class _Clone(_DraftObject):
    """The Clone object"""

    def __init__(self,obj):
        _DraftObject.__init__(self,obj,"Clone")
        obj.addProperty("App::PropertyLinkListGlobal","Objects","Draft",QT_TRANSLATE_NOOP("App::Property","The objects included in this clone"))
        obj.addProperty("App::PropertyVector","Scale","Draft",QT_TRANSLATE_NOOP("App::Property","The scale factor of this clone"))
        obj.addProperty("App::PropertyBool","Fuse","Draft",QT_TRANSLATE_NOOP("App::Property","If this clones several objects, this specifies if the result is a fusion or a compound"))
        obj.Scale = Vector(1,1,1)

    def join(self,obj,shapes):
        if len(shapes) < 2:
            return shapes[0]
        import Part
        if hasattr(obj,"Fuse"):
            if obj.Fuse:
                try:
                    sh = shapes[0].multiFuse(shapes[1:])
                    sh = sh.removeSplitter()
                except:
                    pass
                else:
                    return sh
        return Part.makeCompound(shapes)

    def execute(self,obj):
        import Part, DraftGeomUtils
        pl = obj.Placement
        shapes = []
        if obj.isDerivedFrom("Part::Part2DObject"):
            # if our clone is 2D, make sure all its linked geometry is 2D too
            for o in obj.Objects:
                if not o.isDerivedFrom("Part::Part2DObject"):
                    FreeCAD.Console.PrintWarning("Warning 2D Clone "+obj.Name+" contains 3D geometry")
                    return
        objs = getGroupContents(obj.Objects)
        for o in objs:
            sh = None
            if o.isDerivedFrom("Part::Feature"):
                if not o.Shape.isNull():
                    sh = o.Shape.copy()
            elif o.hasExtension("App::GeoFeatureGroupExtension"):
                shps = []
                for so in o.Group:
                    if so.isDerivedFrom("Part::Feature"):
                        if not so.Shape.isNull():
                            shps.append(so.Shape)
                if shps:
                    sh = self.join(obj,shps)
            if sh:
                m = FreeCAD.Matrix()
                if hasattr(obj,"Scale") and not sh.isNull():
                    sx,sy,sz = obj.Scale
                    if not DraftVecUtils.equals(obj.Scale,Vector(1,1,1)):
                        op = sh.Placement
                        sh.Placement = FreeCAD.Placement()
                        m.scale(obj.Scale)
                        if sx == sy == sz:
                            sh.transformShape(m)
                        else:
                            sh = sh.transformGeometry(m)
                        sh.Placement = op
                if not sh.isNull():
                    shapes.append(sh)
        if shapes:
            if len(shapes) == 1:
                obj.Shape = shapes[0]
                obj.Placement = shapes[0].Placement
            else:
                obj.Shape = self.join(obj,shapes)
        obj.Placement = pl
        if hasattr(obj,"positionBySupport"):
            obj.positionBySupport()

    def getSubVolume(self,obj,placement=None):
        # this allows clones of arch windows to return a subvolume too
        if obj.Objects:
            if hasattr(obj.Objects[0],"Proxy"):
                if hasattr(obj.Objects[0].Proxy,"getSubVolume"):
                    if not placement:
                        # clones must displace the original subvolume too
                        placement = obj.Placement
                    return obj.Objects[0].Proxy.getSubVolume(obj.Objects[0],placement)
        return None


class _ViewProviderClone:
    """a view provider that displays a Clone icon instead of a Draft icon"""

    def __init__(self,vobj):
        vobj.Proxy = self

    def getIcon(self):
        return ":/icons/Draft_Clone.svg"

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def getDisplayModes(self, vobj):
        modes=[]
        return modes

    def setDisplayMode(self, mode):
        return mode

    def resetColors(self, vobj):
        colors = []
        for o in getGroupContents(vobj.Object.Objects):
            if o.isDerivedFrom("Part::Feature"):
                if len(o.ViewObject.DiffuseColor) > 1:
                    colors.extend(o.ViewObject.DiffuseColor)
                else:
                    c = o.ViewObject.ShapeColor
                    c = (c[0],c[1],c[2],o.ViewObject.Transparency/100.0)
                    for f in o.Shape.Faces:
                        colors.append(c)
            elif o.hasExtension("App::GeoFeatureGroupExtension"):
                for so in vobj.Object.Group:
                    if so.isDerivedFrom("Part::Feature"):
                        if len(so.ViewObject.DiffuseColor) > 1:
                            colors.extend(so.ViewObject.DiffuseColor)
                        else:
                            c = so.ViewObject.ShapeColor
                            c = (c[0],c[1],c[2],so.ViewObject.Transparency/100.0)
                            for f in so.Shape.Faces:
                                colors.append(c)
        if colors:
            vobj.DiffuseColor = colors


class Draft_Clone(Modifier):
    """The Draft Clone command definition"""

    def __init__(self):
        Modifier.__init__(self)
        self.moveAfterCloning = False

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Clone',
                'Accel' : "C,L",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Clone", "Clone"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Clone", "Clones the selected object(s)")}

    def Activated(self):
        Modifier.Activated(self)
        if not FreeCADGui.Selection.getSelection():
            if self.ui:
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Select an object to clone")+"\n")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
        else:
            self.proceed()

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        if FreeCADGui.Selection.getSelection():
            l = len(FreeCADGui.Selection.getSelection())
            FreeCADGui.addModule("Draft")
            FreeCAD.ActiveDocument.openTransaction("Clone")
            nonRepeatList = []
            for obj in FreeCADGui.Selection.getSelection():
                if obj not in nonRepeatList:
                    FreeCADGui.doCommand("Draft.clone(FreeCAD.ActiveDocument.getObject(\""+obj.Name+"\"))")
                    nonRepeatList.append(obj)
            FreeCAD.ActiveDocument.commitTransaction()
            FreeCAD.ActiveDocument.recompute()
            FreeCADGui.Selection.clearSelection()
            for i in range(l):
                FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Objects[-(1+i)])
        self.finish()

    def finish(self,close=False):
        Modifier.finish(self,close=False)
        if self.moveAfterCloning:
            todo.delay(FreeCADGui.runCommand,"Draft_Move")


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Clone',Draft_Clone())

