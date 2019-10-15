
def makeAngularDimension(center,angles,p3,normal=None):
    """makeAngularDimension(center,angle1,angle2,p3,[normal]): creates an angular Dimension
    from the given center, with the given list of angles, passing through p3.
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Dimension")
    _AngularDimension(obj)
    obj.Center = center
    for a in range(len(angles)):
        if angles[a] > 2*math.pi:
            angles[a] = angles[a]-(2*math.pi)
    obj.FirstAngle = math.degrees(angles[1])
    obj.LastAngle = math.degrees(angles[0])
    obj.Dimline = p3
    if not normal:
        if hasattr(FreeCAD,"DraftWorkingPlane"):
            normal = FreeCAD.DraftWorkingPlane.axis
        else:
            normal = Vector(0,0,1)
    if gui:
        # invert the normal if we are viewing it from the back
        vnorm = get3DView().getViewDirection()
        if vnorm.getAngle(normal) < math.pi/2:
            normal = normal.negative()
    obj.Normal = normal
    if gui:
        _ViewProviderAngularDimension(obj.ViewObject)
        formatObject(obj)
        select(obj)

    return obj


class _AngularDimension(_DraftObject):
    """The Draft AngularDimension object"""
    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"AngularDimension")
        obj.addProperty("App::PropertyAngle","FirstAngle","Draft",QT_TRANSLATE_NOOP("App::Property","Start angle of the dimension"))
        obj.addProperty("App::PropertyAngle","LastAngle","Draft",QT_TRANSLATE_NOOP("App::Property","End angle of the dimension"))
        obj.addProperty("App::PropertyVectorDistance","Dimline","Draft",QT_TRANSLATE_NOOP("App::Property","Point through which the dimension line passes"))
        obj.addProperty("App::PropertyVectorDistance","Center","Draft",QT_TRANSLATE_NOOP("App::Property","The center point of this dimension"))
        obj.addProperty("App::PropertyVector","Normal","Draft",QT_TRANSLATE_NOOP("App::Property","The normal direction of this dimension"))
        obj.addProperty("App::PropertyLink","Support","Draft",QT_TRANSLATE_NOOP("App::Property","The object measured by this dimension"))
        obj.addProperty("App::PropertyLinkSubList","LinkedGeometry","Draft",QT_TRANSLATE_NOOP("App::Property","The geometry this dimension is linked to"))
        obj.addProperty("App::PropertyAngle","Angle","Draft",QT_TRANSLATE_NOOP("App::Property","The measurement of this dimension"))
        obj.FirstAngle = 0
        obj.LastAngle = 90
        obj.Dimline = FreeCAD.Vector(0,1,0)
        obj.Center = FreeCAD.Vector(0,0,0)
        obj.Normal = FreeCAD.Vector(0,0,1)

    def onChanged(self,obj,prop):
        if hasattr(obj,"Angle"):
            obj.setEditorMode('Angle',1)
        if hasattr(obj,"Normal"):
            obj.setEditorMode('Normal',2)
        if hasattr(obj,"Support"):
            obj.setEditorMode('Support',2)

    def execute(self, fp):
        if fp.ViewObject:
            fp.ViewObject.update()


class _ViewProviderAngularDimension(_ViewProviderDraft):
    """A View Provider for the Draft Angular Dimension object"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength","FontSize","Draft",QT_TRANSLATE_NOOP("App::Property","Font size"))
        obj.addProperty("App::PropertyInteger","Decimals","Draft",QT_TRANSLATE_NOOP("App::Property","The number of decimals to show"))
        obj.addProperty("App::PropertyFont","FontName","Draft",QT_TRANSLATE_NOOP("App::Property","Font name"))
        obj.addProperty("App::PropertyLength","ArrowSize","Draft",QT_TRANSLATE_NOOP("App::Property","Arrow size"))
        obj.addProperty("App::PropertyLength","TextSpacing","Draft",QT_TRANSLATE_NOOP("App::Property","The spacing between the text and the dimension line"))
        obj.addProperty("App::PropertyEnumeration","ArrowType","Draft",QT_TRANSLATE_NOOP("App::Property","Arrow type"))
        obj.addProperty("App::PropertyFloat","LineWidth","Draft",QT_TRANSLATE_NOOP("App::Property","Line width"))
        obj.addProperty("App::PropertyColor","LineColor","Draft",QT_TRANSLATE_NOOP("App::Property","Line color"))
        obj.addProperty("App::PropertyBool","FlipArrows","Draft",QT_TRANSLATE_NOOP("App::Property","Rotate the dimension arrows 180 degrees"))
        obj.addProperty("App::PropertyBool","ShowUnit","Draft",QT_TRANSLATE_NOOP("App::Property","Show the unit suffix"))
        obj.addProperty("App::PropertyVectorDistance","TextPosition","Draft",QT_TRANSLATE_NOOP("App::Property","The position of the text. Leave (0,0,0) for automatic position"))
        obj.addProperty("App::PropertyString","Override","Draft",QT_TRANSLATE_NOOP("App::Property","Text override. Use 'dim' to insert the dimension length"))
        obj.FontSize = getParam("textheight",0.20)
        obj.FontName = getParam("textfont","")
        obj.TextSpacing = getParam("dimspacing",0.05)
        obj.ArrowSize = getParam("arrowsize",0.1)
        obj.ArrowType = arrowtypes
        obj.ArrowType = arrowtypes[getParam("dimsymbol",0)]
        obj.Override = ''
        obj.Decimals = getParam("dimPrecision",2)
        obj.ShowUnit = getParam("showUnit",True)
        _ViewProviderDraft.__init__(self,obj)

    def attach(self, vobj):
        from pivy import coin
        self.Object = vobj.Object
        self.color = coin.SoBaseColor()
        self.color.rgb.setValue(vobj.LineColor[0],vobj.LineColor[1],vobj.LineColor[2])
        self.font = coin.SoFont()
        self.font3d = coin.SoFont()
        self.text = coin.SoAsciiText()
        self.text3d = coin.SoText2()
        self.text.string = "d" # some versions of coin crash if string is not set
        self.text3d.string = "d"
        self.text.justification = self.text3d.justification = coin.SoAsciiText.CENTER
        self.textpos = coin.SoTransform()
        label = coin.SoSeparator()
        label.addChild(self.textpos)
        label.addChild(self.color)
        label.addChild(self.font)
        label.addChild(self.text)
        label3d = coin.SoSeparator()
        label3d.addChild(self.textpos)
        label3d.addChild(self.color)
        label3d.addChild(self.font3d)
        label3d.addChild(self.text3d)
        self.coord1 = coin.SoCoordinate3()
        self.trans1 = coin.SoTransform()
        self.coord2 = coin.SoCoordinate3()
        self.trans2 = coin.SoTransform()
        self.marks = coin.SoSeparator()
        self.drawstyle = coin.SoDrawStyle()
        self.coords = coin.SoCoordinate3()
        self.arc = coin.SoType.fromName("SoBrepEdgeSet").createInstance()
        self.node = coin.SoGroup()
        self.node.addChild(self.color)
        self.node.addChild(self.drawstyle)
        self.node.addChild(self.coords)
        self.node.addChild(self.arc)
        self.node.addChild(self.marks)
        self.node.addChild(label)
        self.node3d = coin.SoGroup()
        self.node3d.addChild(self.color)
        self.node3d.addChild(self.drawstyle)
        self.node3d.addChild(self.coords)
        self.node3d.addChild(self.arc)
        self.node3d.addChild(self.marks)
        self.node3d.addChild(label3d)
        vobj.addDisplayMode(self.node,"2D")
        vobj.addDisplayMode(self.node3d,"3D")
        self.updateData(vobj.Object,None)
        self.onChanged(vobj,"FontSize")
        self.onChanged(vobj,"FontName")
        self.onChanged(vobj,"ArrowType")
        self.onChanged(vobj,"LineColor")

    def updateData(self, obj, prop):
        if hasattr(self,"arc"):
            from pivy import coin
            import Part, DraftGeomUtils
            import DraftGui
            text = None
            ivob = None
            arcsegs = 24

            # calculate the arc data
            if DraftVecUtils.isNull(obj.Normal):
                norm = Vector(0,0,1)
            else:
                norm = obj.Normal
            radius = (obj.Dimline.sub(obj.Center)).Length
            self.circle = Part.makeCircle(radius,obj.Center,norm,obj.FirstAngle.Value,obj.LastAngle.Value)
            self.p2 = self.circle.Vertexes[0].Point
            self.p3 = self.circle.Vertexes[-1].Point
            mp = DraftGeomUtils.findMidpoint(self.circle.Edges[0])
            ray = mp.sub(obj.Center)

            # set text value
            if obj.LastAngle.Value > obj.FirstAngle.Value:
                a = obj.LastAngle.Value - obj.FirstAngle.Value
            else:
                a = (360 - obj.FirstAngle.Value) + obj.LastAngle.Value
            su = True
            if hasattr(obj.ViewObject,"ShowUnit"):
                su = obj.ViewObject.ShowUnit
            if hasattr(obj.ViewObject,"Decimals"):
                self.string = DraftGui.displayExternal(a,obj.ViewObject.Decimals,'Angle',su)
            else:
                self.string = DraftGui.displayExternal(a,None,'Angle',su)
            if obj.ViewObject.Override:
                self.string = obj.ViewObject.Override.replace("$dim",\
                    self.string)
            self.text.string = self.text3d.string = stringencodecoin(self.string)

            # check display mode
            try:
                m = obj.ViewObject.DisplayMode
            except: # swallow all exceptions here since it always fails on first run (Displaymode enum no set yet)
                m = ["2D","3D"][getParam("dimstyle",0)]

            # set the arc
            if m == "3D":
                # calculate the spacing of the text
                spacing = (len(self.string)*obj.ViewObject.FontSize.Value)/8.0
                pts1 = []
                cut = None
                pts2 = []
                for i in range(arcsegs+1):
                    p = self.circle.valueAt(self.circle.FirstParameter+((self.circle.LastParameter-self.circle.FirstParameter)/arcsegs)*i)
                    if (p.sub(mp)).Length <= spacing:
                        if cut == None:
                            cut = i
                    else:
                        if cut == None:
                            pts1.append([p.x,p.y,p.z])
                        else:
                            pts2.append([p.x,p.y,p.z])
                self.coords.point.setValues(pts1+pts2)
                i1 = len(pts1)
                i2 = i1+len(pts2)
                self.arc.coordIndex.setValues(0,len(pts1)+len(pts2)+1,list(range(len(pts1)))+[-1]+list(range(i1,i2)))
                if (len(pts1) >= 3) and (len(pts2) >= 3):
                    self.circle1 = Part.Arc(Vector(pts1[0][0],pts1[0][1],pts1[0][2]),Vector(pts1[1][0],pts1[1][1],pts1[1][2]),Vector(pts1[-1][0],pts1[-1][1],pts1[-1][2])).toShape()
                    self.circle2 = Part.Arc(Vector(pts2[0][0],pts2[0][1],pts2[0][2]),Vector(pts2[1][0],pts2[1][1],pts2[1][2]),Vector(pts2[-1][0],pts2[-1][1],pts2[-1][2])).toShape()
            else:
                pts = []
                for i in range(arcsegs+1):
                    p = self.circle.valueAt(self.circle.FirstParameter+((self.circle.LastParameter-self.circle.FirstParameter)/arcsegs)*i)
                    pts.append([p.x,p.y,p.z])
                self.coords.point.setValues(pts)
                self.arc.coordIndex.setValues(0,arcsegs+1,list(range(arcsegs+1)))

            # set the arrow coords and rotation
            self.trans1.translation.setValue((self.p2.x,self.p2.y,self.p2.z))
            self.coord1.point.setValue((self.p2.x,self.p2.y,self.p2.z))
            self.trans2.translation.setValue((self.p3.x,self.p3.y,self.p3.z))
            self.coord2.point.setValue((self.p3.x,self.p3.y,self.p3.z))
            # calculate small chords to make arrows look better
            arrowlength = 4*obj.ViewObject.ArrowSize.Value
            u1 = (self.circle.valueAt(self.circle.FirstParameter+arrowlength)).sub(self.circle.valueAt(self.circle.FirstParameter)).normalize()
            u2 = (self.circle.valueAt(self.circle.LastParameter)).sub(self.circle.valueAt(self.circle.LastParameter-arrowlength)).normalize()
            if hasattr(obj.ViewObject,"FlipArrows"):
                if obj.ViewObject.FlipArrows:
                    u1 = u1.negative()
                    u2 = u2.negative()
            w2 = self.circle.Curve.Axis
            w1 = w2.negative()
            v1 = w1.cross(u1)
            v2 = w2.cross(u2)
            q1 = FreeCAD.Placement(DraftVecUtils.getPlaneRotation(u1,v1,w1)).Rotation.Q
            q2 = FreeCAD.Placement(DraftVecUtils.getPlaneRotation(u2,v2,w2)).Rotation.Q
            self.trans1.rotation.setValue((q1[0],q1[1],q1[2],q1[3]))
            self.trans2.rotation.setValue((q2[0],q2[1],q2[2],q2[3]))

            # setting text pos & rot
            self.tbase = mp
            if hasattr(obj.ViewObject,"TextPosition"):
                if not DraftVecUtils.isNull(obj.ViewObject.TextPosition):
                    self.tbase = obj.ViewObject.TextPosition

            u3 = ray.cross(norm).normalize()
            v3 = norm.cross(u3)
            r = FreeCAD.Placement(DraftVecUtils.getPlaneRotation(u3,v3,norm)).Rotation
            offset = r.multVec(Vector(0,1,0))

            if hasattr(obj.ViewObject,"TextSpacing"):
                offset = DraftVecUtils.scaleTo(offset,obj.ViewObject.TextSpacing.Value)
            else:
                offset = DraftVecUtils.scaleTo(offset,0.05)
            if m == "3D":
                offset = offset.negative()
            self.tbase = self.tbase.add(offset)
            q = r.Q
            self.textpos.translation.setValue([self.tbase.x,self.tbase.y,self.tbase.z])
            self.textpos.rotation = coin.SbRotation(q[0],q[1],q[2],q[3])

            # set the angle property
            if round(obj.Angle,precision()) != round(a,precision()):
                obj.Angle = a

    def onChanged(self, vobj, prop):
        if prop == "FontSize":
            if hasattr(self,"font"):
                self.font.size = vobj.FontSize.Value
            if hasattr(self,"font3d"):
                self.font3d.size = vobj.FontSize.Value*100
            vobj.Object.touch()
        elif prop == "FontName":
            if hasattr(self,"font") and hasattr(self,"font3d"):
                self.font.name = self.font3d.name = str(vobj.FontName)
                vobj.Object.touch()
        elif prop == "LineColor":
            if hasattr(self,"color"):
                c = vobj.LineColor
                self.color.rgb.setValue(c[0],c[1],c[2])
        elif prop == "LineWidth":
            if hasattr(self,"drawstyle"):
                self.drawstyle.lineWidth = vobj.LineWidth
        elif prop in ["ArrowSize","ArrowType"]:
            if hasattr(self,"node") and hasattr(self,"p2"):
                from pivy import coin

                if not hasattr(vobj,"ArrowType"):
                    return

                # set scale
                symbol = arrowtypes.index(vobj.ArrowType)
                s = vobj.ArrowSize.Value
                self.trans1.scaleFactor.setValue((s,s,s))
                self.trans2.scaleFactor.setValue((s,s,s))

                # remove existing nodes
                self.node.removeChild(self.marks)
                self.node3d.removeChild(self.marks)

                # set new nodes
                self.marks = coin.SoSeparator()
                self.marks.addChild(self.color)
                s1 = coin.SoSeparator()
                if symbol == "Circle":
                    s1.addChild(self.coord1)
                else:
                    s1.addChild(self.trans1)
                s1.addChild(dimSymbol(symbol,invert=False))
                self.marks.addChild(s1)
                s2 = coin.SoSeparator()
                if symbol == "Circle":
                    s2.addChild(self.coord2)
                else:
                    s2.addChild(self.trans2)
                s2.addChild(dimSymbol(symbol,invert=True))
                self.marks.addChild(s2)
                self.node.insertChild(self.marks,2)
                self.node3d.insertChild(self.marks,2)
                vobj.Object.touch()
        else:
            self.updateData(vobj.Object, None)

    def doubleClicked(self,vobj):
        self.setEdit(vobj)

    def getDisplayModes(self,obj):
        modes=[]
        modes.extend(["2D","3D"])
        return modes

    def getDefaultDisplayMode(self):
        if hasattr(self,"defaultmode"):
            return self.defaultmode
        else:
            return ["2D","3D"][getParam("dimstyle",0)]

    def getIcon(self):
        return """
                        /* XPM */
                        static char * dim_xpm[] = {
                        "16 16 4 1",
                        "   c None",
                        ".  c #000000",
                        "+  c #FFFF00",
                        "@  c #FFFFFF",
                        "                ",
                        "                ",
                        "     .    .     ",
                        "    ..    ..    ",
                        "   .+.    .+.   ",
                        "  .++.    .++.  ",
                        " .+++. .. .+++. ",
                        ".++++. .. .++++.",
                        " .+++. .. .+++. ",
                        "  .++.    .++.  ",
                        "   .+.    .+.   ",
                        "    ..    ..    ",
                        "     .    .     ",
                        "                ",
                        "                ",
                        "                "};
                        """

    def __getstate__(self):
        return self.Object.ViewObject.DisplayMode

    def __setstate__(self,state):
        if state:
            self.defaultmode = state
            self.setDisplayMode(state)


