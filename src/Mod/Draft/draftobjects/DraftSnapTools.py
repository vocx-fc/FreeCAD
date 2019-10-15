class Draft_Snap_Lock():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Lock',
                'Accel' : "Shift+S",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Lock", "Toggle On/Off"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Lock", "Activates/deactivates all snap tools at once")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"masterbutton"):
                FreeCADGui.Snapper.masterbutton.toggle()


class Draft_Snap_Midpoint():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Midpoint',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Midpoint", "Midpoint"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Midpoint", "Snaps to midpoints of edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonmidpoint":
                        b.toggle()


class Draft_Snap_Perpendicular():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Perpendicular',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Perpendicular", "Perpendicular"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Perpendicular", "Snaps to perpendicular points on edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonperpendicular":
                        b.toggle()


class Draft_Snap_Grid():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Grid',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Grid", "Grid"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Grid", "Snaps to grid points")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtongrid":
                        b.toggle()


class Draft_Snap_Intersection():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Intersection',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Intersection", "Intersection"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Intersection", "Snaps to edges intersections")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonintersection":
                        b.toggle()


class Draft_Snap_Parallel():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Parallel',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Parallel", "Parallel"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Parallel", "Snaps to parallel directions of edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonparallel":
                        b.toggle()


class Draft_Snap_Endpoint():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Endpoint',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Endpoint", "Endpoint"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Endpoint", "Snaps to endpoints of edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonendpoint":
                        b.toggle()


class Draft_Snap_Angle():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Angle',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Angle", "Angles"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Angle", "Snaps to 45 and 90 degrees points on arcs and circles")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonangle":
                        b.toggle()


class Draft_Snap_Center():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Center',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Center", "Center"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Center", "Snaps to center of circles and arcs")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtoncenter":
                        b.toggle()


class Draft_Snap_Extension():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Extension',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Extension", "Extension"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Extension", "Snaps to extension of edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonextension":
                        b.toggle()


class Draft_Snap_Near():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Near',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Near", "Nearest"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Near", "Snaps to nearest point on edges")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonpassive":
                        b.toggle()


class Draft_Snap_Ortho():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Ortho',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Ortho", "Ortho"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Ortho", "Snaps to orthogonal and 45 degrees directions")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonortho":
                        b.toggle()


class Draft_Snap_Special():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Special',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Special", "Special"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Special", "Snaps to special locations of objects")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonspecial":
                        b.toggle()


class Draft_Snap_Dimensions():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_Dimensions',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Dimensions", "Dimensions"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_Dimensions", "Shows temporary dimensions when snapping to Arch objects")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonDimensions":
                        b.toggle()


class Draft_Snap_WorkingPlane():
    def GetResources(self):
        return {'Pixmap'  : 'Snap_WorkingPlane',
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Snap_WorkingPlane", "Working Plane"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_Snap_WorkingPlane", "Restricts the snapped point to the current working plane")}
    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            if hasattr(FreeCADGui.Snapper,"toolbarButtons"):
                for b in FreeCADGui.Snapper.toolbarButtons:
                    if b.objectName() == "SnapButtonWorkingPlane":
                        b.toggle()


class ShowSnapBar():
    """The ShowSnapBar FreeCAD command definition"""

    def GetResources(self):
        return {'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ShowSnapBar", "Show Snap Bar"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_ShowSnapBar", "Shows Draft snap toolbar")}

    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.show()


class ToggleGrid():
    """The Draft ToggleGrid command definition"""

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Grid',
                'Accel' : "G,R",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_ToggleGrid", "Toggle Grid"),
                'ToolTip' : QtCore.QT_TRANSLATE_NOOP("Draft_ToggleGrid", "Toggles the Draft grid on/off")}

    def Activated(self):
        if hasattr(FreeCADGui,"Snapper"):
            FreeCADGui.Snapper.setTrackers()
            if FreeCADGui.Snapper.grid:
                if FreeCADGui.Snapper.grid.Visible:
                    FreeCADGui.Snapper.grid.off()
                    FreeCADGui.Snapper.forceGridOff=True
                else:
                    FreeCADGui.Snapper.grid.on()
                    FreeCADGui.Snapper.forceGridOff=False


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_ShowSnapBar',ShowSnapBar())
    FreeCADGui.addCommand('Draft_ToggleGrid',ToggleGrid())
    FreeCADGui.addCommand('Draft_Snap_Lock',Draft_Snap_Lock())
    FreeCADGui.addCommand('Draft_Snap_Midpoint',Draft_Snap_Midpoint())
    FreeCADGui.addCommand('Draft_Snap_Perpendicular',Draft_Snap_Perpendicular())
    FreeCADGui.addCommand('Draft_Snap_Grid',Draft_Snap_Grid())
    FreeCADGui.addCommand('Draft_Snap_Intersection',Draft_Snap_Intersection())
    FreeCADGui.addCommand('Draft_Snap_Parallel',Draft_Snap_Parallel())
    FreeCADGui.addCommand('Draft_Snap_Endpoint',Draft_Snap_Endpoint())
    FreeCADGui.addCommand('Draft_Snap_Angle',Draft_Snap_Angle())
    FreeCADGui.addCommand('Draft_Snap_Center',Draft_Snap_Center())
    FreeCADGui.addCommand('Draft_Snap_Extension',Draft_Snap_Extension())
    FreeCADGui.addCommand('Draft_Snap_Near',Draft_Snap_Near())
    FreeCADGui.addCommand('Draft_Snap_Ortho',Draft_Snap_Ortho())
    FreeCADGui.addCommand('Draft_Snap_Special',Draft_Snap_Special())
    FreeCADGui.addCommand('Draft_Snap_Dimensions',Draft_Snap_Dimensions())
    FreeCADGui.addCommand('Draft_Snap_WorkingPlane',Draft_Snap_WorkingPlane())

