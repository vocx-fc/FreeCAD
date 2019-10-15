
def makeDimension(p1,p2,p3=None,p4=None):
    """makeDimension(p1,p2,[p3]) or makeDimension(object,i1,i2,p3)
    or makeDimension(objlist,indices,p3): Creates a Dimension object with
    the dimension line passign through p3.The current line width and color
    will be used. There are multiple  ways to create a dimension, depending on
    the arguments you pass to it:
    - (p1,p2,p3): creates a standard dimension from p1 to p2
    - (object,i1,i2,p3): creates a linked dimension to the given object,
    measuring the distance between its vertices indexed i1 and i2
    - (object,i1,mode,p3): creates a linked dimension
    to the given object, i1 is the index of the (curved) edge to measure,
    and mode is either "radius" or "diameter".
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Dimension")
    _Dimension(obj)
    if gui:
        _ViewProviderDimension(obj.ViewObject)
    if isinstance(p1,Vector) and isinstance(p2,Vector):
        obj.Start = p1
        obj.End = p2
        if not p3:
            p3 = p2.sub(p1)
            p3.multiply(0.5)
            p3 = p1.add(p3)
    elif isinstance(p2,int) and isinstance(p3,int):
        l = []
        l.append((p1,"Vertex"+str(p2+1)))
        l.append((p1,"Vertex"+str(p3+1)))
        obj.LinkedGeometry = l
        obj.Support = p1
        p3 = p4
        if not p3:
            v1 = obj.Base.Shape.Vertexes[idx[0]].Point
            v2 = obj.Base.Shape.Vertexes[idx[1]].Point
            p3 = v2.sub(v1)
            p3.multiply(0.5)
            p3 = v1.add(p3)
    elif isinstance(p3,str):
        l = []
        l.append((p1,"Edge"+str(p2+1)))
        if p3 == "radius":
            #l.append((p1,"Center"))
            obj.ViewObject.Override = "R $dim"
            obj.Diameter = False
        elif p3 == "diameter":
            #l.append((p1,"Diameter"))
            obj.ViewObject.Override = "Ø $dim"
            obj.Diameter = True
        obj.LinkedGeometry = l
        obj.Support = p1
        p3 = p4
        if not p3:
            p3 = p1.Shape.Edges[p2].Curve.Center.add(Vector(1,0,0))
    obj.Dimline = p3
    if hasattr(FreeCAD,"DraftWorkingPlane"):
        normal = FreeCAD.DraftWorkingPlane.axis
    else:
        normal = FreeCAD.Vector(0,0,1)
    if gui:
        # invert the normal if we are viewing it from the back
        vnorm = get3DView().getViewDirection()
        if vnorm.getAngle(normal) < math.pi/2:
            normal = normal.negative()
    obj.Normal = normal
    if gui:
        formatObject(obj)
        select(obj)

    return obj


class _Dimension(_DraftObject):
    """The Draft Dimension object"""
    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"Dimension")
        obj.addProperty("App::PropertyVectorDistance","Start","Draft",QT_TRANSLATE_NOOP("App::Property","Startpoint of dimension"))
        obj.addProperty("App::PropertyVectorDistance","End","Draft",QT_TRANSLATE_NOOP("App::Property","Endpoint of dimension"))
        obj.addProperty("App::PropertyVector","Normal","Draft",QT_TRANSLATE_NOOP("App::Property","The normal direction of this dimension"))
        obj.addProperty("App::PropertyVector","Direction","Draft",QT_TRANSLATE_NOOP("App::Property","The normal direction of this dimension"))
        obj.addProperty("App::PropertyVectorDistance","Dimline","Draft",QT_TRANSLATE_NOOP("App::Property","Point through which the dimension line passes"))
        obj.addProperty("App::PropertyLink","Support","Draft",QT_TRANSLATE_NOOP("App::Property","The object measured by this dimension"))
        obj.addProperty("App::PropertyLinkSubList","LinkedGeometry","Draft",QT_TRANSLATE_NOOP("App::Property","The geometry this dimension is linked to"))
        obj.addProperty("App::PropertyLength","Distance","Draft",QT_TRANSLATE_NOOP("App::Property","The measurement of this dimension"))
        obj.addProperty("App::PropertyBool","Diameter","Draft",QT_TRANSLATE_NOOP("App::Property","For arc/circle measurements, false = radius, true = diameter"))
        obj.Start = FreeCAD.Vector(0,0,0)
        obj.End = FreeCAD.Vector(1,0,0)
        obj.Dimline = FreeCAD.Vector(0,1,0)
        obj.Normal = FreeCAD.Vector(0,0,1)

    def onChanged(self,obj,prop):
        if hasattr(obj,"Distance"):
            obj.setEditorMode('Distance',1)
        #if hasattr(obj,"Normal"):
        #    obj.setEditorMode('Normal',2)
        if hasattr(obj,"Support"):
            obj.setEditorMode('Support',2)

    def execute(self, obj):
        import DraftGeomUtils
        # set start point and end point according to the linked geometry
        if obj.LinkedGeometry:
            if len(obj.LinkedGeometry) == 1:
                lobj = obj.LinkedGeometry[0][0]
                lsub = obj.LinkedGeometry[0][1]
                if len(lsub) == 1:
                    if "Edge" in lsub[0]:
                        n = int(lsub[0][4:])-1
                        edge = lobj.Shape.Edges[n]
                        if DraftGeomUtils.geomType(edge) == "Line":
                            obj.Start = edge.Vertexes[0].Point
                            obj.End = edge.Vertexes[-1].Point
                        elif DraftGeomUtils.geomType(edge) == "Circle":
                            c = edge.Curve.Center
                            r = edge.Curve.Radius
                            a = edge.Curve.Axis
                            ray = obj.Dimline.sub(c).projectToPlane(Vector(0,0,0),a)
                            if (ray.Length == 0):
                                ray = a.cross(Vector(1,0,0))
                                if (ray.Length == 0):
                                    ray = a.cross(Vector(0,1,0))
                            ray = DraftVecUtils.scaleTo(ray,r)
                            if hasattr(obj,"Diameter"):
                                if obj.Diameter:
                                    obj.Start = c.add(ray.negative())
                                    obj.End = c.add(ray)
                                else:
                                    obj.Start = c
                                    obj.End = c.add(ray)
                elif len(lsub) == 2:
                    if ("Vertex" in lsub[0]) and ("Vertex" in lsub[1]):
                        n1 = int(lsub[0][6:])-1
                        n2 = int(lsub[1][6:])-1
                        obj.Start = lobj.Shape.Vertexes[n1].Point
                        obj.End = lobj.Shape.Vertexes[n2].Point
            elif len(obj.LinkedGeometry) == 2:
                lobj1 = obj.LinkedGeometry[0][0]
                lobj2 = obj.LinkedGeometry[1][0]
                lsub1 = obj.LinkedGeometry[0][1]
                lsub2 = obj.LinkedGeometry[1][1]
                if (len(lsub1) == 1) and (len(lsub2) == 1):
                    if ("Vertex" in lsub1[0]) and ("Vertex" in lsub2[1]):
                        n1 = int(lsub1[0][6:])-1
                        n2 = int(lsub2[0][6:])-1
                        obj.Start = lobj1.Shape.Vertexes[n1].Point
                        obj.End = lobj2.Shape.Vertexes[n2].Point
        # set the distance property
        total_len = (obj.Start.sub(obj.End)).Length
        if round(obj.Distance.Value, precision()) != round(total_len, precision()):
            obj.Distance = total_len
        if gui:
            if obj.ViewObject:
                obj.ViewObject.update()


class _ViewProviderDimension(_ViewProviderDraft):
    """A View Provider for the Draft Dimension object"""
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength","FontSize","Draft",QT_TRANSLATE_NOOP("App::Property","Font size"))
        obj.addProperty("App::PropertyInteger","Decimals","Draft",QT_TRANSLATE_NOOP("App::Property","The number of decimals to show"))
        obj.addProperty("App::PropertyLength","ArrowSize","Draft",QT_TRANSLATE_NOOP("App::Property","Arrow size"))
        obj.addProperty("App::PropertyLength","TextSpacing","Draft",QT_TRANSLATE_NOOP("App::Property","The spacing between the text and the dimension line"))
        obj.addProperty("App::PropertyEnumeration","ArrowType","Draft",QT_TRANSLATE_NOOP("App::Property","Arrow type"))
        obj.addProperty("App::PropertyFont","FontName","Draft",QT_TRANSLATE_NOOP("App::Property","Font name"))
        obj.addProperty("App::PropertyFloat","LineWidth","Draft",QT_TRANSLATE_NOOP("App::Property","Line width"))
        obj.addProperty("App::PropertyColor","LineColor","Draft",QT_TRANSLATE_NOOP("App::Property","Line color"))
        obj.addProperty("App::PropertyDistance","ExtLines","Draft",QT_TRANSLATE_NOOP("App::Property","Length of the extension lines"))
        obj.addProperty("App::PropertyDistance","DimOvershoot","Draft",QT_TRANSLATE_NOOP("App::Property","The distance the dimension line is extended past the extension lines"))
        obj.addProperty("App::PropertyDistance","ExtOvershoot","Draft",QT_TRANSLATE_NOOP("App::Property","Length of the extension line above the dimension line"))
        obj.addProperty("App::PropertyBool","FlipArrows","Draft",QT_TRANSLATE_NOOP("App::Property","Rotate the dimension arrows 180 degrees"))
        obj.addProperty("App::PropertyBool","FlipText","Draft",QT_TRANSLATE_NOOP("App::Property","Rotate the dimension text 180 degrees"))
        obj.addProperty("App::PropertyBool","ShowUnit","Draft",QT_TRANSLATE_NOOP("App::Property","Show the unit suffix"))
        obj.addProperty("App::PropertyVectorDistance","TextPosition","Draft",QT_TRANSLATE_NOOP("App::Property","The position of the text. Leave (0,0,0) for automatic position"))
        obj.addProperty("App::PropertyString","Override","Draft",QT_TRANSLATE_NOOP("App::Property","Text override. Use $dim to insert the dimension length"))
        obj.addProperty("App::PropertyString","UnitOverride","Draft",QT_TRANSLATE_NOOP("App::Property","A unit to express the measurement. Leave blank for system default"))
        obj.FontSize = getParam("textheight",0.20)
        obj.TextSpacing = getParam("dimspacing",0.05)
        obj.FontName = getParam("textfont","")
        obj.ArrowSize = getParam("arrowsize",0.1)
        obj.ArrowType = arrowtypes
        obj.ArrowType = arrowtypes[getParam("dimsymbol",0)]
        obj.ExtLines = getParam("extlines",0.3)
        obj.DimOvershoot = getParam("dimovershoot",0)
        obj.ExtOvershoot = getParam("extovershoot",0)
        obj.Decimals = getParam("dimPrecision",2)
        obj.ShowUnit = getParam("showUnit",True)
        _ViewProviderDraft.__init__(self,obj)

    def attach(self, vobj):
        """called on object creation"""
        from pivy import coin
        self.Object = vobj.Object
        self.color = coin.SoBaseColor()
        self.font = coin.SoFont()
        self.font3d = coin.SoFont()
        self.text = coin.SoAsciiText()
        self.text3d = coin.SoText2()
        self.text.string = "d" # some versions of coin crash if string is not set
        self.text3d.string = "d"
        self.textpos = coin.SoTransform()
        self.text.justification = self.text3d.justification = coin.SoAsciiText.CENTER
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
        self.transDimOvershoot1 = coin.SoTransform()
        self.transDimOvershoot2 = coin.SoTransform()
        self.transExtOvershoot1 = coin.SoTransform()
        self.transExtOvershoot2 = coin.SoTransform()
        self.marks = coin.SoSeparator()
        self.marksDimOvershoot = coin.SoSeparator()
        self.marksExtOvershoot = coin.SoSeparator()
        self.drawstyle = coin.SoDrawStyle()
        self.line = coin.SoType.fromName("SoBrepEdgeSet").createInstance()
        self.coords = coin.SoCoordinate3()
        self.node = coin.SoGroup()
        self.node.addChild(self.color)
        self.node.addChild(self.drawstyle)
        self.node.addChild(self.coords)
        self.node.addChild(self.line)
        self.node.addChild(self.marks)
        self.node.addChild(self.marksDimOvershoot)
        self.node.addChild(self.marksExtOvershoot)
        self.node.addChild(label)
        self.node3d = coin.SoGroup()
        self.node3d.addChild(self.color)
        self.node3d.addChild(self.drawstyle)
        self.node3d.addChild(self.coords)
        self.node3d.addChild(self.line)
        self.node3d.addChild(self.marks)
        self.node3d.addChild(self.marksDimOvershoot)
        self.node3d.addChild(self.marksExtOvershoot)
        self.node3d.addChild(label3d)
        vobj.addDisplayMode(self.node,"2D")
        vobj.addDisplayMode(self.node3d,"3D")
        self.updateData(vobj.Object,"Start")
        self.onChanged(vobj,"FontSize")
        self.onChanged(vobj,"FontName")
        self.onChanged(vobj,"ArrowType")
        self.onChanged(vobj,"LineColor")
        self.onChanged(vobj,"DimOvershoot")
        self.onChanged(vobj,"ExtOvershoot")

    def updateData(self, obj, prop):
        """called when the base object is changed"""
        import DraftGui
        if prop in ["Start","End","Dimline","Direction"]:

            if obj.Start == obj.End:
                return

            if not hasattr(self,"node"):
                return

            import Part, DraftGeomUtils
            from pivy import coin

            # calculate the 4 points
            self.p1 = obj.Start
            self.p4 = obj.End
            base = None
            if hasattr(obj,"Direction"):
                if not DraftVecUtils.isNull(obj.Direction):
                    v2 = self.p1.sub(obj.Dimline)
                    v3 = self.p4.sub(obj.Dimline)
                    v2 = DraftVecUtils.project(v2,obj.Direction)
                    v3 = DraftVecUtils.project(v3,obj.Direction)
                    self.p2 = obj.Dimline.add(v2)
                    self.p3 = obj.Dimline.add(v3)
                    if DraftVecUtils.equals(self.p2,self.p3):
                        base = None
                        proj = None
                    else:
                        base = Part.LineSegment(self.p2,self.p3).toShape()
                        proj = DraftGeomUtils.findDistance(self.p1,base)
                        if proj:
                            proj = proj.negative()
            if not base:
                if DraftVecUtils.equals(self.p1,self.p4):
                    base = None
                    proj = None
                else:
                    base = Part.LineSegment(self.p1,self.p4).toShape()
                    proj = DraftGeomUtils.findDistance(obj.Dimline,base)
                if proj:
                    self.p2 = self.p1.add(proj.negative())
                    self.p3 = self.p4.add(proj.negative())
                else:
                    self.p2 = self.p1
                    self.p3 = self.p4
            if proj:
                if hasattr(obj.ViewObject,"ExtLines"):
                    dmax = obj.ViewObject.ExtLines.Value
                    if dmax and (proj.Length > dmax):
                        if (dmax > 0):
                            self.p1 = self.p2.add(DraftVecUtils.scaleTo(proj,dmax))
                            self.p4 = self.p3.add(DraftVecUtils.scaleTo(proj,dmax))
                        else:
                            rest = proj.Length + dmax
                            self.p1 = self.p2.add(DraftVecUtils.scaleTo(proj,rest))
                            self.p4 = self.p3.add(DraftVecUtils.scaleTo(proj,rest))
            else:
                proj = (self.p3.sub(self.p2)).cross(Vector(0,0,1))

            # calculate the arrows positions
            self.trans1.translation.setValue((self.p2.x,self.p2.y,self.p2.z))
            self.coord1.point.setValue((self.p2.x,self.p2.y,self.p2.z))
            self.trans2.translation.setValue((self.p3.x,self.p3.y,self.p3.z))
            self.coord2.point.setValue((self.p3.x,self.p3.y,self.p3.z))

            # calculate dimension and extension lines overshoots positions
            self.transDimOvershoot1.translation.setValue((self.p2.x,self.p2.y,self.p2.z))
            self.transDimOvershoot2.translation.setValue((self.p3.x,self.p3.y,self.p3.z))
            self.transExtOvershoot1.translation.setValue((self.p2.x,self.p2.y,self.p2.z))
            self.transExtOvershoot2.translation.setValue((self.p3.x,self.p3.y,self.p3.z))

            # calculate the text position and orientation
            if hasattr(obj,"Normal"):
                if DraftVecUtils.isNull(obj.Normal):
                    if proj:
                        norm = (self.p3.sub(self.p2).cross(proj)).negative()
                    else:
                        norm = Vector(0,0,1)
                else:
                    norm = FreeCAD.Vector(obj.Normal)
            else:
                if proj:
                    norm = (self.p3.sub(self.p2).cross(proj)).negative()
                else:
                    norm = Vector(0,0,1)
            if not DraftVecUtils.isNull(norm):
                norm.normalize()
            u = self.p3.sub(self.p2)
            u.normalize()
            v1 = norm.cross(u)
            rot1 = FreeCAD.Placement(DraftVecUtils.getPlaneRotation(u,v1,norm)).Rotation.Q
            self.transDimOvershoot1.rotation.setValue((rot1[0],rot1[1],rot1[2],rot1[3]))
            self.transDimOvershoot2.rotation.setValue((rot1[0],rot1[1],rot1[2],rot1[3]))
            if hasattr(obj.ViewObject,"FlipArrows"):
                if obj.ViewObject.FlipArrows:
                    u = u.negative()
            v2 = norm.cross(u)
            rot2 = FreeCAD.Placement(DraftVecUtils.getPlaneRotation(u,v2,norm)).Rotation.Q
            self.trans1.rotation.setValue((rot2[0],rot2[1],rot2[2],rot2[3]))
            self.trans2.rotation.setValue((rot2[0],rot2[1],rot2[2],rot2[3]))
            if self.p1 != self.p2:
                u3 = self.p1.sub(self.p2)
                u3.normalize()
                v3 = norm.cross(u3)
                rot3 = FreeCAD.Placement(DraftVecUtils.getPlaneRotation(u3,v3,norm)).Rotation.Q
                self.transExtOvershoot1.rotation.setValue((rot3[0],rot3[1],rot3[2],rot3[3]))
                self.transExtOvershoot2.rotation.setValue((rot3[0],rot3[1],rot3[2],rot3[3]))
            if hasattr(obj.ViewObject,"TextSpacing"):
                offset = DraftVecUtils.scaleTo(v1,obj.ViewObject.TextSpacing.Value)
            else:
                offset = DraftVecUtils.scaleTo(v1,0.05)
            rott = rot1
            if hasattr(obj.ViewObject,"FlipText"):
                if obj.ViewObject.FlipText:
                    rott = FreeCAD.Rotation(*rott).multiply(FreeCAD.Rotation(norm,180)).Q
                    offset = offset.negative()
            # setting text
            try:
                m = obj.ViewObject.DisplayMode
            except: # swallow all exceptions here since it always fails on first run (Displaymode enum no set yet)
                m = ["2D","3D"][getParam("dimstyle",0)]
            if m == "3D":
                offset = offset.negative()
            self.tbase = (self.p2.add((self.p3.sub(self.p2).multiply(0.5)))).add(offset)
            if hasattr(obj.ViewObject,"TextPosition"):
                if not DraftVecUtils.isNull(obj.ViewObject.TextPosition):
                    self.tbase = obj.ViewObject.TextPosition
            self.textpos.translation.setValue([self.tbase.x,self.tbase.y,self.tbase.z])
            self.textpos.rotation = coin.SbRotation(rott[0],rott[1],rott[2],rott[3])
            su = True
            if hasattr(obj.ViewObject,"ShowUnit"):
                su = obj.ViewObject.ShowUnit
            # set text value
            l = self.p3.sub(self.p2).Length
            unit = None
            if hasattr(obj.ViewObject,"UnitOverride"):
                unit = obj.ViewObject.UnitOverride
            # special representation if "Building US" scheme
            if FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Units").GetInt("UserSchema",0) == 5:
                s = FreeCAD.Units.Quantity(l,FreeCAD.Units.Length).UserString
                self.string = s.replace("' ","'- ")
                self.string = s.replace("+"," ")
            elif hasattr(obj.ViewObject,"Decimals"):
                self.string = DraftGui.displayExternal(l,obj.ViewObject.Decimals,'Length',su,unit)
            else:
                self.string = DraftGui.displayExternal(l,None,'Length',su,unit)
            if hasattr(obj.ViewObject,"Override"):
                if obj.ViewObject.Override:
                    self.string = obj.ViewObject.Override.replace("$dim",\
                            self.string)
            self.text.string = self.text3d.string = stringencodecoin(self.string)

            # set the lines
            if m == "3D":
                # calculate the spacing of the text
                textsize = (len(self.string)*obj.ViewObject.FontSize.Value)/4.0
                spacing = ((self.p3.sub(self.p2)).Length/2.0) - textsize
                self.p2a = self.p2.add(DraftVecUtils.scaleTo(self.p3.sub(self.p2),spacing))
                self.p2b = self.p3.add(DraftVecUtils.scaleTo(self.p2.sub(self.p3),spacing))
                self.coords.point.setValues([[self.p1.x,self.p1.y,self.p1.z],
                                             [self.p2.x,self.p2.y,self.p2.z],
                                             [self.p2a.x,self.p2a.y,self.p2a.z],
                                             [self.p2b.x,self.p2b.y,self.p2b.z],
                                             [self.p3.x,self.p3.y,self.p3.z],
                                             [self.p4.x,self.p4.y,self.p4.z]])
                #self.line.numVertices.setValues([3,3])
                self.line.coordIndex.setValues(0,7,(0,1,2,-1,3,4,5))
            else:
                self.coords.point.setValues([[self.p1.x,self.p1.y,self.p1.z],
                                             [self.p2.x,self.p2.y,self.p2.z],
                                             [self.p3.x,self.p3.y,self.p3.z],
                                             [self.p4.x,self.p4.y,self.p4.z]])
                #self.line.numVertices.setValue(4)
                self.line.coordIndex.setValues(0,4,(0,1,2,3))

    def onChanged(self, vobj, prop):
        """called when a view property has changed"""

        if (prop == "FontSize") and hasattr(vobj,"FontSize"):
            if hasattr(self,"font"):
                self.font.size = vobj.FontSize.Value
            if hasattr(self,"font3d"):
                self.font3d.size = vobj.FontSize.Value*100
            vobj.Object.touch()
        elif (prop == "FontName") and hasattr(vobj,"FontName"):
            if hasattr(self,"font") and hasattr(self,"font3d"):
                self.font.name = self.font3d.name = str(vobj.FontName)
                vobj.Object.touch()
        elif (prop == "LineColor") and hasattr(vobj,"LineColor"):
            if hasattr(self,"color"):
                c = vobj.LineColor
                self.color.rgb.setValue(c[0],c[1],c[2])
        elif (prop == "LineWidth") and hasattr(vobj,"LineWidth"):
            if hasattr(self,"drawstyle"):
                self.drawstyle.lineWidth = vobj.LineWidth
        elif (prop in ["ArrowSize","ArrowType"]) and hasattr(vobj,"ArrowSize"):
            if hasattr(self,"node") and hasattr(self,"p2"):
                from pivy import coin

                if not hasattr(vobj,"ArrowType"):
                    return

                if self.p3.x < self.p2.x:
                    inv = False
                else:
                    inv = True

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
                s1.addChild(dimSymbol(symbol,invert=not(inv)))
                self.marks.addChild(s1)
                s2 = coin.SoSeparator()
                if symbol == "Circle":
                    s2.addChild(self.coord2)
                else:
                    s2.addChild(self.trans2)
                s2.addChild(dimSymbol(symbol,invert=inv))
                self.marks.addChild(s2)
                self.node.insertChild(self.marks,2)
                self.node3d.insertChild(self.marks,2)
                vobj.Object.touch()
        elif (prop == "DimOvershoot") and hasattr(vobj,"DimOvershoot"):
            from pivy import coin

            # set scale
            s = vobj.DimOvershoot.Value
            self.transDimOvershoot1.scaleFactor.setValue((s,s,s))
            self.transDimOvershoot2.scaleFactor.setValue((s,s,s))

            # remove existing nodes
            self.node.removeChild(self.marksDimOvershoot)
            self.node3d.removeChild(self.marksDimOvershoot)

            # set new nodes
            self.marksDimOvershoot = coin.SoSeparator()
            if vobj.DimOvershoot.Value:
                self.marksDimOvershoot.addChild(self.color)
                s1 = coin.SoSeparator()
                s1.addChild(self.transDimOvershoot1)
                s1.addChild(dimDash((-1,0,0),(0,0,0)))
                self.marksDimOvershoot.addChild(s1)
                s2 = coin.SoSeparator()
                s2.addChild(self.transDimOvershoot2)
                s2.addChild(dimDash((0,0,0),(1,0,0)))
                self.marksDimOvershoot.addChild(s2)
            self.node.insertChild(self.marksDimOvershoot,2)
            self.node3d.insertChild(self.marksDimOvershoot,2)
            vobj.Object.touch()
        elif (prop == "ExtOvershoot") and hasattr(vobj,"ExtOvershoot"):
            from pivy import coin

            # set scale
            s = vobj.ExtOvershoot.Value
            self.transExtOvershoot1.scaleFactor.setValue((s,s,s))
            self.transExtOvershoot2.scaleFactor.setValue((s,s,s))

            # remove existing nodes
            self.node.removeChild(self.marksExtOvershoot)
            self.node3d.removeChild(self.marksExtOvershoot)

            # set new nodes
            self.marksExtOvershoot = coin.SoSeparator()
            if vobj.ExtOvershoot.Value:
                self.marksExtOvershoot.addChild(self.color)
                s1 = coin.SoSeparator()
                s1.addChild(self.transExtOvershoot1)
                s1.addChild(dimDash((0,0,0),(-1,0,0)))
                self.marksExtOvershoot.addChild(s1)
                s2 = coin.SoSeparator()
                s2.addChild(self.transExtOvershoot2)
                s2.addChild(dimDash((0,0,0),(-1,0,0)))
                self.marksExtOvershoot.addChild(s2)
            self.node.insertChild(self.marksExtOvershoot,2)
            self.node3d.insertChild(self.marksExtOvershoot,2)
            vobj.Object.touch()
        else:
            self.updateData(vobj.Object,"Start")

    def doubleClicked(self,vobj):
        self.setEdit(vobj)

    def getDisplayModes(self,vobj):
        return ["2D","3D"]

    def getDefaultDisplayMode(self):
        if hasattr(self,"defaultmode"):
            return self.defaultmode
        else:
            return ["2D","3D"][getParam("dimstyle",0)]

    def setDisplayMode(self,mode):
        return mode

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


class Dimension(Creator):
    """The Draft_Dimension FreeCAD command definition"""

    def __init__(self):
        self.max=2
        self.cont = None
        self.dir = None

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Dimension',
                'Accel' : "D, I",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Dimension", "Dimension"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Dimension", "Creates a dimension. CTRL to snap, SHIFT to constrain, ALT to select a segment")}

    def Activated(self):
        name = translate("draft","Dimension")
        if self.cont:
            self.finish()
        elif self.hasMeasures():
            Creator.Activated(self,name)
            self.dimtrack = dimTracker()
            self.arctrack = arcTracker()
            self.createOnMeasures()
            self.finish()
        else:
            Creator.Activated(self,name)
            if self.ui:
                self.ui.pointUi(name)
                self.ui.continueCmd.show()
                self.ui.selectButton.show()
                self.altdown = False
                self.call = self.view.addEventCallback("SoEvent",self.action)
                self.dimtrack = dimTracker()
                self.arctrack = arcTracker()
                self.link = None
                self.edges = []
                self.pts = []
                self.angledata = None
                self.indices = []
                self.center = None
                self.arcmode = False
                self.point2 = None
                self.force = None
                self.info = None
                self.selectmode = False
                self.setFromSelection()
                FreeCAD.Console.PrintMessage(translate("draft", "Pick first point")+"\n")
                FreeCADGui.draftToolBar.show()

    def setFromSelection(self):
        """If we already have selected geometry, fill the nodes accordingly"""
        sel = FreeCADGui.Selection.getSelectionEx()
        import DraftGeomUtils
        if len(sel) == 1:
            if len(sel[0].SubElementNames) == 1:
                if "Edge" in sel[0].SubElementNames[0]:
                    edge = sel[0].SubObjects[0]
                    n = int(sel[0].SubElementNames[0].lstrip("Edge"))-1
                    self.indices.append(n)
                    if DraftGeomUtils.geomType(edge) == "Line":
                        self.node.extend([edge.Vertexes[0].Point,edge.Vertexes[1].Point])
                        v1 = None
                        v2 =None
                        for i,v in enumerate(sel[0].Object.Shape.Vertexes):
                            if v.Point == edge.Vertexes[0].Point:
                                v1 = i
                            if v.Point == edge.Vertexes[1].Point:
                                v2 = i
                        if (v1 != None) and (v2 != None):
                            self.link = [sel[0].Object,v1,v2]
                    elif DraftGeomUtils.geomType(edge) == "Circle":
                        self.node.extend([edge.Curve.Center,edge.Vertexes[0].Point])
                        self.edges = [edge]
                        self.arcmode = "diameter"
                        self.link = [sel[0].Object,n]

    def hasMeasures(self):
        """checks if only measurements objects are selected"""
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            return False
        for o in sel:
            if not o.isDerivedFrom("App::MeasureDistance"):
                return False
        return True

    def finish(self,closed=False):
        """terminates the operation"""
        self.cont = None
        self.dir = None
        Creator.finish(self)
        if self.ui:
            self.dimtrack.finalize()
            self.arctrack.finalize()

    def createOnMeasures(self):
        for o in FreeCADGui.Selection.getSelection():
            p1 = o.P1
            p2 = o.P2
            pt = o.ViewObject.RootNode.getChildren()[1].getChildren()[0].getChildren()[0].getChildren()[3]
            p3 = Vector(pt.point.getValues()[2].getValue())
            FreeCADGui.addModule("Draft")
            self.commit(translate("draft","Create Dimension"),
                        ['dim = Draft.makeDimension('+DraftVecUtils.toString(p1)+','+DraftVecUtils.toString(p2)+','+DraftVecUtils.toString(p3)+')',
                         'FreeCAD.ActiveDocument.removeObject("'+o.Name+'")',
                         'Draft.autogroup(dim)',
                         'FreeCAD.ActiveDocument.recompute()'])

    def createObject(self):
        """creates an object in the current doc"""
        FreeCADGui.addModule("Draft")
        if self.angledata:
            normal = "None"
            if len(self.edges) == 2:
                import DraftGeomUtils
                v1 = DraftGeomUtils.vec(self.edges[0])
                v2 = DraftGeomUtils.vec(self.edges[1])
                normal = DraftVecUtils.toString((v1.cross(v2)).normalize())
            self.commit(translate("draft","Create Dimension"),
                        ['dim = Draft.makeAngularDimension(center='+DraftVecUtils.toString(self.center)+',angles=['+str(self.angledata[0])+','+str(self.angledata[1])+'],p3='+DraftVecUtils.toString(self.node[-1])+',normal='+normal+')',
                        'Draft.autogroup(dim)',
                        'FreeCAD.ActiveDocument.recompute()'])
        elif self.link and (not self.arcmode):
            ops = []
            if self.force == 1:
                self.commit(translate("draft","Create Dimension"),
                        ['dim = Draft.makeDimension(FreeCAD.ActiveDocument.'+self.link[0].Name+','+str(self.link[1])+','+str(self.link[2])+','+DraftVecUtils.toString(self.node[2])+')','dim.Direction=FreeCAD.Vector(0,1,0)',
                        'Draft.autogroup(dim)',
                        'FreeCAD.ActiveDocument.recompute()'])
            elif self.force == 2:
                self.commit(translate("draft","Create Dimension"),
                        ['dim = Draft.makeDimension(FreeCAD.ActiveDocument.'+self.link[0].Name+','+str(self.link[1])+','+str(self.link[2])+','+DraftVecUtils.toString(self.node[2])+')','dim.Direction=FreeCAD.Vector(1,0,0)',
                        'Draft.autogroup(dim)',
                        'FreeCAD.ActiveDocument.recompute()'])
            else:
                self.commit(translate("draft","Create Dimension"),
                        ['dim = Draft.makeDimension(FreeCAD.ActiveDocument.'+self.link[0].Name+','+str(self.link[1])+','+str(self.link[2])+','+DraftVecUtils.toString(self.node[2])+')',
                        'Draft.autogroup(dim)',
                        'FreeCAD.ActiveDocument.recompute()'])
        elif self.arcmode:
            self.commit(translate("draft","Create Dimension"),
                        ['dim = Draft.makeDimension(FreeCAD.ActiveDocument.'+self.link[0].Name+','+str(self.link[1])+',"'+str(self.arcmode)+'",'+DraftVecUtils.toString(self.node[2])+')',
                        'Draft.autogroup(dim)',
                        'FreeCAD.ActiveDocument.recompute()'])
        else:
            self.commit(translate("draft","Create Dimension"),
                        ['dim = Draft.makeDimension('+DraftVecUtils.toString(self.node[0])+','+DraftVecUtils.toString(self.node[1])+','+DraftVecUtils.toString(self.node[2])+')',
                        'Draft.autogroup(dim)',
                        'FreeCAD.ActiveDocument.recompute()'])
        if self.ui.continueMode:
            self.cont = self.node[2]
            if not self.dir:
                if self.link:
                    v1 = self.link[0].Shape.Vertexes[self.link[1]].Point
                    v2 = self.link[0].Shape.Vertexes[self.link[2]].Point
                    self.dir = v2.sub(v1)
                else:
                    self.dir = self.node[1].sub(self.node[0])
            self.node = [self.node[1]]
        self.link = None

    def selectEdge(self):
        self.selectmode = not(self.selectmode)

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            import DraftGeomUtils
            shift = hasMod(arg,MODCONSTRAIN)
            if self.arcmode or self.point2:
                setMod(arg,MODCONSTRAIN,False)
            self.point,ctrlPoint,self.info = getPoint(self,arg,noTracker=(len(self.node)>0))
            if (hasMod(arg,MODALT) or self.selectmode) and (len(self.node)<3):
                self.dimtrack.off()
                if not self.altdown:
                    self.altdown = True
                    self.ui.switchUi(True)
                    if hasattr(FreeCADGui,"Snapper"):
                        FreeCADGui.Snapper.setSelectMode(True)
                snapped = self.view.getObjectInfo((arg["Position"][0],arg["Position"][1]))
                if snapped:
                    ob = self.doc.getObject(snapped['Object'])
                    if "Edge" in snapped['Component']:
                        num = int(snapped['Component'].lstrip('Edge'))-1
                        ed = ob.Shape.Edges[num]
                        v1 = ed.Vertexes[0].Point
                        v2 = ed.Vertexes[-1].Point
                        self.dimtrack.update([v1,v2,self.cont])
            else:
                if self.node and (len(self.edges) < 2):
                    self.dimtrack.on()
                if len(self.edges) == 2:
                    # angular dimension
                    self.dimtrack.off()
                    r = self.point.sub(self.center)
                    self.arctrack.setRadius(r.Length)
                    a = self.arctrack.getAngle(self.point)
                    pair = DraftGeomUtils.getBoundaryAngles(a,self.pts)
                    if not (pair[0] < a < pair[1]):
                        self.angledata = [4*math.pi-pair[0],2*math.pi-pair[1]]
                    else:
                        self.angledata = [2*math.pi-pair[0],2*math.pi-pair[1]]
                    self.arctrack.setStartAngle(self.angledata[0])
                    self.arctrack.setEndAngle(self.angledata[1])
                if self.altdown:
                    self.altdown = False
                    self.ui.switchUi(False)
                    if hasattr(FreeCADGui,"Snapper"):
                        FreeCADGui.Snapper.setSelectMode(False)
                if self.dir:
                    self.point = self.node[0].add(DraftVecUtils.project(self.point.sub(self.node[0]),self.dir))
                if len(self.node) == 2:
                    if self.arcmode and self.edges:
                        cen = self.edges[0].Curve.Center
                        rad = self.edges[0].Curve.Radius
                        baseray = self.point.sub(cen)
                        v2 = DraftVecUtils.scaleTo(baseray,rad)
                        v1 = v2.negative()
                        if shift:
                            self.node = [cen,cen.add(v2)]
                            self.arcmode = "radius"
                        else:
                            self.node = [cen.add(v1),cen.add(v2)]
                            self.arcmode = "diameter"
                        self.dimtrack.update(self.node)
                # Draw constraint tracker line.
                if shift and (not self.arcmode):
                    if len(self.node) == 2:
                        if not self.point2:
                            self.point2 = self.node[1]
                        else:
                            self.node[1] = self.point2
                        if not self.force:
                            a=abs(self.point.sub(self.node[0]).getAngle(plane.u))
                            if (a > math.pi/4) and (a <= 0.75*math.pi):
                                self.force = 1
                            else:
                                self.force = 2
                        if self.force == 1:
                            self.node[1] = Vector(self.node[0].x,self.node[1].y,self.node[0].z)
                        elif self.force == 2:
                            self.node[1] = Vector(self.node[1].x,self.node[0].y,self.node[0].z)
                else:
                    self.force = None
                    if self.point2 and (len(self.node) > 1):
                        self.node[1] = self.point2
                        self.point2 = None
                # update the dimline
                if self.node and (not self.arcmode):
                    self.dimtrack.update(self.node+[self.point]+[self.cont])
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                import DraftGeomUtils
                if self.point:
                    self.ui.redraw()
                    if (not self.node) and (not self.support):
                        getSupport(arg)
                    if (hasMod(arg,MODALT) or self.selectmode) and (len(self.node)<3):
                        #print("snapped: ",self.info)
                        if self.info:
                            ob = self.doc.getObject(self.info['Object'])
                            if 'Edge' in self.info['Component']:
                                num = int(self.info['Component'].lstrip('Edge'))-1
                                ed = ob.Shape.Edges[num]
                                v1 = ed.Vertexes[0].Point
                                v2 = ed.Vertexes[-1].Point
                                i1 = i2 = None
                                for i in range(len(ob.Shape.Vertexes)):
                                    if v1 == ob.Shape.Vertexes[i].Point:
                                        i1 = i
                                    if v2 == ob.Shape.Vertexes[i].Point:
                                        i2 = i
                                if (i1 != None) and (i2 != None):
                                    self.indices.append(num)
                                    if not self.edges:
                                        # nothing snapped yet, we treat it as normal edge-snapped dimension
                                        self.node = [v1,v2]
                                        self.link = [ob,i1,i2]
                                        self.edges.append(ed)
                                        if DraftGeomUtils.geomType(ed) == "Circle":
                                            # snapped edge is an arc
                                            self.arcmode = "diameter"
                                            self.link = [ob,num]
                                    else:
                                        # there is already a snapped edge, so we start angular dimension
                                        self.edges.append(ed)
                                        self.node.extend([v1,v2]) # self.node now has the 4 endpoints
                                        c = DraftGeomUtils.findIntersection(self.node[0],
                                                                   self.node[1],
                                                                   self.node[2],
                                                                   self.node[3],
                                                                   True,True)
                                        if c:
                                            #print("centers:",c)
                                            self.center = c[0]
                                            self.arctrack.setCenter(self.center)
                                            self.arctrack.on()
                                            for e in self.edges:
                                                for v in e.Vertexes:
                                                    self.pts.append(self.arctrack.getAngle(v.Point))
                                            self.link = [self.link[0],ob]
                                        else:
                                            FreeCAD.Console.PrintMessage(translate("draft", "Edges don't intersect!")+"\n")
                                            self.finish()
                                            return
                                self.dimtrack.on()
                    else:
                        self.node.append(self.point)
                    self.selectmode = False
                    #print("node",self.node)
                    self.dimtrack.update(self.node)
                    if (len(self.node) == 2):
                        self.point2 = self.node[1]
                    if (len(self.node) == 1):
                        self.dimtrack.on()
                        if self.planetrack:
                            self.planetrack.set(self.node[0])
                    elif (len(self.node) == 2) and self.cont:
                        self.node.append(self.cont)
                        self.createObject()
                        if not self.cont:
                            self.finish()
                    elif (len(self.node) == 3):
                        # for unlinked arc mode:
                        # if self.arcmode:
                        #        v = self.node[1].sub(self.node[0])
                        #        v.multiply(0.5)
                        #        cen = self.node[0].add(v)
                        #        self.node = [self.node[0],self.node[1],cen]
                        self.createObject()
                        if not self.cont:
                            self.finish()
                    elif self.angledata:
                        self.node.append(self.point)
                        self.createObject()
                        self.finish()

    def numericInput(self,numx,numy,numz):
        """this function gets called by the toolbar when valid x, y, and z have been entered there"""
        self.point = Vector(numx,numy,numz)
        self.node.append(self.point)
        self.dimtrack.update(self.node)
        if (len(self.node) == 1):
            self.dimtrack.on()
        elif (len(self.node) == 3):
            self.createObject()
            if not self.cont:
                self.finish()


class Draft_FlipDimension():
    def GetResources(self):
        return {'Pixmap'  : 'Draft_FlipDimension',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_FlipDimension", "Flip Dimension"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_FlipDimension", "Flip the normal direction of a dimension")}

    def Activated(self):
        for o in FreeCADGui.Selection.getSelection():
            if Draft.getType(o) in ["Dimension","AngularDimension"]:
                FreeCAD.ActiveDocument.openTransaction("Flip dimension")
                FreeCADGui.doCommand("FreeCAD.ActiveDocument."+o.Name+".Normal = FreeCAD.ActiveDocument."+o.Name+".Normal.negative()")
                FreeCAD.ActiveDocument.commitTransaction()
                FreeCAD.ActiveDocument.recompute()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Dimension',Dimension())
    FreeCADGui.addCommand('Draft_FlipDimension',Draft_FlipDimension())

