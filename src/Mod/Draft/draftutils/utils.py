"""This module provides utility functions for the Draft Workbench
"""
## @package utils
# \ingroup  DRAFT
# \brief This module provides utility functions for the Draft Workbench
import FreeCAD
App = FreeCAD

if App.GuiUp:
    # The right translate function needs to be imported here
    # from DraftGui import translate

    # At the moment it is the same function as without GUI
    def translate(context, text):
        return text
else:
    def translate(context, text):
        return text


def _tr(text):
    """Function to translate with the context set."""
    return translate("Draft", text)


def _msg(text, end="\n"):
    App.Console.PrintMessage(text + end)


def _wrn(text, end="\n"):
    App.Console.PrintWarning(text + end)


def _log(text, end="\n"):
    App.Console.PrintLog(text + end)


ARROW_TYPES = ["Dot", "Circle", "Arrow", "Tick", "Tick-2"]
arrowtypes = ARROW_TYPES


def string_encode_coin(ustr):
    """Encode a unicode object to be used as a string in coin

    Parameters
    ----------
    ustr : str
        A string to be encoded

    Returns
    -------
    str
        Encoded string. If the coin version is >= 4
        it will encode the string to `'utf-8'`, otherwise
        it will encode it to `'latin-1'`.
    """
    try:
        from pivy import coin
        coin4 = coin.COIN_MAJOR_VERSION >= 4
    except (ImportError, AttributeError):
        coin4 = False
    if coin4:
        return ustr.encode('utf-8')
    else:
        return ustr.encode('latin1')


stringencodecoin = string_encode_coin


def type_check(args_and_types, name="?"):
    """Check that the arguments are instances of certain types.

    Parameters
    ----------
    args_and_types : list
        A list of tuples. The first element of a tuple is tested as being
        an instance of the second element.
        ::
            args_and_types = [(a, Type), (b, Type2), ...]

        Then
        ::
            isinstance(a, Type)
            isinstance(b, Type2)

        A `Type` can also be a tuple of many types, in which case
        the check is done for any of them.
        ::
            args_and_types = [(a, (Type3, int, float)), ...]

            isinstance(a, (Type3, int, float))

    name : str, optional
        Defaults to `'?'`. The name of the check.

    Raises
    -------
    TypeError
        If the first element in the tuple is not an instance of the second
        element, it raises `Draft.name`.
    """
    for v, t in args_and_types:
        if not isinstance(v, t):
            w = "typecheck[" + str(name) + "]: "
            w += str(v) + " is not " + str(t) + "\n"
            FreeCAD.Console.PrintWarning(w)
            raise TypeError("Draft." + str(name))


typecheck = type_check


def get_param_type(param):
    """Return the type of the parameter entered.

    Parameters
    ----------
    param : str
        A string that indicates a parameter in the parameter database.

    Returns
    -------
    str or None
        The returned string could be `'int'`, `'string'`, `'float'`,
        `'bool'`, `'unsigned'`, depending on the parameter.
        It returns `None` for unhandled situations.
    """
    if param in ("dimsymbol", "dimPrecision", "dimorientation",
                 "precision", "defaultWP", "snapRange", "gridEvery",
                 "linewidth", "UiMode", "modconstrain", "modsnap",
                 "maxSnapEdges", "modalt", "HatchPatternResolution",
                 "snapStyle", "dimstyle", "gridSize"):
        return "int"
    elif param in ("constructiongroupname", "textfont",
                   "patternFile", "template", "snapModes",
                   "FontFile", "ClonePrefix",
                   "labeltype") or "inCommandShortcut" in param:
        return "string"
    elif param in ("textheight", "tolerance", "gridSpacing",
                   "arrowsize", "extlines", "dimspacing",
                   "dimovershoot", "extovershoot"):
        return "float"
    elif param in ("selectBaseObjects", "alwaysSnap", "grid",
                   "fillmode", "saveonexit", "maxSnap",
                   "SvgLinesBlack", "dxfStdSize", "showSnapBar",
                   "hideSnapBar", "alwaysShowGrid", "renderPolylineWidth",
                   "showPlaneTracker", "UsePartPrimitives",
                   "DiscretizeEllipses", "showUnit"):
        return "bool"
    elif param in ("color", "constructioncolor",
                   "snapcolor", "gridColor"):
        return "unsigned"
    else:
        return None


