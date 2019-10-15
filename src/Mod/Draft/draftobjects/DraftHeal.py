
def heal(objlist=None,delete=True,reparent=True):
    """heal([objlist],[delete],[reparent]) - recreates Draft objects that are damaged,
    for example if created from an earlier version. If delete is True,
    the damaged objects are deleted (default). If ran without arguments, all the objects
    in the document will be healed if they are damaged. If reparent is True (default),
    new objects go at the very same place in the tree than their original."""

    auto = False

    if not objlist:
        objlist = FreeCAD.ActiveDocument.Objects
        print("Automatic mode: Healing whole document...")
        auto = True
    else:
        print("Manual mode: Force-healing selected objects...")

    if not isinstance(objlist,list):
        objlist = [objlist]

    dellist = []
    got = False

    for obj in objlist:
        dtype = getType(obj)
        ftype = obj.TypeId
        if ftype in ["Part::FeaturePython","App::FeaturePython","Part::Part2DObjectPython","Drawing::FeatureViewPython"]:
            proxy = obj.Proxy
            if hasattr(obj,"ViewObject"):
                if hasattr(obj.ViewObject,"Proxy"):
                    proxy = obj.ViewObject.Proxy
            if (proxy == 1) or (dtype in ["Unknown","Part"]) or (not auto):
                got = True
                dellist.append(obj.Name)
                props = obj.PropertiesList
                if ("Dimline" in props) and ("Start" in props):
                    print("Healing " + obj.Name + " of type Dimension")
                    nobj = makeCopy(obj,force="Dimension",reparent=reparent)
                elif ("Height" in props) and ("Length" in props):
                    print("Healing " + obj.Name + " of type Rectangle")
                    nobj = makeCopy(obj,force="Rectangle",reparent=reparent)
                elif ("Points" in props) and ("Closed" in props):
                    if "BSpline" in obj.Name:
                        print("Healing " + obj.Name + " of type BSpline")
                        nobj = makeCopy(obj,force="BSpline",reparent=reparent)
                    else:
                        print("Healing " + obj.Name + " of type Wire")
                        nobj = makeCopy(obj,force="Wire",reparent=reparent)
                elif ("Radius" in props) and ("FirstAngle" in props):
                    print("Healing " + obj.Name + " of type Circle")
                    nobj = makeCopy(obj,force="Circle",reparent=reparent)
                elif ("DrawMode" in props) and ("FacesNumber" in props):
                    print("Healing " + obj.Name + " of type Polygon")
                    nobj = makeCopy(obj,force="Polygon",reparent=reparent)
                elif ("FillStyle" in props) and ("FontSize" in props):
                    nobj = makeCopy(obj,force="DrawingView",reparent=reparent)
                else:
                    dellist.pop()
                    print("Object " + obj.Name + " is not healable")

    if not got:
        print("No object seems to need healing")
    else:
        print("Healed ",len(dellist)," objects")

    if dellist and delete:
        for n in dellist:
            FreeCAD.ActiveDocument.removeObject(n)


class Heal():
    """The Draft Heal command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Heal',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Heal", "Heal"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Heal", "Heal faulty Draft objects saved from an earlier FreeCAD version")}

    def Activated(self):
        s = FreeCADGui.Selection.getSelection()
        FreeCAD.ActiveDocument.openTransaction("Heal")
        if s:
            Draft.heal(s)
        else:
            Draft.heal()
        FreeCAD.ActiveDocument.commitTransaction()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Heal',Heal())

