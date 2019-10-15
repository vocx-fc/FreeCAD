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

