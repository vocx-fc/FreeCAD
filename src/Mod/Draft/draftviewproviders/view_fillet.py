"""This module provides the view provider code for Draft Fillet.
"""
## @package view_fillet
# \ingroup DRAFT
# \brief This module provides the view provider code for Draft Fillet.

# ***************************************************************************
# *   Copyright (c) 2019 Eliud Cabrera Castillo <e.cabrera-castillo@tum.de> *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

import Draft
import Draft_rc
ViewProviderWire = Draft._ViewProviderWire

# So the resource file doesn't trigger errors from code checkers (flake8)
True if Draft_rc.__name__ else False


class ViewProviderFillet(ViewProviderWire):
    """View provider for the Draft Fillet object"""
    def __init__(self, vobj):
        super().__init__(vobj)
