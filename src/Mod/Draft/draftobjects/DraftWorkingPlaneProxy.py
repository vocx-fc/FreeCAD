
def makeWorkingPlaneProxy(placement):
    """creates a Working Plane proxy object in the current document"""
    if FreeCAD.ActiveDocument:
        obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","WPProxy")
        WorkingPlaneProxy(obj)
        if FreeCAD.GuiUp:
            ViewProviderWorkingPlaneProxy(obj.ViewObject)
            obj.ViewObject.Proxy.writeCamera()
            obj.ViewObject.Proxy.writeState()
        obj.Placement = placement
        return obj


class WorkingPlaneProxy:
    """The Draft working plane proxy object"""

    def __init__(self,obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyPlacement","Placement","Base",QT_TRANSLATE_NOOP("App::Property","The placement of this object"))
        obj.addProperty("Part::PropertyPartShape","Shape","Base","")
        self.Type = "WorkingPlaneProxy"

    def execute(self,obj):
        import Part
        l = 1
        if obj.ViewObject:
            if hasattr(obj.ViewObject,"DisplaySize"):
                l = obj.ViewObject.DisplaySize.Value
        p = Part.makePlane(l,l,Vector(l/2,-l/2,0),Vector(0,0,-1))
        # make sure the normal direction is pointing outwards, you never know what OCC will decide...
        if p.normalAt(0,0).getAngle(obj.Placement.Rotation.multVec(FreeCAD.Vector(0,0,1))) > 1:
            p.reverse()
        p.Placement = obj.Placement
        obj.Shape = p

    def onChanged(self,obj,prop):
        pass

    def getNormal(self,obj):
        return obj.Shape.Faces[0].normalAt(0,0)

    def __getstate__(self):
        return self.Type

    def __setstate__(self,state):
        if state:
            self.Type = state


class ViewProviderWorkingPlaneProxy:
    """A View Provider for working plane proxies"""

    def __init__(self,vobj):
        # ViewData: 0,1,2: position; 3,4,5,6: rotation; 7: near dist; 8: far dist, 9:aspect ratio;
        # 10: focal dist; 11: height (ortho) or height angle (persp); 12: ortho (0) or persp (1)
        vobj.addProperty("App::PropertyLength","DisplaySize","Arch",QT_TRANSLATE_NOOP("App::Property","The display length of this section plane"))
        vobj.addProperty("App::PropertyLength","ArrowSize","Arch",QT_TRANSLATE_NOOP("App::Property","The size of the arrows of this section plane"))
        vobj.addProperty("App::PropertyPercent","Transparency","Base","")
        vobj.addProperty("App::PropertyFloat","LineWidth","Base","")
        vobj.addProperty("App::PropertyColor","LineColor","Base","")
        vobj.addProperty("App::PropertyFloatList","ViewData","Base","")
        vobj.addProperty("App::PropertyBool","RestoreView","Base","")
        vobj.addProperty("App::PropertyMap","VisibilityMap","Base","")
        vobj.addProperty("App::PropertyBool","RestoreState","Base","")
        vobj.DisplaySize = 100
        vobj.ArrowSize = 5
        vobj.Transparency = 70
        vobj.LineWidth = 1
        c = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch").GetUnsigned("ColorHelpers",674321151)
        vobj.LineColor = (float((c>>24)&0xFF)/255.0,float((c>>16)&0xFF)/255.0,float((c>>8)&0xFF)/255.0,0.0)
        vobj.Proxy = self

    def getIcon(self):
        import Draft_rc
        return ":/icons/Draft_SelectPlane.svg"

    def claimChildren(self):
        return []

    def doubleClicked(self,vobj):
        FreeCADGui.runCommand("Draft_SelectPlane")
        return True

    def setupContextMenu(self,vobj,menu):
        from PySide import QtCore,QtGui
        action1 = QtGui.QAction(QtGui.QIcon(":/icons/Draft_SelectPlane.svg"),"Write camera position",menu)
        QtCore.QObject.connect(action1,QtCore.SIGNAL("triggered()"),self.writeCamera)
        menu.addAction(action1)
        action2 = QtGui.QAction(QtGui.QIcon(":/icons/Draft_SelectPlane.svg"),"Write objects state",menu)
        QtCore.QObject.connect(action2,QtCore.SIGNAL("triggered()"),self.writeState)
        menu.addAction(action2)

    def writeCamera(self):
        if hasattr(self,"Object"):
            from pivy import coin
            n = FreeCADGui.ActiveDocument.ActiveView.getCameraNode()
            FreeCAD.Console.PrintMessage(QT_TRANSLATE_NOOP("Draft","Writing camera position")+"\n")
            cdata = list(n.position.getValue().getValue())
            cdata.extend(list(n.orientation.getValue().getValue()))
            cdata.append(n.nearDistance.getValue())
            cdata.append(n.farDistance.getValue())
            cdata.append(n.aspectRatio.getValue())
            cdata.append(n.focalDistance.getValue())
            if isinstance(n,coin.SoOrthographicCamera):
                cdata.append(n.height.getValue())
                cdata.append(0.0) # orthograhic camera
            elif isinstance(n,coin.SoPerspectiveCamera):
                cdata.append(n.heightAngle.getValue())
                cdata.append(1.0) # perspective camera
            self.Object.ViewObject.ViewData = cdata

    def writeState(self):
        if hasattr(self,"Object"):
            FreeCAD.Console.PrintMessage(QT_TRANSLATE_NOOP("Draft","Writing objects shown/hidden state")+"\n")
            vis = {}
            for o in FreeCAD.ActiveDocument.Objects:
                if o.ViewObject:
                    vis[o.Name] = str(o.ViewObject.Visibility)
            self.Object.ViewObject.VisibilityMap = vis

    def attach(self,vobj):
        from pivy import coin
        self.clip = None
        self.mat1 = coin.SoMaterial()
        self.mat2 = coin.SoMaterial()
        self.fcoords = coin.SoCoordinate3()
        fs = coin.SoIndexedFaceSet()
        fs.coordIndex.setValues(0,7,[0,1,2,-1,0,2,3])
        self.drawstyle = coin.SoDrawStyle()
        self.drawstyle.style = coin.SoDrawStyle.LINES
        self.lcoords = coin.SoCoordinate3()
        ls = coin.SoType.fromName("SoBrepEdgeSet").createInstance()
        ls.coordIndex.setValues(0,28,[0,1,-1,2,3,4,5,-1,6,7,-1,8,9,10,11,-1,12,13,-1,14,15,16,17,-1,18,19,20,21])
        sep = coin.SoSeparator()
        psep = coin.SoSeparator()
        fsep = coin.SoSeparator()
        fsep.addChild(self.mat2)
        fsep.addChild(self.fcoords)
        fsep.addChild(fs)
        psep.addChild(self.mat1)
        psep.addChild(self.drawstyle)
        psep.addChild(self.lcoords)
        psep.addChild(ls)
        sep.addChild(fsep)
        sep.addChild(psep)
        vobj.addDisplayMode(sep,"Default")
        self.onChanged(vobj,"DisplaySize")
        self.onChanged(vobj,"LineColor")
        self.onChanged(vobj,"Transparency")
        self.Object = vobj.Object

    def getDisplayModes(self,vobj):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self,mode):
        return mode

    def updateData(self,obj,prop):
        if prop in ["Placement"]:
            self.onChanged(obj.ViewObject,"DisplaySize")
        return

    def onChanged(self,vobj,prop):
        if prop == "LineColor":
            l = vobj.LineColor
            self.mat1.diffuseColor.setValue([l[0],l[1],l[2]])
            self.mat2.diffuseColor.setValue([l[0],l[1],l[2]])
        elif prop == "Transparency":
            if hasattr(vobj,"Transparency"):
                self.mat2.transparency.setValue(vobj.Transparency/100.0)
        elif prop in ["DisplaySize","ArrowSize"]:
            if hasattr(vobj,"DisplaySize"):
                l = vobj.DisplaySize.Value/2
            else:
                l = 1
            verts = []
            fverts = []
            l1 = 0.1
            if hasattr(vobj,"ArrowSize"):
                l1 = vobj.ArrowSize.Value if vobj.ArrowSize.Value > 0 else 0.1
            l2 = l1/3
            pl = FreeCAD.Placement(vobj.Object.Placement)
            fverts.append(pl.multVec(Vector(-l,-l,0)))
            fverts.append(pl.multVec(Vector(l,-l,0)))
            fverts.append(pl.multVec(Vector(l,l,0)))
            fverts.append(pl.multVec(Vector(-l,l,0)))

            verts.append(pl.multVec(Vector(0,0,0)))
            verts.append(pl.multVec(Vector(l-l1,0,0)))
            verts.append(pl.multVec(Vector(l-l1,l2,0)))
            verts.append(pl.multVec(Vector(l,0,0)))
            verts.append(pl.multVec(Vector(l-l1,-l2,0)))
            verts.append(pl.multVec(Vector(l-l1,l2,0)))

            verts.append(pl.multVec(Vector(0,0,0)))
            verts.append(pl.multVec(Vector(0,l-l1,0)))
            verts.append(pl.multVec(Vector(-l2,l-l1,0)))
            verts.append(pl.multVec(Vector(0,l,0)))
            verts.append(pl.multVec(Vector(l2,l-l1,0)))
            verts.append(pl.multVec(Vector(-l2,l-l1,0)))

            verts.append(pl.multVec(Vector(0,0,0)))
            verts.append(pl.multVec(Vector(0,0,l-l1)))
            verts.append(pl.multVec(Vector(-l2,0,l-l1)))
            verts.append(pl.multVec(Vector(0,0,l)))
            verts.append(pl.multVec(Vector(l2,0,l-l1)))
            verts.append(pl.multVec(Vector(-l2,0,l-l1)))
            verts.append(pl.multVec(Vector(0,-l2,l-l1)))
            verts.append(pl.multVec(Vector(0,0,l)))
            verts.append(pl.multVec(Vector(0,l2,l-l1)))
            verts.append(pl.multVec(Vector(0,-l2,l-l1)))

            self.lcoords.point.setValues(verts)
            self.fcoords.point.setValues(fverts)
        elif prop == "LineWidth":
            self.drawstyle.lineWidth = vobj.LineWidth
        return

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None



class SetWorkingPlaneProxy():
    """The SetWorkingPlaneProxy FreeCAD command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_SelectPlane',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_SetWorkingPlaneProxy", "Create Working Plane Proxy"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_SetWorkingPlaneProxy", "Creates a proxy object from the current working plane")}

    def IsActive(self):
        if FreeCADGui.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):
        if hasattr(FreeCAD,"DraftWorkingPlane"):
            FreeCAD.ActiveDocument.openTransaction("Create WP proxy")
            FreeCADGui.addModule("Draft")
            FreeCADGui.doCommand("Draft.makeWorkingPlaneProxy(FreeCAD.DraftWorkingPlane.getPlacement())")
            FreeCAD.ActiveDocument.recompute()
            FreeCAD.ActiveDocument.commitTransaction()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_SetWorkingPlaneProxy',SetWorkingPlaneProxy())

