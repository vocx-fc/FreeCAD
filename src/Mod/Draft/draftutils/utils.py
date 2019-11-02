"""This module provides utility functions for the Draft Workbench
"""
## @package utils
# \ingroup  DRAFT
# \brief This module provides utility functions for the Draft Workbench
import FreeCAD


arrow_types = ["Dot", "Circle", "Arrow", "Tick", "Tick-2"]


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
