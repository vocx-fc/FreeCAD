class _DraftLink(_DraftObject):

    def __init__(self,obj,tp):
        self.useLink = False if obj else True
        _DraftObject.__init__(self,obj,tp)
        if obj:
            self.attach(obj)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self,state):
        if isinstance(state,dict):
            self.__dict__ = state
        else:
            self.useLink = False
            _DraftObject.__setstate__(self,state)

    def attach(self,obj):
        if self.useLink:
            obj.addExtension('App::LinkExtensionPython', None)
            self.linkSetup(obj)

    def linkSetup(self,obj):
        obj.configLinkProperty('Placement',LinkedObject='Base')
        if hasattr(obj,'ShowElement'):
            # rename 'ShowElement' property to 'ExpandArray' to avoid conflict
            # with native App::Link
            obj.configLinkProperty('ShowElement')
            showElement = obj.ShowElement
            obj.addProperty("App::PropertyBool","ExpandArray","Draft",
                    QT_TRANSLATE_NOOP("App::Property","Show array element as children object"))
            obj.ExpandArray = showElement
            obj.configLinkProperty(ShowElement='ExpandArray')
            obj.removeProperty('ShowElement')
        else:
            obj.configLinkProperty(ShowElement='ExpandArray')
        if getattr(obj,'ExpandArray',False):
            obj.setPropertyStatus('PlacementList','Immutable')
        else:
            obj.setPropertyStatus('PlacementList','-Immutable')

    def getViewProviderName(self,_obj):
        if self.useLink:
            return 'Gui::ViewProviderLinkPython'
        return ''

    def onDocumentRestored(self, obj):
        if self.useLink:
            self.linkSetup(obj)
            if obj.Shape.isNull():
                self.buildShape(obj,obj.Placement,obj.PlacementList)

    def buildShape(self,obj,pl,pls):
        import Part
        import DraftGeomUtils

        if self.useLink:
            if not getattr(obj,'ExpandArray',True) or obj.Count != len(pls):
                obj.setPropertyStatus('PlacementList','-Immutable')
                obj.PlacementList = pls
                obj.setPropertyStatus('PlacementList','Immutable')
                obj.Count = len(pls)

        if obj.Base:
            shape = Part.getShape(obj.Base)
            if shape.isNull():
                raise RuntimeError("'{}' cannot build shape of '{}'\n".format(
                        obj.Name,obj.Base.Name))
            else:
                shape = shape.copy()
                shape.Placement = FreeCAD.Placement()
                base = []
                for i,pla in enumerate(pls):
                    vis = getattr(obj,'VisibilityList',[])
                    if len(vis)>i and not vis[i]:
                        continue;
                    # 'I' is a prefix for disambiguation when mapping element names
                    base.append(shape.transformed(pla.toMatrix(),op='I{}'.format(i)))
                if getattr(obj,'Fuse',False) and len(base) > 1:
                    obj.Shape = base[0].multiFuse(base[1:]).removeSplitter()
                else:
                    obj.Shape = Part.makeCompound(base)

                if not DraftGeomUtils.isNull(pl):
                    obj.Placement = pl

        if self.useLink:
            return False # return False to call LinkExtension::execute()

    def onChanged(self, obj, prop):
        if getattr(obj,'useLink',False):
            return
        elif prop == 'Fuse':
            if obj.Fuse:
                obj.setPropertyStatus('Shape','-Transient')
            else:
                obj.setPropertyStatus('Shape','Transient')
        elif prop == 'ExpandArray':
            if hasattr(obj,'PlacementList'):
                obj.setPropertyStatus('PlacementList',
                        '-Immutable' if obj.ExpandArray else 'Immutable')


class _ViewProviderDraftLink:
    "a view provider for link type object"

    def __init__(self,vobj):
        self.Object = vobj.Object
        vobj.Proxy = self

    def attach(self,vobj):
        self.Object = vobj.Object

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def getIcon(self):
        tp = self.Object.Proxy.Type
        if tp == 'Array':
            return ":/icons/Draft_LinkArray.svg"
        elif tp == 'PathArray':
            return ":/icons/Draft_PathLinkArray.svg"

    def claimChildren(self):
        obj = self.Object
        if hasattr(obj,'ExpandArray'):
            expand = obj.ExpandArray
        else:
            expand = obj.ShowElement
        if not expand:
            return [obj.Base]
        else:
            return obj.ElementList

