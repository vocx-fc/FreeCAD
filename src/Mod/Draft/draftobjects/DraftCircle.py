import math
from DraftGui import translate
from FreeCAD import Console as FCC


def _tMsg(context="Workbench", text="message"):
    FreeCAD.Console.PrintMessage(context + ">  " + translate(context, text) + "\n")


def _sMsg(context="Workbench", text="message"):
    FreeCAD.Console.PrintMessage(context + ">  " + text + "\n")


def make_arc3(points, placement=None, face=None, support=None):
    """Return a circular defined by three points in the circumference.

    Parameters
    ----------
    points : list of Base::Vector3d
        A list that must be three points.

    placement : Base::Placement, optional
        It defaults to `None`.
        A placement, comprised of a `Base` (`Base::Vector3`),
        and a `Rotation` (`Base::Rotation`).
        If it exists it moves the center of the arc to the point
        indicated by `placement.Base`, while `placement.Rotation`
        is ignored.

    face : bool, optional
        It defaults to `False`.
        If it is `True` it will create a face in the closed arc.
        Otherwise only the circumference edge will be shown.

    support : optional
        A support object.

    Returns
    -------
    Part::Part2DObject
        The new arc object.
    """
    if not isinstance(points, (list, tuple)):
        _tMsg("Draft", "Wrong input: must be list or tuple")
        return None

    if len(points) != 3:
        _tMsg("Draft", "Wrong input: must be three points")
        return None

    p1, p2, p3 = points
    final_placement = placement

    _edge = Part.Arc(p1, p2, p3)
    edge = _edge.toShape()
    radius = edge.Curve.Radius
    rot = App.Rotation(edge.Curve.XAxis,
                       edge.Curve.YAxis,
                       edge.Curve.Axis, "ZXY")
    placement = App.Placement(edge.Curve.Center, rot)
    start = edge.FirstParameter
    end = math.degrees(edge.LastParameter)
    obj = Draft.makeCircle(radius, placement=placement, face=face,
                           startangle=start, endangle=end,
                           support=support)

    Draft.autogroup(obj)

    _sMsg("Draft", "p1: %s" % p1)
    _sMsg("Draft", "p2: %s" % p2)
    _sMsg("Draft", "p3: %s" % p3)
    _sMsg("Draft", translate("Draft", "center") + ": %s" % edge.Curve.Center)

    if final_placement:
        obj.Placement.Base = final_placement.Base
        _sMsg("Draft", translate("Draft", "placement:") + " %s" % final_placement.Base)

    return obj


def makeCircle(radius, placement=None, face=None, startangle=None, endangle=None, support=None):
    """makeCircle(radius,[placement,face,startangle,endangle])
    or makeCircle(edge,[face]):
    Creates a circle object with given radius. If placement is given, it is
    used. If face is False, the circle is shown as a
    wireframe, otherwise as a face. If startangle AND endangle are given
    (in degrees), they are used and the object appears as an arc. If an edge
    is passed, its Curve must be a Part.Circle"""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    import Part, DraftGeomUtils
    if placement: typecheck([(placement,FreeCAD.Placement)], "makeCircle")
    if startangle != endangle:
        n = "Arc"
    else:
        n = "Circle"
    obj = FreeCAD.ActiveDocument.addObject("Part::Part2DObjectPython",n)
    _Circle(obj)
    if face != None:
        obj.MakeFace = face
    if isinstance(radius,Part.Edge):
        edge = radius
        if DraftGeomUtils.geomType(edge) == "Circle":
            obj.Radius = edge.Curve.Radius
            placement = FreeCAD.Placement(edge.Placement)
            delta = edge.Curve.Center.sub(placement.Base)
            placement.move(delta)
            # Rotation of the edge
            rotOk = FreeCAD.Rotation(edge.Curve.XAxis, edge.Curve.YAxis, edge.Curve.Axis, "ZXY")
            placement.Rotation = rotOk
            if len(edge.Vertexes) > 1:
                v0 = edge.Curve.XAxis
                v1 = (edge.Vertexes[0].Point).sub(edge.Curve.Center)
                v2 = (edge.Vertexes[-1].Point).sub(edge.Curve.Center)
                # Angle between edge.Curve.XAxis and the vector from center to start of arc
                a0 = math.degrees(FreeCAD.Vector.getAngle(v0, v1))
                # Angle between edge.Curve.XAxis and the vector from center to end of arc
                a1 = math.degrees(FreeCAD.Vector.getAngle(v0, v2))
                obj.FirstAngle = a0
                obj.LastAngle = a1
    else:
        obj.Radius = radius
        if (startangle != None) and (endangle != None):
            if startangle == -0: startangle = 0
            obj.FirstAngle = startangle
            obj.LastAngle = endangle
    obj.Support = support
    if placement: obj.Placement = placement
    if gui:
        _ViewProviderDraft(obj.ViewObject)
        formatObject(obj)
        select(obj)

    return obj


class _Circle(_DraftObject):
    """The Circle object"""

    def __init__(self, obj):
        _DraftObject.__init__(self,obj,"Circle")
        obj.addProperty("App::PropertyAngle","FirstAngle","Draft",QT_TRANSLATE_NOOP("App::Property","Start angle of the arc"))
        obj.addProperty("App::PropertyAngle","LastAngle","Draft",QT_TRANSLATE_NOOP("App::Property","End angle of the arc (for a full circle, give it same value as First Angle)"))
        obj.addProperty("App::PropertyLength","Radius","Draft",QT_TRANSLATE_NOOP("App::Property","Radius of the circle"))
        obj.addProperty("App::PropertyBool","MakeFace","Draft",QT_TRANSLATE_NOOP("App::Property","Create a face"))
        obj.addProperty("App::PropertyArea","Area","Draft",QT_TRANSLATE_NOOP("App::Property","The area of this object"))
        obj.MakeFace = getParam("fillmode",True)

    def execute(self, obj):
        import Part
        plm = obj.Placement
        shape = Part.makeCircle(obj.Radius.Value,Vector(0,0,0),Vector(0,0,1),obj.FirstAngle.Value,obj.LastAngle.Value)
        if obj.FirstAngle.Value == obj.LastAngle.Value:
            shape = Part.Wire(shape)
            if hasattr(obj,"MakeFace"):
                if obj.MakeFace:
                    shape = Part.Face(shape)
            else:
                shape = Part.Face(shape)
        obj.Shape = shape
        if hasattr(obj,"Area") and hasattr(shape,"Area"):
            obj.Area = shape.Area
        obj.Placement = plm
        obj.positionBySupport()


class Circle(Arc):
    """The Draft_Circle FreeCAD command definition"""

    def __init__(self):
        self.closedCircle=True
        self.featureName = "Circle"

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Circle',
                'Accel' : "C, I",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Circle", "Circle"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Circle", "Creates a circle. CTRL to snap, ALT to select tangent objects")}


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Circle',Circle())

