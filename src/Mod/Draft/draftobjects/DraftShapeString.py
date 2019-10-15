
def makeShapeString(String,FontFile,Size = 100,Tracking = 0):
    """ShapeString(Text,FontFile,Height,Track): Turns a text string
    into a Compound Shape"""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","ShapeString")
    _ShapeString(obj)
    obj.String = String
    obj.FontFile = FontFile
    obj.Size = Size
    obj.Tracking = Tracking

    if gui:
        _ViewProviderDraft(obj.ViewObject)
        formatObject(obj)
        obrep = obj.ViewObject
        if "PointSize" in obrep.PropertiesList: obrep.PointSize = 1             # hide the segment end points
        select(obj)
    obj.recompute()
    return obj


class _ShapeString(_DraftObject):
    """The ShapeString object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"ShapeString")
        obj.addProperty("App::PropertyString","String","Draft",QT_TRANSLATE_NOOP("App::Property","Text string"))
        obj.addProperty("App::PropertyFile","FontFile","Draft",QT_TRANSLATE_NOOP("App::Property","Font file name"))
        obj.addProperty("App::PropertyLength","Size","Draft",QT_TRANSLATE_NOOP("App::Property","Height of text"))
        obj.addProperty("App::PropertyLength","Tracking","Draft",QT_TRANSLATE_NOOP("App::Property","Inter-character spacing"))

    def execute(self, obj):
        import Part
        # import OpenSCAD2Dgeom
        import os
        if obj.String and obj.FontFile:
            if obj.Placement:
                plm = obj.Placement
            ff8 = obj.FontFile.encode('utf8')                  # 1947 accents in filepath
                                                               # TODO: change for Py3?? bytes?
                                                               # Part.makeWireString uses FontFile as char* string
            if sys.version_info.major < 3:
                CharList = Part.makeWireString(obj.String,ff8,obj.Size,obj.Tracking)
            else:
                CharList = Part.makeWireString(obj.String,obj.FontFile,obj.Size,obj.Tracking)
            if len(CharList) == 0:
                FreeCAD.Console.PrintWarning(translate("draft","ShapeString: string has no wires")+"\n")
                return
            SSChars = []

            # test a simple letter to know if we have a sticky font or not
            sticky = False
            if sys.version_info.major < 3:
                testWire = Part.makeWireString("L",ff8,obj.Size,obj.Tracking)[0][0]
            else:
                testWire = Part.makeWireString("L",obj.FontFile,obj.Size,obj.Tracking)[0][0]
            if testWire.isClosed:
                try:
                    testFace = Part.Face(testWire)
                except Part.OCCError:
                    sticky = True
                else:
                    if not testFace.isValid():
                        sticky = True
            else:
                sticky = True

            for char in CharList:
                if sticky:
                    for CWire in char:
                        SSChars.append(CWire)
                else:
                    CharFaces = []
                    for CWire in char:
                        f = Part.Face(CWire)
                        if f:
                            CharFaces.append(f)
                    # whitespace (ex: ' ') has no faces. This breaks OpenSCAD2Dgeom...
                    if CharFaces:
                        # s = OpenSCAD2Dgeom.Overlappingfaces(CharFaces).makeshape()
                        # s = self.makeGlyph(CharFaces)
                        s = self.makeFaces(char)
                        SSChars.append(s)
            shape = Part.Compound(SSChars)
            obj.Shape = shape
            if plm:
                obj.Placement = plm
        obj.positionBySupport()

    def makeFaces(self, wireChar):
        import Part
        compFaces=[]
        allEdges = []
        wirelist=sorted(wireChar,key=(lambda shape: shape.BoundBox.DiagonalLength),reverse=True)
        fixedwire = []
        for w in wirelist:
            compEdges = Part.Compound(w.Edges)
            compEdges = compEdges.connectEdgesToWires()
            fixedwire.append(compEdges.Wires[0])
        wirelist = fixedwire
        sep_wirelist = []
        while len(wirelist) > 0:
            wire2Face = [wirelist[0]]
            face = Part.Face(wirelist[0])
            for w in wirelist[1:]:
                p = w.Vertexes[0].Point
                u,v = face.Surface.parameter(p)
                if face.isPartOfDomain(u,v):
                    f = Part.Face(w)
                    if face.Orientation == f.Orientation:
                        if f.Surface.Axis * face.Surface.Axis < 0:
                            w.reverse()
                    else:
                        if f.Surface.Axis * face.Surface.Axis > 0:
                            w.reverse()
                    wire2Face.append(w)
                else:
                    sep_wirelist.append(w)
            wirelist = sep_wirelist
            sep_wirelist = []
            face = Part.Face(wire2Face)
            face.validate()
            try:
                # some fonts fail here
                if face.Surface.Axis.z < 0.0:
                    face.reverse()
            except:
                pass
            compFaces.append(face)
        ret = Part.Compound(compFaces)
        return ret

    def makeGlyph(self, facelist):
        ''' turn list of simple contour faces into a compound shape representing a glyph '''
        ''' remove cuts, fuse overlapping contours, retain islands '''
        import Part
        if len(facelist) == 1:
            return(facelist[0])

        sortedfaces = sorted(facelist,key=(lambda shape: shape.Area),reverse=True)

        biggest = sortedfaces[0]
        result = biggest
        islands =[]
        for face in sortedfaces[1:]:
            bcfA = biggest.common(face).Area
            fA = face.Area
            difA = abs(bcfA - fA)
            eps = epsilon()
#            if biggest.common(face).Area == face.Area:
            if difA <= eps:                              # close enough to zero
                # biggest completely overlaps current face ==> cut
                result = result.cut(face)
#            elif biggest.common(face).Area == 0:
            elif bcfA <= eps:
                # island
                islands.append(face)
            else:
                # partial overlap - (font designer error?)
                result = result.fuse(face)
        #glyphfaces = [result]
        wl = result.Wires
        for w in wl:
            w.fixWire()
        glyphfaces = [Part.Face(wl)]
        glyphfaces.extend(islands)
        ret = Part.Compound(glyphfaces)           # should we fuse these instead of making compound?
        return ret


class ShapeString(Creator):
    """This class creates a shapestring feature."""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_ShapeString',
                'Accel' : "S, S",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ShapeString", "Shape from text..."),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_ShapeString", "Creates text string in shapes.")}

    def Activated(self):
        name = translate("draft","ShapeString")
        Creator.Activated(self,name)
        self.creator = Creator
        if self.ui:
            self.ui.sourceCmd = self
            self.taskmode = Draft.getParam("UiMode",1)
            if self.taskmode:
                try:
                    del self.task
                except AttributeError:
                    pass
                self.task = DraftGui.ShapeStringTaskPanel()
                self.task.sourceCmd = self
                DraftGui.todo.delay(FreeCADGui.Control.showDialog,self.task)
            else:
                self.dialog = None
                self.text = ''
                self.ui.sourceCmd = self
                self.ui.pointUi(name)
                self.active = True
                self.call = self.view.addEventCallback("SoEvent",self.action)
                self.ssBase = None
                self.ui.xValue.setFocus()
                self.ui.xValue.selectAll()
                FreeCAD.Console.PrintMessage(translate("draft", "Pick ShapeString location point")+"\n")
                FreeCADGui.draftToolBar.show()

    def createObject(self):
        """creates object in the current doc"""
        #print("debug: D_T ShapeString.createObject type(self.SString): "  str(type(self.SString)))

        dquote = '"'
        if sys.version_info.major < 3: # Python3: no more unicode
            String  = 'u' + dquote + self.SString.encode('unicode_escape') + dquote
        else:
            String  = dquote + self.SString + dquote
        Size = str(self.SSSize)                              # numbers are ascii so this should always work
        Tracking = str(self.SSTrack)                         # numbers are ascii so this should always work
        FFile = dquote + self.FFile + dquote
#        print("debug: D_T ShapeString.createObject type(String): "  str(type(String)))
#        print("debug: D_T ShapeString.createObject type(FFile): "  str(type(FFile)))

        try:
            qr,sup,points,fil = self.getStrings()
            FreeCADGui.addModule("Draft")
            self.commit(translate("draft","Create ShapeString"),
                        ['ss=Draft.makeShapeString(String='+String+',FontFile='+FFile+',Size='+Size+',Tracking='+Tracking+')',
                         'plm=FreeCAD.Placement()',
                         'plm.Base='+DraftVecUtils.toString(self.ssBase),
                         'plm.Rotation.Q='+qr,
                         'ss.Placement=plm',
                         'ss.Support='+sup,
                         'Draft.autogroup(ss)',
                         'FreeCAD.ActiveDocument.recompute()'])
        except Exception as e:
            FreeCAD.Console.PrintError("Draft_ShapeString: error delaying commit\n")
        self.finish()

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            if self.active:
                self.point,ctrlPoint,info = getPoint(self,arg,noTracker=True)
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if not self.ssBase:
                    self.ssBase = self.point
                    self.active = False
                    FreeCADGui.Snapper.off()
                    self.ui.SSUi()

    def numericInput(self,numx,numy,numz):
        '''this function gets called by the toolbar when valid
        x, y, and z have been entered there'''
        self.ssBase = Vector(numx,numy,numz)
        self.ui.SSUi()                   #move on to next step in parameter entry

    def numericSSize(self,ssize):
        '''this function is called by the toolbar when valid size parameter
        has been entered. '''
        self.SSSize = ssize
        self.ui.STrackUi()

    def numericSTrack(self,strack):
        '''this function is called by the toolbar when valid size parameter
        has been entered. ?'''
        self.SSTrack = strack
        self.ui.SFileUi()

    def validSString(self,sstring):
        '''this function is called by the toolbar when a ?valid? string parameter
        has been entered.  '''
        self.SString = sstring
        self.ui.SSizeUi()

    def validFFile(self,FFile):
        '''this function is called by the toolbar when a ?valid? font file parameter
        has been entered. '''
        self.FFile = FFile
        # last step in ShapeString parm capture, create object
        self.createObject()

    def finish(self, finishbool=False):
        """terminates the operation"""
        Creator.finish(self)
        if self.ui:
#            del self.dialog                       # what does this do??
            if self.ui.continueMode:
                self.Activated()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_ShapeString',ShapeString())

