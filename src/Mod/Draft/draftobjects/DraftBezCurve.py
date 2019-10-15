
def makeBezCurve(pointslist,closed=False,placement=None,face=None,support=None,Degree=None):
    """makeBezCurve(pointslist,[closed],[placement]): Creates a Bezier Curve object
    from the given list of vectors.   Instead of a pointslist, you can also pass a Part Wire."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if not isinstance(pointslist,list):
        nlist = []
        for v in pointslist.Vertexes:
            nlist.append(v.Point)
        pointslist = nlist
    if placement: typecheck([(placement,FreeCAD.Placement)], "makeBezCurve")
    if len(pointslist) == 2: fname = "Line"
    else: fname = "BezCurve"
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython",fname)
    _BezCurve(obj)
    obj.Points = pointslist
    if Degree:
        obj.Degree = Degree
    else:
        import Part
        obj.Degree = min((len(pointslist)-(1 * (not closed))),\
            Part.BezierCurve().MaxDegree)
    obj.Closed = closed
    obj.Support = support
    if face != None:
        obj.MakeFace = face
    obj.Proxy.resetcontinuity(obj)
    if placement: obj.Placement = placement
    if gui:
        _ViewProviderWire(obj.ViewObject)
#        if not face: obj.ViewObject.DisplayMode = "Wireframe"
#        obj.ViewObject.DisplayMode = "Wireframe"
        formatObject(obj)
        select(obj)

    return obj


class _BezCurve(_DraftObject):
    """The BezCurve object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"BezCurve")
        obj.addProperty("App::PropertyVectorList","Points","Draft",QT_TRANSLATE_NOOP("App::Property","The points of the Bezier curve"))
        obj.addProperty("App::PropertyInteger","Degree","Draft",QT_TRANSLATE_NOOP("App::Property","The degree of the Bezier function"))
        obj.addProperty("App::PropertyIntegerList","Continuity","Draft",QT_TRANSLATE_NOOP("App::Property","Continuity"))
        obj.addProperty("App::PropertyBool","Closed","Draft",QT_TRANSLATE_NOOP("App::Property","If the Bezier curve should be closed or not"))
        obj.addProperty("App::PropertyBool","MakeFace","Draft",QT_TRANSLATE_NOOP("App::Property","Create a face if this curve is closed"))
        obj.addProperty("App::PropertyLength","Length","Draft",QT_TRANSLATE_NOOP("App::Property","The length of this object"))
        obj.addProperty("App::PropertyArea","Area","Draft",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.MakeFace = getParam("fillmode",True)
        obj.Closed = False
        obj.Degree = 3
        obj.Continuity = []
        #obj.setEditorMode("Degree",2)#hide
        obj.setEditorMode("Continuity",1)#ro

    def execute(self, fp):
        self.createGeometry(fp)
        fp.positionBySupport()

    def _segpoleslst(self,fp):
        """split the points into segments"""
        if not fp.Closed and len(fp.Points) >= 2: #allow lower degree segment
            poles=fp.Points[1:]
        elif fp.Closed and len(fp.Points) >= fp.Degree: #drawable
            #poles=fp.Points[1:(fp.Degree*(len(fp.Points)//fp.Degree))]+fp.Points[0:1]
            poles=fp.Points[1:]+fp.Points[0:1]
        else:
            poles=[]
        return [poles[x:x+fp.Degree] for x in \
            range(0, len(poles), (fp.Degree or 1))]

    def resetcontinuity(self,fp):
        fp.Continuity = [0]*(len(self._segpoleslst(fp))-1+1*fp.Closed)
        #nump= len(fp.Points)-1+fp.Closed*1
        #numsegments = (nump // fp.Degree) + 1 * (nump % fp.Degree > 0) -1
        #fp.Continuity = [0]*numsegments

    def onChanged(self, fp, prop):
        if prop == 'Closed': # if remove the last entry when curve gets opened
            oldlen = len(fp.Continuity)
            newlen = (len(self._segpoleslst(fp))-1+1*fp.Closed)
            if oldlen > newlen:
                fp.Continuity = fp.Continuity[:newlen]
            if oldlen < newlen:
                fp.Continuity = fp.Continuity + [0]*(newlen-oldlen)
        if hasattr(fp,'Closed') and fp.Closed and prop in  ['Points','Degree','Closed'] and\
                len(fp.Points) % fp.Degree: # the curve editing tools can't handle extra points
            fp.Points=fp.Points[:(fp.Degree*(len(fp.Points)//fp.Degree))] #for closed curves
        if prop in ["Degree"] and fp.Degree >= 1: #reset Continuity
            self.resetcontinuity(fp)
        if prop in ["Points","Degree","Continuity","Closed"]:
            self.createGeometry(fp)

    def createGeometry(self,fp):
        import Part
        plm = fp.Placement
        if fp.Points:
            startpoint=fp.Points[0]
            edges = []
            for segpoles in self._segpoleslst(fp):
#                if len(segpoles) == fp.Degree # would skip additional poles
                 c = Part.BezierCurve() #last segment may have lower degree
                 c.increase(len(segpoles))
                 c.setPoles([startpoint]+segpoles)
                 edges.append(Part.Edge(c))
                 startpoint = segpoles[-1]
            w = Part.Wire(edges)
            if fp.Closed and w.isClosed():
                try:
                    if hasattr(fp,"MakeFace"):
                        if fp.MakeFace:
                            w = Part.Face(w)
                    else:
                        w = Part.Face(w)
                except Part.OCCError:
                    pass
            fp.Shape = w
            if hasattr(fp,"Area") and hasattr(w,"Area"):
                fp.Area = w.Area
            if hasattr(fp,"Length") and hasattr(w,"Length"):
                fp.Length = w.Length            
        fp.Placement = plm

    @classmethod
    def symmetricpoles(cls,knot, p1, p2):
        """make two poles symmetric respective to the knot"""
        p1h=FreeCAD.Vector(p1)
        p2h=FreeCAD.Vector(p2)
        p1h.multiply(0.5)
        p2h.multiply(0.5)
        return ( knot+p1h-p2h , knot+p2h-p1h)

    @classmethod
    def tangentpoles(cls,knot, p1, p2,allowsameside=False):
        """make two poles have the same tangent at knot"""
        p12n=p2.sub(p1)
        p12n.normalize()
        p1k=knot-p1
        p2k=knot-p2
        p1k_= FreeCAD.Vector(p12n)
        kon12=(p1k*p12n)
        if allowsameside or not (kon12 < 0 or p2k*p12n > 0):# instead of moving
            p1k_.multiply(kon12)
            pk_k=knot-p1-p1k_
            return (p1+pk_k,p2+pk_k)
        else:
            return cls.symmetricpoles(knot, p1, p2)

    @staticmethod
    def modifysymmetricpole(knot,p1):
        """calculate the coordinates of the opposite pole
        of a symmetric knot"""
        return knot+knot-p1

    @staticmethod
    def modifytangentpole(knot,p1,oldp2):
        """calculate the coordinates of the opposite pole
        of a tangent knot"""
        pn=knot-p1
        pn.normalize()
        pn.multiply((knot-oldp2).Length)
        return pn+knot

# for compatibility with older versions ???????
_ViewProviderBezCurve = _ViewProviderWire


class BezCurve(Line):
    """a FreeCAD command for creating a Bezier Curve"""

    def __init__(self):
        Line.__init__(self,wiremode=True)
        self.degree = None

    def GetResources(self):
        return {'Pixmap'  : 'Draft_BezCurve',
                'Accel' : "B, Z",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_BezCurve", "BezCurve"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_BezCurve", "Creates a Bezier curve. CTRL to snap, SHIFT to constrain")}

    def Activated(self):
        Line.Activated(self,name=translate("draft","BezCurve"))
        if self.doc:
            self.bezcurvetrack = bezcurveTracker()

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            self.point,ctrlPoint,info = getPoint(self,arg,noTracker=True)
            self.bezcurvetrack.update(self.node + [self.point],degree=self.degree)                 #existing points + this pointer position
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):       #left click
                if (arg["Position"] == self.pos):                               #double click?
                    self.finish(False,cont=True)
                else:
                    if (not self.node) and (not self.support):                  #first point
                        getSupport(arg)
                        self.point,ctrlPoint,info = getPoint(self,arg,noTracker=True)
                    if self.point:
                        self.ui.redraw()
                        self.pos = arg["Position"]
                        self.node.append(self.point)                            #add point to "clicked list"
                        # sb add a control point, if mod(len(cpoints),2) == 0) then create 2 handle points?
                        self.drawUpdate(self.point)                             #???
                        if (not self.isWire and len(self.node) == 2):
                            self.finish(False,cont=True)
                        if (len(self.node) > 2):                                #does this make sense for a BCurve?
                            # DNC: allows to close the curve
                            # by placing ends close to each other
                            # with tol = Draft tolerance
                            # old code has been to insensitive
                            if ((self.point-self.node[0]).Length < Draft.tolerance()):
                                self.undolast()
                                self.finish(True,cont=True)
                                FreeCAD.Console.PrintMessage(translate("draft", "Bezier curve has been closed")+"\n")

    def undolast(self):
        """undoes last line segment"""
        if (len(self.node) > 1):
            self.node.pop()
            self.bezcurvetrack.update(self.node,degree=self.degree)
            self.obj.Shape = self.updateShape(self.node)
            FreeCAD.Console.PrintMessage(translate("draft", "Last point has been removed")+"\n")

    def drawUpdate(self,point):
        if (len(self.node) == 1):
            self.bezcurvetrack.on()
            if self.planetrack:
                self.planetrack.set(self.node[0])
            FreeCAD.Console.PrintMessage(translate("draft", "Pick next point")+"\n")
        else:
            self.obj.Shape = self.updateShape(self.node)
            FreeCAD.Console.PrintMessage(translate("draft", "Pick next point, or Finish (shift-F) or close (o)")+"\n")

    def updateShape(self, pts):
        '''creates shape for display during creation process.'''
        edges = []
        if len(pts) >= 2: #allow lower degree segment
            poles=pts[1:]
        else:
            poles=[]
        if self.degree:
            segpoleslst = [poles[x:x+self.degree] for x in range(0, len(poles), (self.degree or 1))]
        else:
            segpoleslst = [pts]
        startpoint=pts[0]
        for segpoles in segpoleslst:
            c = Part.BezierCurve() #last segment may have lower degree
            c.increase(len(segpoles))
            c.setPoles([startpoint]+segpoles)
            edges.append(Part.Edge(c))
            startpoint = segpoles[-1]
        w = Part.Wire(edges)
        return(w)

    def finish(self,closed=False,cont=False):
        """terminates the operation and closes the poly if asked"""
        if self.ui:
            if hasattr(self,"bezcurvetrack"):
                self.bezcurvetrack.finalize()
        if not Draft.getParam("UiMode",1):
            FreeCADGui.Control.closeDialog()
        if self.obj:
            # remove temporary object, if any
            old = self.obj.Name
            todo.delay(self.doc.removeObject,old)
        if (len(self.node) > 1):
            try:
                # building command string
                rot,sup,pts,fil = self.getStrings()
                FreeCADGui.addModule("Draft")
                self.commit(translate("draft","Create BezCurve"),
                            ['points = '+pts,
                             'bez = Draft.makeBezCurve(points,closed='+str(closed)+',support='+sup+',Degree='+str(self.degree)+')',
                             'Draft.autogroup(bez)'])
            except:
                print("Draft: error delaying commit")
        Creator.finish(self)
        if self.ui:
            if self.ui.continueMode:
                self.Activated()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_BezCurve', BezCurve())

