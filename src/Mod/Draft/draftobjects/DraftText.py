
def makeText(stringslist,point=Vector(0,0,0),screen=False):
    """makeText(strings,[point],[screen]): Creates a Text object at the given point,
    containing the strings given in the strings list, one string by line (strings
    can also be one single string). The current color and text height and font
    specified in preferences are used.
    If screen is True, the text always faces the view direction."""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    typecheck([(point,Vector)], "makeText")
    if not isinstance(stringslist,list): stringslist = [stringslist]
    obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython","Text")
    DraftText(obj)
    obj.Text = stringslist
    obj.Placement.Base = point
    if FreeCAD.GuiUp:
        ViewProviderDraftText(obj.ViewObject)
        if screen:
            obj.ViewObject.DisplayMode = "3D text"
        h = getParam("textheight",0.20)
        if screen:
            h = h*10
        obj.ViewObject.FontSize = h
        obj.ViewObject.FontName = getParam("textfont","")
        obj.ViewObject.LineSpacing = 1
        formatObject(obj)
        select(obj)
    return obj


class DraftText:
    """The Draft Text object"""

    def __init__(self,obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyPlacement","Placement","Base",QT_TRANSLATE_NOOP("App::Property","The placement of this object"))
        obj.addProperty("App::PropertyStringList","Text","Base",QT_TRANSLATE_NOOP("App::Property","The text displayed by this object"))
        self.Type = "DraftText"

    def execute(self,obj):
        pass


class ViewProviderDraftText:
    """A View Provider for the Draft Label"""

    def __init__(self,vobj):
        vobj.addProperty("App::PropertyLength","FontSize","Base",QT_TRANSLATE_NOOP("App::Property","The size of the text"))
        vobj.addProperty("App::PropertyFont","FontName","Base",QT_TRANSLATE_NOOP("App::Property","The font of the text"))
        vobj.addProperty("App::PropertyEnumeration","Justification","Base",QT_TRANSLATE_NOOP("App::Property","The vertical alignment of the text"))
        vobj.addProperty("App::PropertyColor","TextColor","Base",QT_TRANSLATE_NOOP("App::Property","Text color"))
        vobj.addProperty("App::PropertyFloat","LineSpacing","Base",QT_TRANSLATE_NOOP("App::Property","Line spacing (relative to font size)"))
        vobj.Proxy = self
        self.Object = vobj.Object
        vobj.Justification = ["Left","Center","Right"]
        vobj.FontName = getParam("textfont","sans")
        vobj.FontSize = getParam("textheight",1)

    def getIcon(self):
        import Draft_rc
        return ":/icons/Draft_Text.svg"

    def claimChildren(self):
        return []

    def attach(self,vobj):
        from pivy import coin
        self.mattext = coin.SoMaterial()
        textdrawstyle = coin.SoDrawStyle()
        textdrawstyle.style = coin.SoDrawStyle.FILLED
        self.trans = coin.SoTransform()
        self.font = coin.SoFont()
        self.text2d = coin.SoAsciiText()
        self.text3d = coin.SoText2()
        self.text2d.string = self.text3d.string = "Label" # need to init with something, otherwise, crash!
        self.text2d.justification = coin.SoAsciiText.LEFT
        self.text3d.justification = coin.SoText2.LEFT
        self.node2d = coin.SoGroup()
        self.node2d.addChild(self.trans)
        self.node2d.addChild(self.mattext)
        self.node2d.addChild(textdrawstyle)
        self.node2d.addChild(self.font)
        self.node2d.addChild(self.text2d)
        self.node3d = coin.SoGroup()
        self.node3d.addChild(self.trans)
        self.node3d.addChild(self.mattext)
        self.node3d.addChild(textdrawstyle)
        self.node3d.addChild(self.font)
        self.node3d.addChild(self.text3d)
        vobj.addDisplayMode(self.node2d,"2D text")
        vobj.addDisplayMode(self.node3d,"3D text")
        self.onChanged(vobj,"TextColor")
        self.onChanged(vobj,"FontSize")
        self.onChanged(vobj,"FontName")
        self.onChanged(vobj,"Justification")
        self.onChanged(vobj,"LineSpacing")

    def getDisplayModes(self,vobj):
        return ["2D text","3D text"]

    def setDisplayMode(self,mode):
        return mode

    def updateData(self,obj,prop):
        if prop == "Text":
            if obj.Text:
                if sys.version_info.major >= 3:
                    self.text2d.string.setValues([l for l in obj.Text if l])
                    self.text3d.string.setValues([l for l in obj.Text if l])
                else:
                    self.text2d.string.setValues([l.encode("utf8") for l in obj.Text if l])
                    self.text3d.string.setValues([l.encode("utf8") for l in obj.Text if l])
        elif prop == "Placement":
            self.trans.translation.setValue(obj.Placement.Base)
            self.trans.rotation.setValue(obj.Placement.Rotation.Q)

    def onChanged(self,vobj,prop):
        if prop == "TextColor":
            if "TextColor" in vobj.PropertiesList:
                l = vobj.TextColor
                self.mattext.diffuseColor.setValue([l[0],l[1],l[2]])
        elif (prop == "FontName"):
            if "FontName" in vobj.PropertiesList:
                self.font.name = vobj.FontName.encode("utf8")
        elif prop  == "FontSize":
            if "FontSize" in vobj.PropertiesList:
                self.font.size = vobj.FontSize.Value
        elif prop == "Justification":
            from pivy import coin
            try:
                if getattr(vobj, "Justification", None) is not None:
                    if vobj.Justification == "Left":
                        self.text2d.justification = coin.SoAsciiText.LEFT
                        self.text3d.justification = coin.SoText2.LEFT
                    elif vobj.Justification == "Right":
                        self.text2d.justification = coin.SoAsciiText.RIGHT
                        self.text3d.justification = coin.SoText2.RIGHT
                    else:
                        self.text2d.justification = coin.SoAsciiText.CENTER
                        self.text3d.justification = coin.SoText2.CENTER
            except AssertionError:
                pass # Race condition - Justification enum has not been set yet
        elif prop == "LineSpacing":
            if "LineSpacing" in vobj.PropertiesList:
                self.text2d.spacing = vobj.LineSpacing
                self.text3d.spacing = vobj.LineSpacing

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None


class Text(Creator):
    """This class creates an annotation feature."""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Text',
                'Accel' : "T, E",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Text", "Text"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Text", "Creates an annotation. CTRL to snap")}

    def Activated(self):
        name = translate("draft","Text")
        Creator.Activated(self,name)
        if self.ui:
            self.dialog = None
            self.text = ''
            self.ui.sourceCmd = self
            self.ui.pointUi(name)
            self.call = self.view.addEventCallback("SoEvent",self.action)
            self.active = True
            self.ui.xValue.setFocus()
            self.ui.xValue.selectAll()
            FreeCAD.Console.PrintMessage(translate("draft", "Pick location point")+"\n")
            FreeCADGui.draftToolBar.show()

    def finish(self,closed=False,cont=False):
        """terminates the operation"""
        Creator.finish(self)
        if self.ui:
            del self.dialog
            if self.ui.continueMode:
                self.Activated()

    def createObject(self):
        """creates an object in the current doc"""
        tx = '['
        for l in self.text:
            if len(tx) > 1:
                tx += ','
            if sys.version_info.major < 3:
                l = unicode(l)
                tx += '"'+str(l.encode("utf8"))+'"'
            else:
                tx += '"'+l+'"' #Python3 no more unicode
        tx += ']'
        FreeCADGui.addModule("Draft")
        self.commit(translate("draft","Create Text"),
                    ['text = Draft.makeText('+tx+',point='+DraftVecUtils.toString(self.node[0])+')',
                    'Draft.autogroup(text)',
                    'FreeCAD.ActiveDocument.recompute()'])
        FreeCAD.ActiveDocument.recompute()

        self.finish(cont=True)

    def action(self,arg):
        """scene event handler"""
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event": #mouse movement detection
            if self.active:
                self.point,ctrlPoint,info = getPoint(self,arg)
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent":
            if (arg["State"] == "DOWN") and (arg["Button"] == "BUTTON1"):
                if self.point:
                    self.active = False
                    FreeCADGui.Snapper.off()
                    self.node.append(self.point)
                    self.ui.textUi()
                    self.ui.textValue.setFocus()

    def numericInput(self,numx,numy,numz):
        '''this function gets called by the toolbar when valid
        x, y, and z have been entered there'''
        self.point = Vector(numx,numy,numz)
        self.node.append(self.point)
        self.ui.textUi()
        self.ui.textValue.setFocus()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Text',Text())