getParamType = get_param_type


def get_param(param, default=None):
    """Return a paramater value from the current parameter database.

    The parameter database is located in the tree
    ::
        'User parameter:BaseApp/Preferences/Mod/Draft'

    In the case that `param` is `'linewidth'` or `'color'` it will get
    the values from the View parameters
    ::
        'User parameter:BaseApp/Preferences/View/DefaultShapeLineWidth'
        'User parameter:BaseApp/Preferences/View/DefaultShapeLineColor'

    Parameters
    ----------
    param : str
        A string that indicates a parameter in the parameter database.

    default : optional
        It indicates the default value of the given parameter.
        It defaults to `None`, in which case it will use a specific
        value depending on the type of parameter determined
        with `get_param_type`.

    Returns
    -------
    int, or str, or float, or bool
        Depending on `param` and its type, by returning `ParameterGrp.GetInt`,
        `ParameterGrp.GetString`, `ParameterGrp.GetFloat`,
        `ParameterGrp.GetBool`, or `ParameterGrp.GetUnsinged`.
    """
    draft_params = "User parameter:BaseApp/Preferences/Mod/Draft"
    view_params = "User parameter:BaseApp/Preferences/View"

    p = FreeCAD.ParamGet(draft_params)
    v = FreeCAD.ParamGet(view_params)
    t = getParamType(param)
    # print("getting param ",param, " of type ",t, " default: ",str(default))
    if t == "int":
        if default is None:
            default = 0
        if param == "linewidth":
            return v.GetInt("DefaultShapeLineWidth", default)
        return p.GetInt(param, default)
    elif t == "string":
        if default is None:
            default = ""
        return p.GetString(param, default)
    elif t == "float":
        if default is None:
            default = 0
        return p.GetFloat(param, default)
    elif t == "bool":
        if default is None:
            default = False
        return p.GetBool(param, default)
    elif t == "unsigned":
        if default is None:
            default = 0
        if param == "color":
            return v.GetUnsigned("DefaultShapeLineColor", default)
        return p.GetUnsigned(param, default)
    else:
        return None


getParam = get_param


def set_param(param, value):
    """Set a Draft parameter with the given value

    The parameter database is located in the tree
    ::
        'User parameter:BaseApp/Preferences/Mod/Draft'

    In the case that `param` is `'linewidth'` or `'color'` it will set
    the View parameters
    ::
        'User parameter:BaseApp/Preferences/View/DefaultShapeLineWidth'
        'User parameter:BaseApp/Preferences/View/DefaultShapeLineColor'

    Parameters
    ----------
    param : str
        A string that indicates a parameter in the parameter database.

    value : int, or str, or float, or bool
        The appropriate value of the parameter.
        Depending on `param` and its type, determined with `get_param_type`,
        it sets the appropriate value by calling `ParameterGrp.SetInt`,
        `ParameterGrp.SetString`, `ParameterGrp.SetFloat`,
        `ParameterGrp.SetBool`, or `ParameterGrp.SetUnsinged`.
    """
    draft_params = "User parameter:BaseApp/Preferences/Mod/Draft"
    view_params = "User parameter:BaseApp/Preferences/View"

    p = FreeCAD.ParamGet(draft_params)
    v = FreeCAD.ParamGet(view_params)
    t = getParamType(param)

    if t == "int":
        if param == "linewidth":
            v.SetInt("DefaultShapeLineWidth", value)
        else:
            p.SetInt(param, value)
    elif t == "string":
        p.SetString(param, value)
    elif t == "float":
        p.SetFloat(param, value)
    elif t == "bool":
        p.SetBool(param, value)
    elif t == "unsigned":
        if param == "color":
            v.SetUnsigned("DefaultShapeLineColor", value)
        else:
            p.SetUnsigned(param, value)


