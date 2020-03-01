"""Produce a NotchConnector."""
import FreeCAD as App
import Part
from FreeCAD import Vector
import draftutils.gui_utils as gui_utils
import draftutils.utils

if App.GuiUp:
    import draftviewproviders.view_notch as view_notch

epsilon = draftutils.utils.epsilon()


class NotchConnectorWorker:
    """Notch connector object"""
    def __init__(self, fp, # FeaturePython
                 Base,
                 Tools,
                 CutDirection=Vector(0,0,0),
                 CutDepth=50.0):
        fp.addProperty("App::PropertyLink", "Base", "NotchConnector", "Object to cut").Base = Base
        fp.addProperty("App::PropertyLinkList", "Tools", "NotchConnector", "Object to cut").Tools = Tools
        fp.addProperty("App::PropertyVector", "CutDirection", "NotchConnector",  "The direction of the cut").CutDirection = CutDirection
        fp.addProperty("App::PropertyFloat", "CutDepth", "NotchConnector",  "Length of the cut in percent").CutDepth = CutDepth
        fp.Proxy = self

    def onChanged(self, fp, prop):
        proplist = ["Base", "Tools", "CutDirection"]
        if prop in proplist:
            self.execute(fp)

        if prop == "CutDepth" and fp.CutDirection != Vector(0.0, 0.0, 0.0):
            cdep = 100 - abs(fp.CutDepth)
            fp.CutDirection = fp.CutDirection.normalize() * cdep / 50.0
            self.execute(fp)

    def execute(self, fp):
        if not fp.Base or not fp.Tools:
            return

        fp.Proxy = None
        if fp.CutDirection == Vector(0.0, 0.0, 0.0):
            bbox = self.extractCompounds([fp.Base])[0].Shape.BoundBox
            v = Vector(1, 1, 1)
            if bbox.XLength < bbox.YLength and bbox.XLength < bbox.ZLength:
                v.x = 0
            elif bbox.YLength <= bbox.XLength and bbox.YLength < bbox.ZLength:
                v.y = 0
            else:
                v.z = 0
            bbox = self.extractCompounds(fp.Tools)[0].Shape.BoundBox
            if bbox.XLength < bbox.YLength and bbox.XLength < bbox.ZLength:
                v.x = 0
            elif bbox.YLength <= bbox.XLength and bbox.YLength < bbox.ZLength:
                v.y = 0
            else:
                v.z = 0
            fp.CutDirection = v * fp.CutDepth / 50.0
        fp.Proxy = self
        self.cutNotches(fp)

    def extractCompounds(self, obj):
        extracted = []
        for o in obj:
            if hasattr(o, 'Links'):
                extracted += self.extractCompounds(o.Links)
            else:
                extracted.append(o)
        return extracted

    def extractShapes(self, lobj):
        shapes = []
        for obj in lobj:
            if len(obj.Shape.Solids) > 0:
                shapes += obj.Shape.Solids
            else:
                shapes += obj.Shape.Faces
        return shapes

    def cutNotches(self, fp):
        shapes = []
        halfsize = fp.CutDirection / 2.0
        for obj in self.extractCompounds([fp.Base]):
            isExtrude = hasattr(obj, "LengthFwd") and hasattr(obj, "Base")
            if isExtrude:
                bShapes = obj.Base
            else:
                bShapes = obj

            for bShape in self.extractShapes([bShapes]):
                cutcubes = []
                for tool in self.extractShapes(fp.Tools):
                    tbox = tool.BoundBox
                    common = tool.common(bShape)
                    cbox = common.BoundBox
                    if cbox.XLength + cbox.YLength + cbox.ZLength > epsilon:
                        vSize = Vector(cbox.XLength, cbox.YLength, cbox.ZLength)
                        vPlace = Vector(cbox.XMin, cbox.YMin, cbox.ZMin)
                        if vSize.x < epsilon or vSize.x > tbox.XLength: 
                            vSize.x = tbox.XLength
                            vPlace.x = tbox.XMin
                        if vSize.y < epsilon or vSize.y > tbox.YLength: 
                            vSize.y = tbox.YLength
                            vPlace.y = tbox.YMin
                        if vSize.z < epsilon or vSize.z > tbox.ZLength: 
                            vSize.z = tbox.ZLength   
                            vPlace.z = tbox.ZMin

                        cutcube = Part.makeBox(vSize.x, vSize.y, vSize.z)
                        cutcube.Placement.Base = vPlace
                        cutcube.Placement.Base.x += cbox.XLength * halfsize.x
                        cutcube.Placement.Base.y += cbox.YLength * halfsize.y
                        cutcube.Placement.Base.z += cbox.ZLength * halfsize.z
                        cutcubes.append(cutcube)

                if len(cutcubes) > 0:
                    cutted = bShape.cut(cutcubes)
                else:
                    cutted = bShape

                if isExtrude:
                    cutted.Placement.Base -= obj.Dir * float(obj.LengthRev)
                    ext = cutted.extrude(obj.Dir * float(obj.LengthFwd + obj.LengthRev))
                    shapes.append(ext)
                else:
                    shapes.append(cutted)

        if len(shapes) == 1:
            fp.Shape = shapes[0]
        elif len(shapes) > 1:
            fp.Shape = Part.makeCompound(shapes)


def make_notch_connector(base, tools,
                         cut_direction=Vector(0, 0, 0),
                         cut_depth=50.0):
    """Produce a NotchConnector."""
    obj = App.ActiveDocument.addObject("Part::FeaturePython",
                                       "NotchConnector")
    NotchConnectorWorker(obj, base, tools, cut_direction, cut_depth)
    if App.GuiUp:
        view_notch.NotchConnectorViewProvider(obj.ViewObject)
        gui_utils.select(obj)
    return obj
