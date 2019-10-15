def joinTwoWires(wire1, wire2):
    """joinTwoWires(object, object): joins two wires if they share a common
    point as a start or an end"""
    wire1AbsPoints = [wire1.Placement.multVec(point) for point in wire1.Points]
    wire2AbsPoints = [wire2.Placement.multVec(point) for point in wire2.Points]
    if (wire1AbsPoints[0] == wire2AbsPoints[-1] and wire1AbsPoints[-1] == wire2AbsPoints[0]) \
        or (wire1AbsPoints[0] == wire2AbsPoints[0] and wire1AbsPoints[-1] == wire2AbsPoints[-1]):
        wire2AbsPoints.pop()
        wire1.Closed = True
    elif wire1AbsPoints[0] == wire2AbsPoints[0]:
        wire1AbsPoints = list(reversed(wire1AbsPoints))
    elif wire1AbsPoints[0] == wire2AbsPoints[-1]:
        wire1AbsPoints = list(reversed(wire1AbsPoints))
        wire2AbsPoints = list(reversed(wire2AbsPoints))
    elif wire1AbsPoints[-1] == wire2AbsPoints[-1]:
        wire2AbsPoints = list(reversed(wire2AbsPoints))
    elif wire1AbsPoints[-1] == wire2AbsPoints[0]:
        pass
    else:
        return False
    wire2AbsPoints.pop(0)
    wire1.Points = [wire1.Placement.inverse().multVec(point) for point in wire1AbsPoints] + [wire1.Placement.inverse().multVec(point) for point in wire2AbsPoints]
    FreeCAD.ActiveDocument.removeObject(wire2.Name)
    return True


def joinWires(wires, joinAttempts = 0):
    """joinWires(objects): merges a set of wires where possible, if any of those
    wires have a coincident start and end point"""
    if joinAttempts > len(wires):
        return
    joinAttempts += 1
    for wire1Index, wire1 in enumerate(wires):
        for wire2Index, wire2 in enumerate(wires):
            if wire2Index <= wire1Index:
                continue
            if joinTwoWires(wire1, wire2):
                wires.pop(wire2Index)
                break
    joinWires(wires, joinAttempts)


class Join(Modifier):
    '''The Draft_Join FreeCAD command definition.'''

    def GetResources(self):
        return {'Pixmap'  : 'Draft_Join',
                'Accel' : "J, O",
                'MenuText': QtCore.QT_TRANSLATE_NOOP("Draft_Join", "Join"),
                'ToolTip': QtCore.QT_TRANSLATE_NOOP("Draft_Join", "Joins two wires together")}

    def Activated(self):
        Modifier.Activated(self,"Join")
        if not self.ui:
            return
        if not FreeCADGui.Selection.getSelection():
            self.ui.selectUi()
            FreeCAD.Console.PrintMessage(translate("draft", "Select an object to join")+"\n")
            self.call = self.view.addEventCallback("SoEvent",selectObject)
        else:
            self.proceed()

    def proceed(self):
        if self.call:
            self.view.removeEventCallback("SoEvent",self.call)
        if FreeCADGui.Selection.getSelection():
            print(FreeCADGui.Selection.getSelection())
            FreeCADGui.addModule("Draft")
            self.commit(translate("draft","Join"),
                ['Draft.joinWires(FreeCADGui.Selection.getSelection())', 'FreeCAD.ActiveDocument.recompute()'])
        self.finish()


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Draft_Join',Join())