setParam = set_param


def precision():
    """Return the precision value from the paramater database.

    It is the number of decimal places that a float will have.
    Example
    ::
        precision=6, 0.123456
        precision=5, 0.12345
        precision=4, 0.1234

    Due to floating point operations there may be rounding errors.
    Therefore, this precision number is used to round up values
    so that all operations are consistent.
    By default the precision is 6 decimal places.

    Returns
    -------
    int
        get_param("precision", 6)
    """
    return getParam("precision", 6)


def tolerance():
    """Return the tolerance value from the parameter database.

    This specifies a tolerance around a quantity.
    ::
        value + tolerance
        value - tolerance

    By default the tolerance is 0.05.

    Returns
    -------
    float
        get_param("tolerance", 0.05)
    """
    return getParam("tolerance", 0.05)


def epsilon():
    """Return a small number based on the tolerance for use in comparisons.

    The epsilon value is used in floating point comparisons. Use with caution.
    ::
        denom = 10**tolerance
        num = 1
        epsilon = num/denom

    Returns
    -------
    float
        1/(10**tolerance)
    """
    return 1.0/(10.0**tolerance())


def get_real_name(name):
    """Strip the trailing numbers from a string to get only the letters.

    Paramaters
    ----------
    name : str
        A string that may have a number at the end, `Line001`.

    Returns
    -------
    str
        A string without the numbers at the end, `Line`.
        The returned string cannot be empty; it will have
        at least one letter.
    """
    for i in range(1, len(name)):
        if name[-i] not in '1234567890':
            return name[:len(name) - (i-1)]
    return name


getRealName = get_real_name


def get_type(obj):
    """Return a string indicating the type of the given object.

    Paramaters
    ----------
    obj : App::DocumentObject
        Any type of scripted object created with Draft,
        or any other workbench.

    Returns
    -------
    str
        If `obj` has a `Proxy`, it will return the value of `obj.Proxy.Type`.

        * If `obj` is a `Part.Shape`, returns `'Shape'`
        * If `'Sketcher::SketchObject'`, returns `'Sketch'`
        * If `'Part::Line'`, returns `'Part::Line'`
        * If `'Part::Offset2D'`, returns `'Offset2D'`
        * If `'Part::Feature'`, returns `'Part'`
        * If `'App::Annotation'`, returns `'Annotation'`
        * If `'Mesh::Feature'`, returns `'Mesh'`
        * If `'Points::Feature'`, returns `'Points'`
        * If `'App::DocumentObjectGroup'`, returns `'Group'`
        * If `'App::Part'`,  returns `'App::Part'`

        In other cases, it will return `'Unknown'`,
        or `None` if `obj` is `None`.
    """
    import Part
    if not obj:
        return None
    if isinstance(obj, Part.Shape):
        return "Shape"
    if "Proxy" in obj.PropertiesList:
        if hasattr(obj.Proxy, "Type"):
            return obj.Proxy.Type
    if obj.isDerivedFrom("Sketcher::SketchObject"):
        return "Sketch"
    if (obj.TypeId == "Part::Line"):
        return "Part::Line"
    if (obj.TypeId == "Part::Offset2D"):
        return "Offset2D"
    if obj.isDerivedFrom("Part::Feature"):
        return "Part"
    if (obj.TypeId == "App::Annotation"):
        return "Annotation"
    if obj.isDerivedFrom("Mesh::Feature"):
        return "Mesh"
    if obj.isDerivedFrom("Points::Feature"):
        return "Points"
    if (obj.TypeId == "App::DocumentObjectGroup"):
        return "Group"
    if (obj.TypeId == "App::Part"):
        return "App::Part"
    return "Unknown"


