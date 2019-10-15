
def makeShape2DView(baseobj,projectionVector=None,facenumbers=[]):
    """
    makeShape2DView(object,[projectionVector,facenumbers]) - adds a 2D shape to the document, which is a
    2D projection of the given object. A specific projection vector can also be given. You can also
    specify a list of face numbers to be considered in individual faces mode.
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","Shape2DView")
    _Shape2DView(obj)
    if gui:
        _ViewProviderDraftAlt(obj.ViewObject)
    obj.Base = baseobj
    if projectionVector:
        obj.Projection = projectionVector
    if facenumbers:
        obj.FaceNumbers = facenumbers
    select(obj)

    return obj


class _Shape2DView(_DraftObject):
    """The Shape2DView object"""

    def __init__(self,obj):
        obj.addProperty("App::PropertyLink","Base","Draft",QT_TRANSLATE_NOOP("App::Property","The base object this 2D view must represent"))
        obj.addProperty("App::PropertyVector","Projection","Draft",QT_TRANSLATE_NOOP("App::Property","The projection vector of this object"))
        obj.addProperty("App::PropertyEnumeration","ProjectionMode","Draft",QT_TRANSLATE_NOOP("App::Property","The way the viewed object must be projected"))
        obj.addProperty("App::PropertyIntegerList","FaceNumbers","Draft",QT_TRANSLATE_NOOP("App::Property","The indices of the faces to be projected in Individual Faces mode"))
        obj.addProperty("App::PropertyBool","HiddenLines","Draft",QT_TRANSLATE_NOOP("App::Property","Show hidden lines"))
        obj.addProperty("App::PropertyBool","FuseArch","Draft",QT_TRANSLATE_NOOP("App::Property","Fuse wall and structure objects of same type and material"))
        obj.addProperty("App::PropertyBool","Tessellation","Draft",QT_TRANSLATE_NOOP("App::Property","Tessellate Ellipses and B-splines into line segments"))
        obj.addProperty("App::PropertyBool","InPlace","Draft",QT_TRANSLATE_NOOP("App::Property","For Cutlines and Cutfaces modes, this leaves the faces at the cut location"))
        obj.addProperty("App::PropertyFloat","SegmentLength","Draft",QT_TRANSLATE_NOOP("App::Property","Length of line segments if tessellating Ellipses or B-splines into line segments"))
        obj.addProperty("App::PropertyBool","VisibleOnly","Draft",QT_TRANSLATE_NOOP("App::Property","If this is True, this object will be recomputed only if it is visible"))
        obj.Projection = Vector(0,0,1)
        obj.ProjectionMode = ["Solid","Individual Faces","Cutlines","Cutfaces"]
        obj.HiddenLines = False
        obj.Tessellation = False
        obj.VisibleOnly = False
        obj.InPlace = True
        obj.SegmentLength = .05
        _DraftObject.__init__(self,obj,"Shape2DView")

    def getProjected(self,obj,shape,direction):
        "returns projected edges from a shape and a direction"
        import Part,Drawing,DraftGeomUtils
        edges = []
        groups = Drawing.projectEx(shape,direction)
        for g in groups[0:5]:
            if g:
                edges.append(g)
        if hasattr(obj,"HiddenLines"):
            if obj.HiddenLines:
                for g in groups[5:]:
                    edges.append(g)
        #return Part.makeCompound(edges)
        if hasattr(obj,"Tessellation") and obj.Tessellation:
            return DraftGeomUtils.cleanProjection(Part.makeCompound(edges),obj.Tessellation,obj.SegmentLength)
        else:
            return Part.makeCompound(edges)
            #return DraftGeomUtils.cleanProjection(Part.makeCompound(edges))

    def execute(self,obj):
        if hasattr(obj,"VisibleOnly"):
            if obj.VisibleOnly:
                if obj.ViewObject:
                    if obj.ViewObject.Visibility == False:
                        return False
        import DraftGeomUtils
        obj.positionBySupport()
        pl = obj.Placement
        if obj.Base:
            if getType(obj.Base) == "SectionPlane":
                if obj.Base.Objects:
                    onlysolids = True
                    if hasattr(obj.Base,"OnlySolids"):
                        onlysolids = obj.Base.OnlySolids
                    import Arch, Part, Drawing
                    objs = getGroupContents(obj.Base.Objects,walls=True)
                    objs = removeHidden(objs)
                    shapes = []
                    if hasattr(obj,"FuseArch") and obj.FuseArch:
                        shtypes = {}
                        for o in objs:
                            if getType(o) in ["Wall","Structure"]:
                                if onlysolids:
                                    shtypes.setdefault(o.Material.Name if (hasattr(o,"Material") and o.Material) else "None",[]).extend(o.Shape.Solids)
                                else:
                                    shtypes.setdefault(o.Material.Name if (hasattr(o,"Material") and o.Material) else "None",[]).append(o.Shape.copy())
                            elif o.isDerivedFrom("Part::Feature"):
                                if onlysolids:
                                    shapes.extend(o.Shape.Solids)
                                else:
                                    shapes.append(o.Shape.copy())
                        for k,v in shtypes.items():
                            v1 = v.pop()
                            if v:
                                v1 = v1.multiFuse(v)
                                v1 = v1.removeSplitter()
                            if v1.Solids:
                                shapes.extend(v1.Solids)
                            else:
                                print("Shape2DView: Fusing Arch objects produced non-solid results")
                                shapes.append(v1)
                    else:
                        for o in objs:
                            if o.isDerivedFrom("Part::Feature"):
                                if onlysolids:
                                    shapes.extend(o.Shape.Solids)
                                else:
                                    shapes.append(o.Shape.copy())
                    clip = False
                    if hasattr(obj.Base,"Clip"):
                        clip = obj.Base.Clip
                    cutp,cutv,iv = Arch.getCutVolume(obj.Base.Shape,shapes,clip)
                    cuts = []
                    opl = FreeCAD.Placement(obj.Base.Placement)
                    proj = opl.Rotation.multVec(FreeCAD.Vector(0,0,1))
                    if obj.ProjectionMode == "Solid":
                        for sh in shapes:
                            if cutv:
                                if sh.Volume < 0:
                                    sh.reverse()
                                #if cutv.BoundBox.intersect(sh.BoundBox):
                                #    c = sh.cut(cutv)
                                #else:
                                #    c = sh.copy()
                                c = sh.cut(cutv)
                                if onlysolids:
                                    cuts.extend(c.Solids)
                                else:
                                    cuts.append(c)
                            else:
                                if onlysolids:
                                    cuts.extend(sh.Solids)
                                else:
                                    cuts.append(sh.copy())
                        comp = Part.makeCompound(cuts)
                        obj.Shape = self.getProjected(obj,comp,proj)
                    elif obj.ProjectionMode in ["Cutlines","Cutfaces"]:
                        for sh in shapes:
                            if sh.Volume < 0:
                                sh.reverse()
                            c = sh.section(cutp)
                            faces = []
                            if (obj.ProjectionMode == "Cutfaces") and (sh.ShapeType == "Solid"):
                                if hasattr(obj,"InPlace"):
                                    if not obj.InPlace:
                                        c = self.getProjected(obj,c,proj)
                                wires = DraftGeomUtils.findWires(c.Edges)
                                for w in wires:
                                    if w.isClosed():
                                        faces.append(Part.Face(w))
                            if faces:
                                cuts.extend(faces)
                            else:
                                cuts.append(c)
                        comp = Part.makeCompound(cuts)
                        opl = FreeCAD.Placement(obj.Base.Placement)
                        comp.Placement = opl.inverse()
                        if comp:
                            obj.Shape = comp

            elif obj.Base.isDerivedFrom("App::DocumentObjectGroup"):
                shapes = []
                objs = getGroupContents(obj.Base)
                for o in objs:
                    if o.isDerivedFrom("Part::Feature"):
                        if o.Shape:
                            if not o.Shape.isNull():
                                shapes.append(o.Shape)
                if shapes:
                    import Part
                    comp = Part.makeCompound(shapes)
                    obj.Shape = self.getProjected(obj,comp,obj.Projection)

            elif obj.Base.isDerivedFrom("Part::Feature"):
                if not DraftVecUtils.isNull(obj.Projection):
                    if obj.ProjectionMode == "Solid":
                        obj.Shape = self.getProjected(obj,obj.Base.Shape,obj.Projection)
                    elif obj.ProjectionMode == "Individual Faces":
                        import Part
                        if obj.FaceNumbers:
                            faces = []
                            for i in obj.FaceNumbers:
                                if len(obj.Base.Shape.Faces) > i:
                                    faces.append(obj.Base.Shape.Faces[i])
                            views = []
                            for f in faces:
                                views.append(self.getProjected(obj,f,obj.Projection))
                            if views:
                                obj.Shape = Part.makeCompound(views)
                    else:
                        FreeCAD.Console.PrintWarning(obj.ProjectionMode+" mode not implemented\n")
        if not DraftGeomUtils.isNull(pl):
            obj.Placement = pl


class Shape2DView(Modifier):
    """The Shape2DView FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_2DShapeView',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Shape2DView", "Shape 2D view"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Shape2DView", "Creates Shape 2D views of selected objects")}

    def Activated(self):
        Modifier.Activated(self)
        if not FreeCADGui.Selection.getSelection():
            if self.ui:
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Select an object to project")+"\n")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
        else:
            self.proceed()

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        faces = []
        objs = []
        vec = FreeCADGui.ActiveDocument.ActiveView.getViewDirection().negative()
        sel = FreeCADGui.Selection.getSelectionEx()
        for s in sel:
            objs.append(s.Object)
            for e in s.SubElementNames:
                if "Face" in e:
                    faces.append(int(e[4:])-1)
        #print(objs,faces)
        commitlist = []
        FreeCADGui.addModule("Draft")
        if (len(objs) == 1) and faces:
            commitlist.append("Draft.makeShape2DView(FreeCAD.ActiveDocument."+objs[0].Name+",FreeCAD.Vector"+str(tuple(vec))+",facenumbers="+str(faces)+")")
        else:
            for o in objs:
                commitlist.append("Draft.makeShape2DView(FreeCAD.ActiveDocument."+o.Name+",FreeCAD.Vector"+str(tuple(vec))+")")
        if commitlist:
            commitlist.append("FreeCAD.ActiveDocument.recompute()")
            self.commit(translate("draft","Create 2D view"),commitlist)
        self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Shape2DView',Shape2DView())

