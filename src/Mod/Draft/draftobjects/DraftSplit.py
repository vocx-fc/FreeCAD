
def split(wire, newPoint, edgeIndex):
    if getType(wire) != "Wire":
        return
    elif wire.Closed:
        splitClosedWire(wire, edgeIndex)
    else:
        splitOpenWire(wire, newPoint, edgeIndex)

def splitClosedWire(wire, edgeIndex):
    wire.Closed = False
    if edgeIndex == len(wire.Points):
        makeWire([wire.Placement.multVec(wire.Points[0]),
            wire.Placement.multVec(wire.Points[-1])], placement=wire.Placement)
    else:
        makeWire([wire.Placement.multVec(wire.Points[edgeIndex-1]),
            wire.Placement.multVec(wire.Points[edgeIndex])], placement=wire.Placement)
        wire.Points = list(reversed(wire.Points[0:edgeIndex])) + list(reversed(wire.Points[edgeIndex:]))

def splitOpenWire(wire, newPoint, edgeIndex):
    wire1Points = []
    wire2Points = []
    for index, point in enumerate(wire.Points):
        if index == edgeIndex:
            wire1Points.append(wire.Placement.inverse().multVec(newPoint))
            wire2Points.append(newPoint)
            wire2Points.append(wire.Placement.multVec(point))
        elif index < edgeIndex:
            wire1Points.append(point)
        elif index > edgeIndex:
            wire2Points.append(wire.Placement.multVec(point))
    wire.Points = wire1Points
    makeWire(wire2Points, placement=wire.Placement)


class Split(Modifier):
    '''The Draft_Split FreeCAD command definition.'''

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Split',
                'Accel' : "S, P",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Split", "Split"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Split", "Splits a wire into two wires")}

    def Activated(self):
        Modifier.Activated(self,"Split")
        if not self.ui:
            return
        FreeCAD.Console.PrintMessage(translate("draft", "Select an object to split")+"\n")
        self.call = self.view.addEventCallback("SoEvent", self.action)

    def action(self, arg):
        "scene event handler"
        if arg["Type"] == "SoKeyboardEvent":
            if arg["Key"] == "ESCAPE":
                self.finish()
        elif arg["Type"] == "SoLocation2Event":
            getPoint(self, arg)
            redraw3DView()
        elif arg["Type"] == "SoMouseButtonEvent" and arg["State"] == "DOWN" and arg["Button"] == "BUTTON1":
            self.point, ctrlPoint, info = getPoint(self, arg)
            if "Edge" in info["Component"]:
                return self.proceed(info)

    def proceed(self, info):
        Draft.split(FreeCAD.ActiveDocument.getObject(info["Object"]),
            self.point, int(info["Component"][4:]))
        if self.call:
            self.view.removeEventCallback("SoEvent", self.call)
        self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Split',Split())

