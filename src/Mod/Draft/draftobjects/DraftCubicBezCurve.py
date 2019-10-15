
class CubicBezCurve(Line):
    """a FreeCAD command for creating a 3rd degree Bezier Curve"""

    def __init__(self):
        Line.__init__(self,wiremode=True)
        self.degree = 3

    def GetResources(self):
        return {'Pixmap'  : 'Draft_CubicBezCurve',
                #'Accel' : "B, Z",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_CubicBezCurve", "CubicBezCurve"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_CubicBezCurve", "Creates a Cubic Bezier curve \nClick and drag to define control points. CTRL to snap, SHIFT to constrain")}

    def Activated(self):
        Line.Activated(self,name=translate("draft","CubicBezCurve"))
        if self.doc:
            self.bezcurvetrack = bezcurveTracker()

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            self.point,ctrlPoint,info = getPoint(self,arg,noTracker=True)
            if (len(self.node)-1) % self.degree == 0 and len(self.node) > 2 :
                    prevctrl = 2 * self.node[-1] - self.point
                    self.bezcurvetrack.update(self.node[0:-2] + [prevctrl] + [self.node[-1]] +[self.point],degree=self.degree)                 #existing points + this pointer position
            else:
                self.bezcurvetrack.update(self.node + [self.point],degree=self.degree)                 #existing points + this pointer position
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):       #left click
                if (arg["Position"] == self.pos):                               #double click?
                    if len(self.node) > 2:
                        self.node = self.node[0:-2]
                    else:
                        self.node = []
                    return
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
                            self.node.append(self.point)                            #add point to "clicked list"
                            self.drawUpdate(self.point)
                            # DNC: allows to close the curve
                            # by placing ends close to each other
                            # with tol = Draft tolerance
                            # old code has been to insensitive
                            if ((self.point-self.node[0]).Length < Draft.tolerance()) and len(self.node) >= 4:
                                #self.undolast()
                                self.node=self.node[0:-2]
                                self.node.append(2 * self.node[0] - self.node[1]) #close the curve with a smooth symmetric knot
                                self.finish(True,cont=True)
                                FreeCAD.Console.PrintMessage(translate("draft", "Bezier curve has been closed")+"\n")
            if (arg["State"] == "UP") and (arg["Button"] == "BUTTON1"):       #left click
                if (arg["Position"] == self.pos):                               #double click?
                    self.node = self.node[0:-2]
                    return
                else:
                    if (not self.node) and (not self.support):                  #first point
                        return
                    if self.point:
                        self.ui.redraw()
                        self.pos = arg["Position"]
                        self.node.append(self.point)                            #add point to "clicked list"
                        # sb add a control point, if mod(len(cpoints),2) == 0) then create 2 handle points?
                        self.drawUpdate(self.point)                             #???
                        if (not self.isWire and len(self.node) == 2):
                            self.finish(False,cont=True)
                        if (len(self.node) > 2):                                #does this make sense for a BCurve?
                            self.node[-3] = 2 * self.node[-2] - self.node[-1]
                            self.drawUpdate(self.point)
                            # DNC: allows to close the curve
                            # by placing ends close to each other
                            # with tol = Draft tolerance
                            # old code has been to insensitive

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
            FreeCAD.Console.PrintMessage(translate("draft", "Click and drag to define next knot")+"\n")
        elif (len(self.node)-1) % self.degree == 1 and len(self.node) > 2 : #is a knot
            self.obj.Shape = self.updateShape(self.node[:-1])
            FreeCAD.Console.PrintMessage(translate("draft", "Click and drag to define next knot: ESC to Finish or close (o)")+"\n")

    def updateShape(self, pts):
        '''creates shape for display during creation process.'''
# not quite right. draws 1 big bez.  sb segmented
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
        if closed == False :
            cleannd=(len(self.node)-1) % self.degree
            if cleannd == 0 : self.node = self.node[0:-3]
            if cleannd > 0 : self.node = self.node[0:-cleannd]
        if (len(self.node) > 1):
            try:
                # building command string
                rot,sup,pts,fil = self.getStrings()
                FreeCADGui.addModule("Draft")
                self.commit(translate("draft","Create BezCurve"),
                            ['points = '+pts,
                             'bez = Draft.makeBezCurve(points,closed='+str(closed)+',support='+sup+',Degree='+str(self.degree)+')',
                             'Draft.autogroup(bez)',
                             'FreeCAD.ActiveDocument.recompute()'])
            except:
                print("Draft: error delaying commit")
        Creator.finish(self)
        if self.ui:
            if self.ui.continueMode:
                self.Activated()


class CommandBezierGroup:
    def GetCommands(self):
        return tuple(['Draft_BezCurve','Draft_CubicBezCurve'])
    def GetResources(self):
        return { 'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_BezierTools",'Bezier tools'),
                 'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_BezierTools",'Bezier tools')
               }
    def IsActive(self):
        return not FreeCAD.ActiveDocument is None


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_CubicBezCurve',CubicBezCurve())
    FreeCADGui.addCommand('Draft_BezierTools', CommandBezierGroup())

