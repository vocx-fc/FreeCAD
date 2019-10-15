
def makeLabel(targetpoint=None,target=None,direction=None,distance=None,labeltype=None,placement=None):
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","dLabel")
    DraftLabel(obj)
    if FreeCAD.GuiUp:
        ViewProviderDraftLabel(obj.ViewObject)
    if targetpoint:
        obj.TargetPoint = targetpoint
    if target:
        obj.Target = target
    if direction:
        obj.StraightDirection = direction
    if distance:
        obj.StraightDistance = distance
    if labeltype:
        obj.LabelType = labeltype
    if placement:
        obj.Placement = placement

    return obj


class DraftLabel:
    """The Draft Label object"""

    def __init__(self,obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyPlacement","Placement","Base",QT_TRANSLATE_NOOP("App::Property","The placement of this object"))
        obj.addProperty("App::PropertyDistance","StraightDistance","Base",QT_TRANSLATE_NOOP("App::Property","The length of the straight segment"))
        obj.addProperty("App::PropertyVector","TargetPoint","Base",QT_TRANSLATE_NOOP("App::Property","The point indicated by this label"))
        obj.addProperty("App::PropertyVectorList","Points","Base",QT_TRANSLATE_NOOP("App::Property","The points defining the label polyline"))
        obj.addProperty("App::PropertyEnumeration","StraightDirection","Base",QT_TRANSLATE_NOOP("App::Property","The direction of the straight segment"))
        obj.addProperty("App::PropertyEnumeration","LabelType","Base",QT_TRANSLATE_NOOP("App::Property","The type of information shown by this label"))
        obj.addProperty("App::PropertyLinkSub","Target","Base",QT_TRANSLATE_NOOP("App::Property","The target object of this label"))
        obj.addProperty("App::PropertyStringList","CustomText","Base",QT_TRANSLATE_NOOP("App::Property","The text to display when type is set to custom"))
        obj.addProperty("App::PropertyStringList","Text","Base",QT_TRANSLATE_NOOP("App::Property","The text displayed by this label"))
        self.Type = "Label"
        obj.StraightDirection = ["Horizontal","Vertical","Custom"]
        obj.LabelType = ["Custom","Name","Label","Position","Length","Area","Volume","Tag","Material"]
        obj.setEditorMode("Text",1)
        obj.StraightDistance = 1
        obj.TargetPoint = Vector(2,-1,0)
        obj.CustomText = "Label"

    def execute(self,obj):
        if obj.StraightDirection != "Custom":
            p1 = obj.Placement.Base
            if obj.StraightDirection == "Horizontal":
                p2 = Vector(obj.StraightDistance.Value,0,0)
            else:
                p2 = Vector(0,obj.StraightDistance.Value,0)
            p2 = obj.Placement.multVec(p2)
            # p3 = obj.Placement.multVec(obj.TargetPoint)
            p3 = obj.TargetPoint
            obj.Points = [p1,p2,p3]
        if obj.LabelType == "Custom":
            if obj.CustomText:
                obj.Text = obj.CustomText
        elif obj.Target and obj.Target[0]:
            if obj.LabelType == "Name":
                obj.Text = [obj.Target[0].Name]
            elif obj.LabelType == "Label":
                obj.Text = [obj.Target[0].Label]
            elif obj.LabelType == "Tag":
                if hasattr(obj.Target[0],"Tag"):
                    obj.Text = [obj.Target[0].Tag]
            elif obj.LabelType == "Material":
                if hasattr(obj.Target[0],"Material"):
                    if hasattr(obj.Target[0].Material,"Label"):
                        obj.Text = [obj.Target[0].Material.Label]
            elif obj.LabelType == "Position":
                p = obj.Target[0].Placement.Base
                if obj.Target[1]:
                    if "Vertex" in obj.Target[1][0]:
                        p = obj.Target[0].Shape.Vertexes[int(obj.Target[1][0][6:])-1].Point
                obj.Text = [FreeCAD.Units.Quantity(x,FreeCAD.Units.Length).UserString for x in tuple(p)]
            elif obj.LabelType == "Length":
                if obj.Target[0].isDerivedFrom("Part::Feature"):
                    if hasattr(obj.Target[0].Shape,"Length"):
                        obj.Text = [FreeCAD.Units.Quantity(obj.Target[0].Shape.Length,FreeCAD.Units.Length).UserString]
                    if obj.Target[1] and ("Edge" in obj.Target[1][0]):
                        obj.Text = [FreeCAD.Units.Quantity(obj.Target[0].Shape.Edges[int(obj.Target[1][0][4:])-1].Length,FreeCAD.Units.Length).UserString]
            elif obj.LabelType == "Area":
                if obj.Target[0].isDerivedFrom("Part::Feature"):
                    if hasattr(obj.Target[0].Shape,"Area"):
                        obj.Text = [FreeCAD.Units.Quantity(obj.Target[0].Shape.Area,FreeCAD.Units.Area).UserString.replace("^2","²")]
                    if obj.Target[1] and ("Face" in obj.Target[1][0]):
                        obj.Text = [FreeCAD.Units.Quantity(obj.Target[0].Shape.Faces[int(obj.Target[1][0][4:])-1].Area,FreeCAD.Units.Area).UserString]
            elif obj.LabelType == "Volume":
                if obj.Target[0].isDerivedFrom("Part::Feature"):
                    if hasattr(obj.Target[0].Shape,"Volume"):
                        obj.Text = [FreeCAD.Units.Quantity(obj.Target[0].Shape.Volume,FreeCAD.Units.Volume).UserString.replace("^3","³")]

    def onChanged(self,obj,prop):
        pass

    def __getstate__(self):
        return self.Type

    def __setstate__(self,state):
        if state:
            self.Type = state


class ViewProviderDraftLabel:
    """A View Provider for the Draft Label"""

    def __init__(self,vobj):
        vobj.addProperty("App::PropertyLength","TextSize","Base",QT_TRANSLATE_NOOP("App::Property","The size of the text"))
        vobj.addProperty("App::PropertyFont","TextFont","Base",QT_TRANSLATE_NOOP("App::Property","The font of the text"))
        vobj.addProperty("App::PropertyLength","ArrowSize","Base",QT_TRANSLATE_NOOP("App::Property","The size of the arrow"))
        vobj.addProperty("App::PropertyEnumeration","TextAlignment","Base",QT_TRANSLATE_NOOP("App::Property","The vertical alignment of the text"))
        vobj.addProperty("App::PropertyEnumeration","ArrowType","Base",QT_TRANSLATE_NOOP("App::Property","The type of arrow of this label"))
        vobj.addProperty("App::PropertyEnumeration","Frame","Base",QT_TRANSLATE_NOOP("App::Property","The type of frame around the text of this object"))
        vobj.addProperty("App::PropertyBool","Line","Base",QT_TRANSLATE_NOOP("App::Property","Display a leader line or not"))
        vobj.addProperty("App::PropertyFloat","LineWidth","Base",QT_TRANSLATE_NOOP("App::Property","Line width"))
        vobj.addProperty("App::PropertyColor","LineColor","Base",QT_TRANSLATE_NOOP("App::Property","Line color"))
        vobj.addProperty("App::PropertyColor","TextColor","Base",QT_TRANSLATE_NOOP("App::Property","Text color"))
        vobj.addProperty("App::PropertyInteger","MaxChars","Base",QT_TRANSLATE_NOOP("App::Property","The maximum number of characters on each line of the text box"))
        vobj.Proxy = self
        self.Object = vobj.Object
        vobj.TextAlignment = ["Top","Middle","Bottom"]
        vobj.TextAlignment = "Middle"
        vobj.LineWidth = getParam("linewidth",1)
        vobj.TextFont = getParam("textfont")
        vobj.TextSize = getParam("textheight",1)
        vobj.ArrowSize = getParam("arrowsize",1)
        vobj.ArrowType = arrowtypes
        vobj.ArrowType = arrowtypes[getParam("dimsymbol")]
        vobj.Frame = ["None","Rectangle"]
        vobj.Line = True

    def getIcon(self):
        import Draft_rc
        return ":/icons/Draft_Label.svg"

    def claimChildren(self):
        return []

    def attach(self,vobj):
        from pivy import coin
        self.arrow = coin.SoSeparator()
        self.arrowpos = coin.SoTransform()
        self.arrow.addChild(self.arrowpos)
        self.matline = coin.SoMaterial()
        self.drawstyle = coin.SoDrawStyle()
        self.drawstyle.style = coin.SoDrawStyle.LINES
        self.lcoords = coin.SoCoordinate3()
        self.line = coin.SoType.fromName("SoBrepEdgeSet").createInstance()
        self.mattext = coin.SoMaterial()
        textdrawstyle = coin.SoDrawStyle()
        textdrawstyle.style = coin.SoDrawStyle.FILLED
        self.textpos = coin.SoTransform()
        self.font = coin.SoFont()
        self.text2d = coin.SoText2()
        self.text3d = coin.SoAsciiText()
        self.text2d.string = self.text3d.string = "Label" # need to init with something, otherwise, crash!
        self.text2d.justification = coin.SoText2.RIGHT
        self.text3d.justification = coin.SoAsciiText.RIGHT
        self.fcoords = coin.SoCoordinate3()
        self.frame = coin.SoType.fromName("SoBrepEdgeSet").createInstance()
        self.lineswitch = coin.SoSwitch()
        switchnode = coin.SoSeparator()
        switchnode.addChild(self.line)
        switchnode.addChild(self.arrow)
        self.lineswitch.addChild(switchnode)
        self.lineswitch.whichChild = 0
        self.node2d = coin.SoGroup()
        self.node2d.addChild(self.matline)
        self.node2d.addChild(self.arrow)
        self.node2d.addChild(self.drawstyle)
        self.node2d.addChild(self.lcoords)
        self.node2d.addChild(self.lineswitch)
        self.node2d.addChild(self.mattext)
        self.node2d.addChild(textdrawstyle)
        self.node2d.addChild(self.textpos)
        self.node2d.addChild(self.font)
        self.node2d.addChild(self.text2d)
        self.node2d.addChild(self.fcoords)
        self.node2d.addChild(self.frame)
        self.node3d = coin.SoGroup()
        self.node3d.addChild(self.matline)
        self.node3d.addChild(self.arrow)
        self.node3d.addChild(self.drawstyle)
        self.node3d.addChild(self.lcoords)
        self.node3d.addChild(self.lineswitch)
        self.node3d.addChild(self.mattext)
        self.node3d.addChild(textdrawstyle)
        self.node3d.addChild(self.textpos)
        self.node3d.addChild(self.font)
        self.node3d.addChild(self.text3d)
        self.node3d.addChild(self.fcoords)
        self.node3d.addChild(self.frame)
        vobj.addDisplayMode(self.node2d,"2D text")
        vobj.addDisplayMode(self.node3d,"3D text")
        self.onChanged(vobj,"LineColor")
        self.onChanged(vobj,"TextColor")
        self.onChanged(vobj,"ArrowSize")
        self.onChanged(vobj,"Line")

    def getDisplayModes(self,vobj):
        return ["2D text","3D text"]

    def getDefaultDisplayMode(self):
        return "3D text"

    def setDisplayMode(self,mode):
        return mode

    def updateData(self,obj,prop):
        if prop == "Points":
            from pivy import coin
            if len(obj.Points) >= 2:
                self.line.coordIndex.deleteValues(0)
                self.lcoords.point.setValues(obj.Points)
                self.line.coordIndex.setValues(0,len(obj.Points),range(len(obj.Points)))
                self.onChanged(obj.ViewObject,"TextSize")
                self.onChanged(obj.ViewObject,"ArrowType")
            if obj.StraightDistance > 0:
                self.text2d.justification = coin.SoText2.RIGHT
                self.text3d.justification = coin.SoAsciiText.RIGHT
            else:
                self.text2d.justification = coin.SoText2.LEFT
                self.text3d.justification = coin.SoAsciiText.LEFT
        elif prop == "Text":
            if obj.Text:
                if sys.version_info.major >= 3:
                    self.text2d.string.setValues([l for l in obj.Text if l])
                    self.text3d.string.setValues([l for l in obj.Text if l])
                else:
                    self.text2d.string.setValues([l.encode("utf8") for l in obj.Text if l])
                    self.text3d.string.setValues([l.encode("utf8") for l in obj.Text if l])
                self.onChanged(obj.ViewObject,"TextAlignment")

    def getTextSize(self,vobj):
        from pivy import coin
        if vobj.DisplayMode == "3D text":
            text = self.text3d
        else:
            text = self.text2d
        v = FreeCADGui.ActiveDocument.ActiveView.getViewer().getSoRenderManager().getViewportRegion()
        b = coin.SoGetBoundingBoxAction(v)
        text.getBoundingBox(b)
        return b.getBoundingBox().getSize().getValue()

    def onChanged(self,vobj,prop):
        if prop == "LineColor":
            if hasattr(vobj,"LineColor"):
                l = vobj.LineColor
                self.matline.diffuseColor.setValue([l[0],l[1],l[2]])
        elif prop == "TextColor":
            if hasattr(vobj,"TextColor"):
                l = vobj.TextColor
                self.mattext.diffuseColor.setValue([l[0],l[1],l[2]])
        elif prop == "LineWidth":
            if hasattr(vobj,"LineWidth"):
                self.drawstyle.lineWidth = vobj.LineWidth
        elif (prop == "TextFont"):
            if hasattr(vobj,"TextFont"):
                self.font.name = vobj.TextFont.encode("utf8")
        elif prop in ["TextSize","TextAlignment"]:
            if hasattr(vobj,"TextSize") and hasattr(vobj,"TextAlignment"):
                self.font.size = vobj.TextSize.Value
                v = Vector(1,0,0)
                if vobj.Object.StraightDistance > 0:
                    v = v.negative()
                v.multiply(vobj.TextSize/10)
                tsize = self.getTextSize(vobj)
                if len(vobj.Object.Text) > 1:
                    v = v.add(Vector(0,(tsize[1]-1)*2,0))
                if vobj.TextAlignment == "Top":
                    v = v.add(Vector(0,-tsize[1]*2,0))
                elif vobj.TextAlignment == "Middle":
                    v = v.add(Vector(0,-tsize[1],0))
                v = vobj.Object.Placement.Rotation.multVec(v)
                pos = vobj.Object.Placement.Base.add(v)
                self.textpos.translation.setValue(pos)
                self.textpos.rotation.setValue(vobj.Object.Placement.Rotation.Q)
        elif prop == "Line":
            if hasattr(vobj,"Line"):
                if vobj.Line:
                    self.lineswitch.whichChild = 0
                else:
                    self.lineswitch.whichChild = -1
        elif prop == "ArrowType":
            if hasattr(vobj,"ArrowType"):
                if len(vobj.Object.Points) > 1:
                    if hasattr(self,"symbol"):
                        if self.arrow.findChild(self.symbol) != -1:
                                self.arrow.removeChild(self.symbol)
                    s = arrowtypes.index(vobj.ArrowType)
                    self.symbol = dimSymbol(s)
                    self.arrow.addChild(self.symbol)
                    self.arrowpos.translation.setValue(vobj.Object.Points[-1])
                    v1 = vobj.Object.Points[-2].sub(vobj.Object.Points[-1])
                    if not DraftVecUtils.isNull(v1):
                        v1.normalize()
                        import DraftGeomUtils
                        v2 = Vector(0,0,1)
                        if round(v2.getAngle(v1),4) in [0,round(math.pi,4)]:
                            v2 = Vector(0,1,0)
                        v3 = v1.cross(v2).negative()
                        q = FreeCAD.Placement(DraftVecUtils.getPlaneRotation(v1,v3,v2)).Rotation.Q
                        self.arrowpos.rotation.setValue((q[0],q[1],q[2],q[3]))
        elif prop == "ArrowSize":
            if hasattr(vobj,"ArrowSize"):
                s = vobj.ArrowSize.Value
                if s:
                    self.arrowpos.scaleFactor.setValue((s,s,s))
        elif prop == "Frame":
            if hasattr(vobj,"Frame"):
                self.frame.coordIndex.deleteValues(0)
                if vobj.Frame == "Rectangle":
                    tsize = self.getTextSize(vobj)
                    pts = []
                    base = vobj.Object.Placement.Base.sub(Vector(self.textpos.translation.getValue().getValue()))
                    pts.append(base.add(Vector(0,tsize[1]*3,0)))
                    pts.append(pts[-1].add(Vector(-tsize[0]*6,0,0)))
                    pts.append(pts[-1].add(Vector(0,-tsize[1]*6,0)))
                    pts.append(pts[-1].add(Vector(tsize[0]*6,0,0)))
                    pts.append(pts[0])
                    self.fcoords.point.setValues(pts)
                    self.frame.coordIndex.setValues(0,len(pts),range(len(pts)))

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None


class Draft_Label(Creator):
    """The Draft_Label command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Label',
                'Accel' : "D, L",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Label", "Label"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Label", "Creates a label, optionally attached to a selected object or element")}

    def Activated(self):
        self.name = translate("draft","Label", utf8_decode=True)
        Creator.Activated(self,self.name,noplanesetup=True)
        self.ghost = None
        self.labeltype = Draft.getParam("labeltype","Custom")
        self.sel = FreeCADGui.Selection.getSelectionEx()
        if self.sel:
            self.sel = self.sel[0]
        self.ui.labelUi(self.name,callback=self.setmode)
        self.ui.xValue.setFocus()
        self.ui.xValue.selectAll()
        self.ghost = DraftTrackers.lineTracker()
        self.call = self.view.addEventCallback("SoEvent",self.action)
        FreeCAD.Console.PrintMessage(translate("draft", "Pick target point")+"\n")
        self.ui.isCopy.hide()

    def setmode(self,i):
        self.labeltype = ["Custom","Name","Label","Position","Length","Area","Volume","Tag","Material"][i]
        Draft.setParam("labeltype",self.labeltype)

    def finish(self,closed=False,cont=False):
        if self.ghost:
            self.ghost.finalize()
        Creator.finish(self)

    def create(self):
        if len(self.node) == 3:
            targetpoint = self.node[0]
            basepoint = self.node[2]
            v = self.node[2].sub(self.node[1])
            dist = v.Length
            if hasattr(FreeCAD,"DraftWorkingPlane"):
                h = FreeCAD.DraftWorkingPlane.u
                n = FreeCAD.DraftWorkingPlane.axis
                r = FreeCAD.DraftWorkingPlane.getRotation().Rotation
            else:
                h = Vector(1,0,0)
                n = Vector(0,0,1)
                r = FreeCAD.Rotation()
            if abs(DraftVecUtils.angle(v,h,n)) <= math.pi/4:
                direction = "Horizontal"
                dist = -dist
            elif abs(DraftVecUtils.angle(v,h,n)) >= math.pi*3/4:
                direction = "Horizontal"
            elif DraftVecUtils.angle(v,h,n) > 0:
                direction = "Vertical"
            else:
                direction = "Vertical"
                dist = -dist
            tp = "targetpoint=FreeCAD."+str(targetpoint)+","
            sel = ""
            if self.sel:
                if self.sel.SubElementNames:
                    sub = "'"+self.sel.SubElementNames[0]+"'"
                else:
                    sub = "()"
                sel="target=(FreeCAD.ActiveDocument."+self.sel.Object.Name+","+sub+"),"
            pl = "placement=FreeCAD.Placement(FreeCAD."+str(basepoint)+",FreeCAD.Rotation"+str(r.Q)+")"
            FreeCAD.ActiveDocument.openTransaction("Create Label")
            FreeCADGui.addModule("Draft")
            FreeCADGui.doCommand("l = Draft.makeLabel("+tp+sel+"direction='"+direction+"',distance="+str(dist)+",labeltype='"+self.labeltype+"',"+pl+")")
            FreeCAD.ActiveDocument.recompute()
            FreeCAD.ActiveDocument.commitTransaction()
        self.finish()

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event":
            if hasattr(FreeCADGui,"Snapper"):
                FreeCADGui.Snapper.affinity = None # don't keep affinity
            if len(self.node) == 2:
                setMod(arg,MODCONSTRAIN,True)
            self.point,ctrlPoint,info = getPoint(self,arg)
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if self.point:
                    self.ui.redraw()
                    if not self.node:
                        # first click
                        self.node.append(self.point)
                        self.ui.isRelative.show()
                        FreeCAD.Console.PrintMessage(translate("draft", "Pick endpoint of leader line")+"\n")
                        if self.planetrack:
                            self.planetrack.set(self.point)
                    elif len(self.node) == 1:
                        # second click
                        self.node.append(self.point)
                        if self.ghost:
                            self.ghost.p1(self.node[0])
                            self.ghost.p2(self.node[1])
                            self.ghost.on()
                        FreeCAD.Console.PrintMessage(translate("draft", "Pick text position")+"\n")
                    else:
                        # third click
                        self.node.append(self.point)
                        self.create()

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        self.point = Vector(numx,numy,numz)
        if not self.node:
            # first click
            self.node.append(self.point)
            self.ui.isRelative.show()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick endpoint of leader line")+"\n")
            if self.planetrack:
                self.planetrack.set(self.point)
        elif len(self.node) == 1:
            # second click
            self.node.append(self.point)
            if self.ghost:
                self.ghost.p1(self.node[0])
                self.ghost.p2(self.node[1])
                self.ghost.on()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick text position")+"\n")
        else:
            # third click
            self.node.append(self.point)
            self.create()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Label',Draft_Label())

