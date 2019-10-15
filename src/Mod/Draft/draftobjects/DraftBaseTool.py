
class DraftTool:
    """The base class of all Draft Tools"""

    def __init__(self):
        self.commitList = []

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self, name="None", noplanesetup=False, is_subtool=False):
        if FreeCAD.activeDraftCommand and not is_subtool:
            FreeCAD.activeDraftCommand.finish()

        global Part, DraftGeomUtils
        import Part, DraftGeomUtils

        self.ui = None
        self.call = None
        self.support = None
        self.point = None
        self.commitList = []
        self.doc = FreeCAD.ActiveDocument
        if not self.doc:
            self.finish()
            return

        FreeCAD.activeDraftCommand = self
        self.view = Draft.get3DView()
        self.ui = FreeCADGui.draftToolBar
        self.featureName = name
        self.ui.sourceCmd = self
        self.ui.setTitle(name)
        self.ui.show()
        if not noplanesetup:
            plane.setup()
        self.node = []
        self.pos = []
        self.constrain = None
        self.obj = None
        self.extendedCopy = False
        self.ui.setTitle(name)
        self.planetrack = None
        if Draft.getParam("showPlaneTracker",False):
            self.planetrack = PlaneTracker()
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.setTrackers()

    def finish(self,close=False):
        self.node = []
        FreeCAD.activeDraftCommand = None
        if self.ui:
            self.ui.offUi()
            self.ui.sourceCmd = None
        if self.planetrack:
            self.planetrack.finalize()
        plane.restore()
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.off()
        if self.call:
            try:
                self.view.removeEventCallback("SoEvent",self.call)
            except RuntimeError:
                # the view has been deleted already
                pass
            self.call = None
        if self.commitList:
            todo.delayCommit(self.commitList)
        self.commitList = []

    def commit(self,name,func):
        """stores actions to be committed to the FreeCAD document"""
        self.commitList.append((name,func))

    def getStrings(self,addrot=None):
        """returns a couple of useful strings for building python commands"""

        # current plane rotation
        p = plane.getRotation()
        qr = p.Rotation.Q
        qr = '('+str(qr[0])+','+str(qr[1])+','+str(qr[2])+','+str(qr[3])+')'

        # support object
        if self.support and FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft").GetBool("useSupport",False):
            sup = 'FreeCAD.ActiveDocument.getObject("' + self.support.Name + '")'
        else:
            sup = 'None'

        # contents of self.node
        points='['
        for n in self.node:
            if len(points) > 1:
                points += ','
            points += DraftVecUtils.toString(n)
        points += ']'

        # fill mode
        if self.ui:
            fil = str(bool(self.ui.fillmode))
        else:
            fil = "True"

        return qr,sup,points,fil


class Creator(DraftTool):
    """A generic Draft Creator Tool used by creation tools such as line or arc"""

    def __init__(self):
        DraftTool.__init__(self)

    def Activated(self,name="None",noplanesetup=False):
        DraftTool.Activated(self,name,noplanesetup)
        if not noplanesetup:
            self.support = getSupport()


class Modifier(DraftTool):
    """A generic Modifier Tool, used by modification tools such as move"""

    def __init__(self):
        DraftTool.__init__(self)
        self.copymode = False


