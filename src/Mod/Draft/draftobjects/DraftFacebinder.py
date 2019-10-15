
def makeFacebinder(selectionset,name="Facebinder"):
    """makeFacebinder(selectionset,[name]): creates a Facebinder object from a selection set.
    Only faces will be added."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if not isinstance(selectionset,list):
        selectionset = [selectionset]
    fb = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",name)
    _Facebinder(fb)
    if gui:
        _ViewProviderFacebinder(fb.ViewObject)
    faces = []
    fb.Proxy.addSubobjects(fb,selectionset)
    select(fb)
    return fb


class _Facebinder(_DraftObject):
    """The Draft Facebinder object"""
    def __init__(self,obj):
        _DraftObject.__init__(self,obj,"Facebinder")
        obj.addProperty("App::PropertyLinkSubList","Faces","Draft",QT_TRANSLATE_NOOP("App::Property","Linked faces"))
        obj.addProperty("App::PropertyBool","RemoveSplitter","Draft",QT_TRANSLATE_NOOP("App::Property","Specifies if splitter lines must be removed"))
        obj.addProperty("App::PropertyDistance","Extrusion","Draft",QT_TRANSLATE_NOOP("App::Property","An optional extrusion value to be applied to all faces"))
        obj.addProperty("App::PropertyBool","Sew","Draft",QT_TRANSLATE_NOOP("App::Property","This specifies if the shapes sew"))


    def execute(self,obj):
        import Part
        pl = obj.Placement
        if not obj.Faces:
            return
        faces = []
        for sel in obj.Faces:
            for f in sel[1]:
                if "Face" in f:
                    try:
                        fnum = int(f[4:])-1
                        faces.append(sel[0].Shape.Faces[fnum])
                    except(IndexError,Part.OCCError):
                        print("Draft: wrong face index")
                        return
        if not faces:
            return
        try:
            if len(faces) > 1:
                sh = None
                if hasattr(obj,"Extrusion"):
                    if obj.Extrusion.Value:
                        for f in faces:
                            f = f.extrude(f.normalAt(0,0).multiply(obj.Extrusion.Value))
                            if sh:
                                sh = sh.fuse(f)
                            else:
                                sh = f
                if not sh:
                    sh = faces.pop()
                    sh = sh.multiFuse(faces)
                if hasattr(obj,"Sew"):
                    if obj.Sew:
                        sh = sh.copy()
                        sh.sewShape()
                if hasattr(obj,"RemoveSplitter"):
                    if obj.RemoveSplitter:
                        sh = sh.removeSplitter()
                else:
                    sh = sh.removeSplitter()
            else:
                sh = faces[0]
                if hasattr(obj,"Extrusion"):
                    if obj.Extrusion.Value:
                        sh = sh.extrude(sh.normalAt(0,0).multiply(obj.Extrusion.Value))
                sh.transformShape(sh.Matrix, True)
        except Part.OCCError:
            print("Draft: error building facebinder")
            return
        obj.Shape = sh
        obj.Placement = pl

    def addSubobjects(self,obj,facelinks):
        """adds facelinks to this facebinder"""
        objs = obj.Faces
        for o in facelinks:
            if isinstance(o,tuple) or isinstance(o,list):
                if o[0].Name != obj.Name:
                    objs.append(tuple(o))
            else:
                for el in o.SubElementNames:
                    if "Face" in el:
                        if o.Object.Name != obj.Name:
                            objs.append((o.Object,el))
        obj.Faces = objs
        self.execute(obj)


class _ViewProviderFacebinder(_ViewProviderDraft):
    def __init__(self,vobj):
        _ViewProviderDraft.__init__(self,vobj)

    def getIcon(self):
        return ":/icons/Draft_Facebinder_Provider.svg"

    def setEdit(self,vobj,mode):
        import DraftGui
        taskd = DraftGui.FacebinderTaskPanel()
        taskd.obj = vobj.Object
        taskd.update()
        FreeCADGui.Control.showDialog(taskd)
        return True

    def unsetEdit(self,vobj,mode):
        FreeCADGui.Control.closeDialog()
        return False


class Draft_Facebinder(Creator):
    """The Draft Facebinder command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Facebinder',
                'Accel' : "F,F",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Facebinder", "Facebinder"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Facebinder", "Creates a facebinder object from selected face(s)")}

    def Activated(self):
        Creator.Activated(self)
        if not FreeCADGui.Selection.getSelection():
            if self.ui:
                self.ui.selectUi()
                FreeCAD.Console.PrintMessage(translate("draft", "Select face(s) on existing object(s)")+"\n")
                self.call = self.view.addEventCallback("SoEvent",selectObject)
        else:
            self.proceed()

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        if FreeCADGui.Selection.getSelection():
            FreeCAD.ActiveDocument.openTransaction("Facebinder")
            FreeCADGui.addModule("Draft")
            FreeCADGui.doCommand("s = FreeCADGui.Selection.getSelectionEx()")
            FreeCADGui.doCommand("f = Draft.makeFacebinder(s)")
            FreeCADGui.doCommand('Draft.autogroup(f)')
            FreeCADGui.doCommand('FreeCAD.ActiveDocument.recompute()')
            FreeCAD.ActiveDocument.commitTransaction()
            FreeCAD.ActiveDocument.recompute()
        self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Facebinder',Draft_Facebinder())

