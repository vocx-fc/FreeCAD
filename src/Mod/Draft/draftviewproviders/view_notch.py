"""View provider for the NotchConnector."""
import Draft_rc

True if Draft_rc.__name__ else False


class NotchConnectorViewProvider:
    """View provider for the notch object."""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object

    def getIcon(self):
        return ":/icons/Draft_Draft"

    def attach(self, vobj):
        self.Object = vobj.Object
        self.onChanged(vobj, "Base")

    def claimChildren(self):
        childs = [self.Object.Base] + self.Object.Tools
        for c in childs:
            c.ViewObject.hide()
        return childs

    def onDelete(self, feature, subelements):
        return True

    def onChanged(self, fp, prop):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
