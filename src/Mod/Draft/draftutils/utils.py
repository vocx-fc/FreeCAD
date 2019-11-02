"""This module provides utility functions for the Draft Workbench
"""
## @package utils
# \ingroup  DRAFT
# \brief This module provides utility functions for the Draft Workbench
import FreeCAD


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

    In the case that `param` is `'linewidth'` or `'color'` it will use
    the values from the View preferences
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
        Depending on `param` and its type, by calling `FreeCAD.GetInt`,
        `FreeCAD.GetString`, `FreeCAD.GetFloat`, `FreeCAD.GetBool`,
        or `FreeCAD.GetUnsinged`.
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
