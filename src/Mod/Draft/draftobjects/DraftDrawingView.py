
def makeDrawingView(obj,page,lwmod=None,tmod=None,otherProjection=None):
    """
    makeDrawingView(object,page,[lwmod,tmod]) - adds a View of the given object to the
    given page. lwmod modifies lineweights (in percent), tmod modifies text heights
    (in percent). The Hint scale, X and Y of the page are used.
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if getType(obj) == "SectionPlane":
        import ArchSectionPlane
        viewobj = FreeCAD.ActiveDocument.addObject("Drawing::FeatureViewPython","View")
        page.addObject(viewobj)
        ArchSectionPlane._ArchDrawingView(viewobj)
        viewobj.Source = obj
        viewobj.Label = "View of "+obj.Name
    elif getType(obj) == "Panel":
        import ArchPanel
        viewobj = ArchPanel.makePanelView(obj,page)
    else:
        viewobj = FreeCAD.ActiveDocument.addObject("Drawing::FeatureViewPython","View"+obj.Name)
        _DrawingView(viewobj)
        page.addObject(viewobj)
        if (otherProjection):
            if hasattr(otherProjection,"Scale"):
                viewobj.Scale = otherProjection.Scale
            if hasattr(otherProjection,"X"):
                viewobj.X = otherProjection.X
            if hasattr(otherProjection,"Y"):
                viewobj.Y = otherProjection.Y
            if hasattr(otherProjection,"Rotation"):
                viewobj.Rotation = otherProjection.Rotation
            if hasattr(otherProjection,"Direction"):
                viewobj.Direction = otherProjection.Direction
        else:
            if hasattr(page.ViewObject,"HintScale"):
                viewobj.Scale = page.ViewObject.HintScale
            if hasattr(page.ViewObject,"HintOffsetX"):
                viewobj.X = page.ViewObject.HintOffsetX
            if hasattr(page.ViewObject,"HintOffsetY"):
                viewobj.Y = page.ViewObject.HintOffsetY
        viewobj.Source = obj
        if lwmod: viewobj.LineweightModifier = lwmod
        if tmod: viewobj.TextModifier = tmod
        if hasattr(obj.ViewObject,"Pattern"):
            if str(obj.ViewObject.Pattern) in list(svgpatterns().keys()):
                viewobj.FillStyle = str(obj.ViewObject.Pattern)
        if hasattr(obj.ViewObject,"DrawStyle"):
            viewobj.LineStyle = obj.ViewObject.DrawStyle
        if hasattr(obj.ViewObject,"LineColor"):
            viewobj.LineColor = obj.ViewObject.LineColor
        elif hasattr(obj.ViewObject,"TextColor"):
            viewobj.LineColor = obj.ViewObject.TextColor
    return viewobj


class _DrawingView(_DraftObject):
    """The Draft DrawingView object"""
    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"DrawingView")
        obj.addProperty("App::PropertyVector","Direction","Shape View",QT_TRANSLATE_NOOP("App::Property","Projection direction"))
        obj.addProperty("App::PropertyFloat","LineWidth","View Style",QT_TRANSLATE_NOOP("App::Property","The width of the lines inside this object"))
        obj.addProperty("App::PropertyLength","FontSize","View Style",QT_TRANSLATE_NOOP("App::Property","The size of the texts inside this object"))
        obj.addProperty("App::PropertyLength","LineSpacing","View Style",QT_TRANSLATE_NOOP("App::Property","The spacing between lines of text"))
        obj.addProperty("App::PropertyColor","LineColor","View Style",QT_TRANSLATE_NOOP("App::Property","The color of the projected objects"))
        obj.addProperty("App::PropertyLink","Source","Base",QT_TRANSLATE_NOOP("App::Property","The linked object"))
        obj.addProperty("App::PropertyEnumeration","FillStyle","View Style",QT_TRANSLATE_NOOP("App::Property","Shape Fill Style"))
        obj.addProperty("App::PropertyEnumeration","LineStyle","View Style",QT_TRANSLATE_NOOP("App::Property","Line Style"))
        obj.addProperty("App::PropertyBool","AlwaysOn","View Style",QT_TRANSLATE_NOOP("App::Property","If checked, source objects are displayed regardless of being visible in the 3D model"))
        obj.FillStyle = ['shape color'] + list(svgpatterns().keys())
        obj.LineStyle = ['Solid','Dashed','Dotted','Dashdot']
        obj.LineWidth = 0.35
        obj.FontSize = 12

    def execute(self, obj):
        result = ""
        if hasattr(obj,"Source"):
            if obj.Source:
                if hasattr(obj,"LineStyle"):
                    ls = obj.LineStyle
                else:
                    ls = None
                if hasattr(obj,"LineColor"):
                    lc = obj.LineColor
                else:
                    lc = None
                if hasattr(obj,"LineSpacing"):
                    lp = obj.LineSpacing
                else:
                    lp = None
                if obj.Source.isDerivedFrom("App::DocumentObjectGroup"):
                    svg = ""
                    shapes = []
                    others = []
                    objs = getGroupContents([obj.Source])
                    for o in objs:
                        v = o.ViewObject.isVisible()
                        if hasattr(obj,"AlwaysOn"):
                            if obj.AlwaysOn:
                                v = True
                        if v:
                            svg += getSVG(o,obj.Scale,obj.LineWidth,obj.FontSize.Value,obj.FillStyle,obj.Direction,ls,lc,lp)
                else:
                    svg = getSVG(obj.Source,obj.Scale,obj.LineWidth,obj.FontSize.Value,obj.FillStyle,obj.Direction,ls,lc,lp)
                result += '<g id="' + obj.Name + '"'
                result += ' transform="'
                result += 'rotate('+str(obj.Rotation)+','+str(obj.X)+','+str(obj.Y)+') '
                result += 'translate('+str(obj.X)+','+str(obj.Y)+') '
                result += 'scale('+str(obj.Scale)+','+str(-obj.Scale)+')'
                result += '">'
                result += svg
                result += '</g>'
        obj.ViewResult = result

    def getDXF(self,obj):
        "returns a DXF fragment"
        return getDXF(obj)


class Drawing(Modifier):
    """The Draft Drawing command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Drawing',
                'Accel' : "D, D",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Drawing", "Drawing"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Drawing", "Puts the selected objects on a Drawing sheet")}

    def Activated(self):
        Modifier.Activated(self,"Drawing")
        if not FreeCADGui.Selection.getSelection():
            self.ghost = None
            self.ui.selectUi()
            FreeCAD.Console.PrintMessage(translate("draft", "Select an object to project")+"\n")
            self.call = self.view.addEventCallback("SoEvent",selectObject)
        else:
            self.proceed()

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            self.page = self.createDefaultPage()
        else:
            self.page = None
            # if the user selected a page, put the objects on that page
            for obj in sel:
                if obj.isDerivedFrom("Drawing::FeaturePage"):
                    self.page = obj
                    break
            if not self.page:
                # no page selected, default to the first page in the document
                for obj in self.doc.Objects:
                    if obj.isDerivedFrom("Drawing::FeaturePage"):
                        self.page = obj
                        break
            if not self.page:
                # no page in the document, create a default page.
                self.page = self.createDefaultPage()
            otherProjection = None
            # if an existing projection is selected, reuse its projection properties
            for obj in sel:
                if obj.isDerivedFrom("Drawing::FeatureView"):
                    otherProjection = obj
                    break
            sel.reverse()
            for obj in sel:
                if ( obj.ViewObject.isVisible() and not obj.isDerivedFrom("Drawing::FeatureView")
                        and not obj.isDerivedFrom("Drawing::FeaturePage") ):
                    name = 'View'+obj.Name
                    # no reason to remove the old one...
                    #oldobj = self.page.getObject(name)
                    #if oldobj:
                    #    self.doc.removeObject(oldobj.Name)
                    Draft.makeDrawingView(obj,self.page,otherProjection=otherProjection)
            self.doc.recompute()

    def createDefaultPage(self):
        """created a default page"""
        template = Draft.getParam("template",FreeCAD.getResourceDir()+'Mod/Drawing/Templates/A3_Landscape.svg')
        page = self.doc.addObject('Drawing::FeaturePage','Page')
        page.ViewObject.HintOffsetX = 200
        page.ViewObject.HintOffsetY = 100
        page.ViewObject.HintScale = 20
        page.Template = template
        self.doc.recompute()
        return page


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Drawing',Drawing())