getType = get_type


def get_objects_of_type(objects, typ):
    """Return only the objects that match the type in the list of objects.

    Parameters
    ----------
    objects : list of App::DocumentObject
        A list of objects which will be tested.

    typ : str
        A string that indicates a type. This should be one of the types
        that can be returned by `get_type`.

    Returns
    -------
    list of objects
        Only the objects that match `typ` will be added to the output list.
    """
    objs = []
    for o in objects:
        if getType(o) == typ:
            objs.append(o)
    return objs


getObjectsOfType = get_objects_of_type


def is_clone(obj, objtype, recursive=False):
    """Return True if the given object is a clone of a certain type.

    A clone is of type `'Clone'`, and has a reference
    to the original object inside its `Objects` attribute,
    which is an `'App::PropertyLinkListGlobal'`.

    The `Objects` attribute can point to another `'Clone'` object.
    If `recursive` is `True`, the function will be called recursively
    to further test this clone, until the type of the original object
    can be compared to `objtype`.

    Parameters
    ----------
    obj : App::DocumentObject
        The clone object that will be tested for a certain type.

    objtype : str or list of str
        A type string such as one obtained from `get_type`.
        Or a list of such types.

    recursive : bool, optional
        It defaults to `False`.
        If it is `True`, this same function will be called recursively
        with `obj.Object[0]` as input.

        This option only works if `obj.Object[0]` is of type `'Clone'`,
        that is, if `obj` is a clone of a clone.

    Returns
    -------
    bool
        Returns `True` if `obj` is of type `'Clone'`,
        and `obj.Object[0]` is of type `objtype`.

        If `objtype` is a list, then `obj.Objects[0]`
        will be tested against each of the elements in the list,
        and it will return `True` if at least one element matches the type.

        If `obj` isn't of type `'Clone'` but has the `CloneOf` attribute,
        it will also return `True`.

        It returns `False` otherwise, for example,
        if `obj` is not even a clone.
    """
    if isinstance(objtype, list):
        return any([isClone(obj, t, recursive) for t in objtype])

    if getType(obj) == "Clone":
        if len(obj.Objects) == 1:
            if getType(obj.Objects[0]) == objtype:
                return True
            elif recursive and (getType(obj.Objects[0]) == "Clone"):
                return isClone(obj.Objects[0], objtype, recursive)
    elif hasattr(obj, "CloneOf"):
        if obj.CloneOf:
            return True
    return False


isClone = is_clone


def get_group_names():
    """Return a list of names of existing groups in the document.

    Returns
    -------
    list of str
        A list of names of objects that are "groups".
        These are objects derived from `'App::DocumentObjectGroup'`
        or which are of types `'Floor'`, `'Building'`, or `'Site'`
        (from the Arch Workbench).

        Otherwise, return an empty list.
    """
    glist = []
    doc = FreeCAD.ActiveDocument
    for obj in doc.Objects:
        if (obj.isDerivedFrom("App::DocumentObjectGroup")
                or getType(obj) in ("Floor", "Building", "Site")):
            glist.append(obj.Name)
    return glist


getGroupNames = get_group_names


def ungroup(obj):
    """Remove the object from any group to which it belongs.

    A "group" is any object returned by `get_group_names`.

    Parameters
    ----------
    obj : App::DocumentObject
        Any type of scripted object.
    """
    for name in getGroupNames():
        group = FreeCAD.ActiveDocument.getObject(name)
        if obj in group.Group:
            # The list of objects cannot be modified directly,
            # so a new list is created, this new list is modified,
            # and then it is assigned over the older list.
            objects = group.Group
            objects.remove(obj)
            group.Group = objects


