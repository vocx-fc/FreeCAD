

def makeBlock(objectslist):
    """makeBlock(objectslist): Creates a Draft Block from the given objects"""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython","Block")
    _Block(obj)
    obj.Components = objectslist
    if gui:
        _ViewProviderDraftPart(obj.ViewObject)
        for o in objectslist:
            o.ViewObject.Visibility = False
        select(obj)
    return obj


class _Block(_DraftObject):
    """The Block object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"Block")
        obj.addProperty("App::PropertyLinkList","Components","Draft",QT_TRANSLATE_NOOP("App::Property","The components of this block"))

    def execute(self, obj):
        import Part
        plm = obj.Placement
        shps = []
        for c in obj.Components:
            shps.append(c.Shape)
        if shps:
            shape = Part.makeCompound(shps)
            obj.Shape = shape
        obj.Placement = plm
        obj.positionBySupport()