def shapify(obj):
    """Transform a parametric object into a static, non-parametric shape.

    Parameters
    ----------
    obj : App::DocumentObject
        Any type of scripted object.

        This object will be removed, and a non-parametric object
        with the same topological shape (`Part::TopoShape`)
        will be created.

    Returns
    -------
    Part::Feature
        The new object that takes `obj.Shape` as its own.

        Depending on the contents of the Shape, the resulting object
        will be named `'Face'`, `'Solid'`, `'Compound'`,
        `'Shell'`, `'Wire'`, `'Line'`, `'Circle'`,
        or the name returned by `get_real_name(obj.Name)`.

        If there is a problem with `obj.Shape`, it will return `None`,
        and the original object will not be modified.
    """
    try:
        shape = obj.Shape
    except Exception:
        return None

    if len(shape.Faces) == 1:
        name = "Face"
    elif len(shape.Solids) == 1:
        name = "Solid"
    elif len(shape.Solids) > 1:
        name = "Compound"
    elif len(shape.Faces) > 1:
        name = "Shell"
    elif len(shape.Wires) == 1:
        name = "Wire"
    elif len(shape.Edges) == 1:
        import DraftGeomUtils
        if DraftGeomUtils.geomType(shape.Edges[0]) == "Line":
            name = "Line"
        else:
            name = "Circle"
    else:
        name = getRealName(obj.Name)

    FreeCAD.ActiveDocument.removeObject(obj.Name)
    newobj = FreeCAD.ActiveDocument.addObject("Part::Feature", name)
    newobj.Shape = shape

    return newobj


def get_group_contents(objectslist,
                       walls=False, addgroups=False,
                       spaces=False, noarchchild=False):
    """Return a list of objects from expanding the input groups.

    The function accepts any type of object, although it is most useful
    with "groups", as it is meant to unpack the objects inside these groups.

    Parameters
    ----------
    objectslist : list
        If any object in the list is a group, its contents (`obj.Group`)
        are extracted and added to the output list.

        The "groups" are objects derived from `'App::DocumentObjectGroup'`,
        but they can also be `'App::Part'`, or `'Building'`, `'BuildingPart'`,
        `'Space'`, and `'Site'` from the Arch Workbench.

        Single items that aren't groups are added to the output list
        as is.

    walls : bool, optional
        It defaults to `False`.
        If it is `True`, Wall and Structure objects (Arch Workbench)
        are treated as groups; they are scanned for Window, Door,
        and Rebar objects, and these are added to the output list.

    addgroups : bool, optional
        It defaults to `False`.
        If it is `True`, the group itself is kept as part of the output list.

    spaces : bool, optional
        It defaults to `False`.
        If it is `True`, Arch Spaces are treated as groups,
        and are added to the output list.

    noarchchild : bool, optional
        It defaults to `False`.
        If it is `True`, the objects inside Building and BuildingParts
        (Arch Workbench) aren't added to the output list.

    Returns
    -------
    list
        The list of objects from each group present in `objectslist`,
        plus any other individual object given in `objectslist`.
    """
    def getWindows(obj):
        l = []
        if getType(obj) in ["Wall", "Structure"]:
            for o in obj.OutList:
                l.extend(getWindows(o))
            for i in obj.InList:
                if (getType(i) in ["Window"]) or isClone(obj, "Window"):
                    if hasattr(i, "Hosts"):
                        if obj in i.Hosts:
                            l.append(i)
                elif (getType(i) in ["Rebar"]) or isClone(obj, "Rebar"):
                    if hasattr(i, "Host"):
                        if obj == i.Host:
                            l.append(i)
        elif (getType(obj) in ["Window", "Rebar"]) or isClone(obj, ["Window", "Rebar"]):
            l.append(obj)
        return l

    newlist = []
    if not isinstance(objectslist, list):
        objectslist = [objectslist]
    for obj in objectslist:
        if obj:
            if (obj.isDerivedFrom("App::DocumentObjectGroup")
                    or ((getType(obj) in ["App::Part",
                                          "Building", "BuildingPart",
                                          "Space", "Site"])
                        and hasattr(obj, "Group"))):
                if getType(obj) == "Site":
                    if obj.Shape:
                        newlist.append(obj)
                if obj.isDerivedFrom("Drawing::FeaturePage"):
                    # skip if the group is a page
                    newlist.append(obj)
                else:
                    if addgroups or (spaces and (getType(obj) == "Space")):
                        newlist.append(obj)
                    if (noarchchild
                            and (getType(obj) in ["Building",
                                                  "BuildingPart"])):
                        pass
                    else:
                        newlist.extend(getGroupContents(obj.Group,
                                                        walls, addgroups))
            else:
                # print("adding ", obj.Name)
                newlist.append(obj)
                if walls:
                    newlist.extend(getWindows(obj))

    # Clean possible duplicates
    cleanlist = []
    for obj in newlist:
        if obj not in cleanlist:
            cleanlist.append(obj)
    return cleanlist


getGroupContents = get_group_contents


def print_shape(shape):
    """Print detailed information of a topological shape.

    Parameters
    ----------
    shape : Part::TopoShape
        Any topological shape in an object, usually obtained from `obj.Shape`.
    """
    _msg(_tr("Solids:") + " {}".format(len(shape.Solids)))
    _msg(_tr("Faces:") + " {}".format(len(shape.Faces)))
    _msg(_tr("Wires:") + " {}".format(len(shape.Wires)))
    _msg(_tr("Edges:") + " {}".format(len(shape.Edges)))
    _msg(_tr("Vertices:") + " {}".format(len(shape.Vertexes)))

    if shape.Faces:
        for f in range(len(shape.Faces)):
            _msg(_tr("Face") + " {}:".format(f))
            for v in shape.Faces[f].Vertexes:
                _msg("    {}".format(v.Point))
    elif shape.Wires:
        for w in range(len(shape.Wires)):
            _msg(_tr("Wire") + " {}:".format(w))
            for v in shape.Wires[w].Vertexes:
                _msg("    {}".format(v.Point))
    else:
        for v in shape.Vertexes:
            _msg("    {}".format(v.Point))


printShape = print_shape


def compare_objects(obj1, obj2):
    """Print the differences between 2 objects.

    The two objects are compared through their `TypeId` attribute,
    or by using the `get_type` function.

    If they are the same type their properties are compared
    looking for differences.

    Neither `Shape` nor `Label` attributes are compared.

    Parameters
    ----------
    obj1 : App::DocumentObject
        Any type of scripted object.
    obj2 : App::DocumentObject
        Any type of scripted object.
    """
    if obj1.TypeId != obj2.TypeId:
        _msg("'{0}' ({1}), '{2}' ({3}): ".format(obj1.Name, obj1.TypeId,
                                                 obj2.Name, obj2.TypeId)
             + _tr("different types") + " (TypeId)")
    elif getType(obj1) != getType(obj2):
        _msg("'{0}' ({1}), '{2}' ({3}): ".format(obj1.Name, get_type(obj1),
                                                 obj2.Name, get_type(obj2))
             + _tr("different types") + " (Proxy.Type)")
    else:
        for p in obj1.PropertiesList:
            if p in obj2.PropertiesList:
                if p in ("Shape", "Label"):
                    pass
                elif p == "Placement":
                    delta = obj1.Placement.Base.sub(obj2.Placement.Base)
                    text = _tr("Objects have different placements. "
                               "Distance between the two base points: ")
                    _msg(text + str(delta.Length))
                else:
                    if getattr(obj1, p) != getattr(obj2, p):
                        _msg("'{}' ".format(p) + _tr("has a different value"))
            else:
                _msg("{} ".format(p)
                     + _tr("doesn't exist in one of the objects"))


compareObjects = compare_objects
