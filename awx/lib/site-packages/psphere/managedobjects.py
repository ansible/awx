from psphere import ManagedObject, cached_property

class ExtensibleManagedObject(ManagedObject):
    _valid_attrs = set(['availableField', 'value'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def availableField(self):
       return self._get_dataobject("availableField", True)
    @cached_property
    def value(self):
       return self._get_dataobject("value", True)


class Alarm(ExtensibleManagedObject):
    _valid_attrs = set(['info'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)


class AlarmManager(ManagedObject):
    _valid_attrs = set(['defaultExpression', 'description'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def defaultExpression(self):
       return self._get_dataobject("defaultExpression", True)
    @cached_property
    def description(self):
       return self._get_dataobject("description", False)


class AuthorizationManager(ManagedObject):
    _valid_attrs = set(['description', 'privilegeList', 'roleList'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def description(self):
       return self._get_dataobject("description", False)
    @cached_property
    def privilegeList(self):
       return self._get_dataobject("privilegeList", True)
    @cached_property
    def roleList(self):
       return self._get_dataobject("roleList", True)


class ManagedEntity(ExtensibleManagedObject):
    _valid_attrs = set(['alarmActionsEnabled', 'configIssue', 'configStatus', 'customValue', 'declaredAlarmState', 'disabledMethod', 'effectiveRole', 'name', 'overallStatus', 'parent', 'permission', 'recentTask', 'tag', 'triggeredAlarmState'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def alarmActionsEnabled(self):
       return self._get_dataobject("alarmActionsEnabled", False)
    @cached_property
    def configIssue(self):
       return self._get_dataobject("configIssue", True)
    @cached_property
    def configStatus(self):
       return self._get_dataobject("configStatus", False)
    @cached_property
    def customValue(self):
       return self._get_dataobject("customValue", True)
    @cached_property
    def declaredAlarmState(self):
       return self._get_dataobject("declaredAlarmState", True)
    @cached_property
    def disabledMethod(self):
       return self._get_dataobject("disabledMethod", True)
    @cached_property
    def effectiveRole(self):
       return self._get_dataobject("effectiveRole", True)
    @cached_property
    def name(self):
       return self._get_dataobject("name", False)
    @cached_property
    def overallStatus(self):
       return self._get_dataobject("overallStatus", False)
    @cached_property
    def parent(self):
       return self._get_mor("parent", False)
    @cached_property
    def permission(self):
       return self._get_dataobject("permission", True)
    @cached_property
    def recentTask(self):
       return self._get_mor("recentTask", True)
    @cached_property
    def tag(self):
       return self._get_dataobject("tag", True)
    @cached_property
    def triggeredAlarmState(self):
       return self._get_dataobject("triggeredAlarmState", True)

    @classmethod
    def all(cls, client, properties=None):
        if properties is None:
            properties = []

        if "name" not in properties:
            properties.append("name")

        return client.find_entity_views(cls.__name__, properties=properties)
    
    @classmethod
    def get(cls, client, **kwargs):
        if "properties" in kwargs.keys():
            properties = kwargs["properties"]
            # Delete properties key so it doesn't get filtered
            del kwargs["properties"]
        else:
            properties = None

        if properties is None:
            properties = []

        # Automatically get the name property for every ManagedEntity
        if "name" not in properties:
            properties.append("name")

        filter = {}
        for key in kwargs.keys():
            filter[key] = kwargs[key]

        return client.find_entity_view(cls.__name__,
                                       filter=filter,
                                       properties=properties)

    def __cmp__(self, other):
       if self.name == other.name:
           return 0
       if self.name < other.name:
           return -1
       if self.name > other.name:
           return 1

#    def __str__(self):
#        return self.name


class ComputeResource(ManagedEntity):
    _valid_attrs = set(['configurationEx', 'datastore', 'environmentBrowser', 'host', 'network', 'resourcePool', 'summary'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def configurationEx(self):
       return self._get_dataobject("configurationEx", False)
    @cached_property
    def datastore(self):
       return self._get_mor("datastore", True)
    @cached_property
    def environmentBrowser(self):
       return self._get_mor("environmentBrowser", False)
    @cached_property
    def host(self):
       return self._get_mor("host", True)
    @cached_property
    def network(self):
       return self._get_mor("network", True)
    @cached_property
    def resourcePool(self):
       return self._get_mor("resourcePool", False)
    @cached_property
    def summary(self):
       return self._get_dataobject("summary", False)


class ClusterComputeResource(ComputeResource):
    _valid_attrs = set(['actionHistory', 'configuration', 'drsFault', 'drsRecommendation', 'migrationHistory', 'recommendation'])
    def __init__(self, mo_ref, client):
        ComputeResource.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ComputeResource._valid_attrs)
    @cached_property
    def actionHistory(self):
       return self._get_dataobject("actionHistory", True)
    @cached_property
    def configuration(self):
       return self._get_dataobject("configuration", False)
    @cached_property
    def drsFault(self):
       return self._get_dataobject("drsFault", True)
    @cached_property
    def drsRecommendation(self):
       return self._get_dataobject("drsRecommendation", True)
    @cached_property
    def migrationHistory(self):
       return self._get_dataobject("migrationHistory", True)
    @cached_property
    def recommendation(self):
       return self._get_dataobject("recommendation", True)


class Profile(ManagedObject):
    _valid_attrs = set(['complianceStatus', 'config', 'createdTime', 'description', 'entity', 'modifiedTime', 'name'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def complianceStatus(self):
       return self._get_dataobject("complianceStatus", False)
    @cached_property
    def config(self):
       return self._get_dataobject("config", False)
    @cached_property
    def createdTime(self):
       return self._get_dataobject("createdTime", False)
    @cached_property
    def description(self):
       return self._get_dataobject("description", False)
    @cached_property
    def entity(self):
       return self._get_mor("entity", True)
    @cached_property
    def modifiedTime(self):
       return self._get_dataobject("modifiedTime", False)
    @cached_property
    def name(self):
       return self._get_dataobject("name", False)


class ClusterProfile(Profile):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        Profile.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, Profile._valid_attrs)


class ProfileManager(ManagedObject):
    _valid_attrs = set(['profile'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def profile(self):
       return self._get_mor("profile", True)


class ClusterProfileManager(ProfileManager):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ProfileManager.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ProfileManager._valid_attrs)


class View(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class ManagedObjectView(View):
    _valid_attrs = set(['view'])
    def __init__(self, mo_ref, client):
        View.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, View._valid_attrs)
    @cached_property
    def view(self):
       return self._get_mor("view", True)


class ContainerView(ManagedObjectView):
    _valid_attrs = set(['container', 'recursive', 'type'])
    def __init__(self, mo_ref, client):
        ManagedObjectView.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObjectView._valid_attrs)
    @cached_property
    def container(self):
       return self._get_mor("container", False)
    @cached_property
    def recursive(self):
       return self._get_dataobject("recursive", False)
    @cached_property
    def type(self):
       return self._get_dataobject("type", True)


class CustomFieldsManager(ManagedObject):
    _valid_attrs = set(['field'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def field(self):
       return self._get_dataobject("field", True)


class CustomizationSpecManager(ManagedObject):
    _valid_attrs = set(['encryptionKey', 'info'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def encryptionKey(self):
       return self._get_dataobject("encryptionKey", True)
    @cached_property
    def info(self):
       return self._get_dataobject("info", True)


class Datacenter(ManagedEntity):
    _valid_attrs = set(['datastore', 'datastoreFolder', 'hostFolder', 'network', 'networkFolder', 'vmFolder'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def datastore(self):
       return self._get_mor("datastore", True)
    @cached_property
    def datastoreFolder(self):
       return self._get_mor("datastoreFolder", False)
    @cached_property
    def hostFolder(self):
       return self._get_mor("hostFolder", False)
    @cached_property
    def network(self):
       return self._get_mor("network", True)
    @cached_property
    def networkFolder(self):
       return self._get_mor("networkFolder", False)
    @cached_property
    def vmFolder(self):
       return self._get_mor("vmFolder", False)


class Datastore(ManagedEntity):
    _valid_attrs = set(['browser', 'capability', 'host', 'info', 'iormConfiguration', 'summary', 'vm'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def browser(self):
       return self._get_mor("browser", False)
    @cached_property
    def capability(self):
       return self._get_dataobject("capability", False)
    @cached_property
    def host(self):
       return self._get_dataobject("host", True)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)
    @cached_property
    def iormConfiguration(self):
       return self._get_dataobject("iormConfiguration", False)
    @cached_property
    def summary(self):
       return self._get_dataobject("summary", False)
    @cached_property
    def vm(self):
       return self._get_mor("vm", True)


class DiagnosticManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class Network(ManagedEntity):
    _valid_attrs = set(['host', 'name', 'summary', 'vm'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def host(self):
       return self._get_mor("host", True)
    @cached_property
    def name(self):
       return self._get_dataobject("name", False)
    @cached_property
    def summary(self):
       return self._get_dataobject("summary", False)
    @cached_property
    def vm(self):
       return self._get_mor("vm", True)


class DistributedVirtualPortgroup(Network):
    _valid_attrs = set(['config', 'key', 'portKeys'])
    def __init__(self, mo_ref, client):
        Network.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, Network._valid_attrs)
    @cached_property
    def config(self):
       return self._get_dataobject("config", False)
    @cached_property
    def key(self):
       return self._get_dataobject("key", False)
    @cached_property
    def portKeys(self):
       return self._get_dataobject("portKeys", True)


class DistributedVirtualSwitch(ManagedEntity):
    _valid_attrs = set(['capability', 'config', 'networkResourcePool', 'portgroup', 'summary', 'uuid'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def capability(self):
       return self._get_dataobject("capability", False)
    @cached_property
    def config(self):
       return self._get_dataobject("config", False)
    @cached_property
    def networkResourcePool(self):
       return self._get_dataobject("networkResourcePool", True)
    @cached_property
    def portgroup(self):
       return self._get_mor("portgroup", True)
    @cached_property
    def summary(self):
       return self._get_dataobject("summary", False)
    @cached_property
    def uuid(self):
       return self._get_dataobject("uuid", False)


class DistributedVirtualSwitchManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class EnvironmentBrowser(ManagedObject):
    _valid_attrs = set(['datastoreBrowser'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def datastoreBrowser(self):
       return self._get_mor("datastoreBrowser", False)


class HistoryCollector(ManagedObject):
    _valid_attrs = set(['filter'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def filter(self):
       return self._get_dataobject("filter", False)


class EventHistoryCollector(HistoryCollector):
    _valid_attrs = set(['latestPage'])
    def __init__(self, mo_ref, client):
        HistoryCollector.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, HistoryCollector._valid_attrs)
    @cached_property
    def latestPage(self):
       return self._get_dataobject("latestPage", True)


class EventManager(ManagedObject):
    _valid_attrs = set(['description', 'latestEvent', 'maxCollector'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def description(self):
       return self._get_dataobject("description", False)
    @cached_property
    def latestEvent(self):
       return self._get_dataobject("latestEvent", False)
    @cached_property
    def maxCollector(self):
       return self._get_dataobject("maxCollector", False)


class ExtensionManager(ManagedObject):
    _valid_attrs = set(['extensionList'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def extensionList(self):
       return self._get_dataobject("extensionList", True)


class FileManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class Folder(ManagedEntity):
    _valid_attrs = set(['childEntity', 'childType'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def childEntity(self):
       return self._get_mor("childEntity", True)
    @cached_property
    def childType(self):
       return self._get_dataobject("childType", True)


class GuestAuthManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class GuestFileManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class GuestOperationsManager(ManagedObject):
    _valid_attrs = set(['authManager', 'fileManager', 'processManager'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def authManager(self):
       return self._get_mor("authManager", False)
    @cached_property
    def fileManager(self):
       return self._get_mor("fileManager", False)
    @cached_property
    def processManager(self):
       return self._get_mor("processManager", False)


class GuestProcessManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)

class HostAuthenticationStore(ManagedObject):
    _valid_attrs = set(['info'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)


class HostDirectoryStore(HostAuthenticationStore):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        HostAuthenticationStore.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, HostAuthenticationStore._valid_attrs)


class HostActiveDirectoryAuthentication(HostDirectoryStore):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        HostDirectoryStore.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, HostDirectoryStore._valid_attrs)


class HostAuthenticationManager(ManagedObject):
    _valid_attrs = set(['info', 'supportedStore'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)
    @cached_property
    def supportedStore(self):
       return self._get_mor("supportedStore", True)


class HostAutoStartManager(ManagedObject):
    _valid_attrs = set(['config'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def config(self):
       return self._get_dataobject("config", False)


class HostBootDeviceSystem(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)

class HostCacheConfigurationManager(ManagedObject):
    _valid_attrs = set(['cacheConfigurationInfo'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def cacheConfigurationInfo(self):
       return self._get_dataobject("cacheConfigurationInfo", True)

class HostCpuSchedulerSystem(ExtensibleManagedObject):
    _valid_attrs = set(['hyperthreadInfo'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def hyperthreadInfo(self):
       return self._get_dataobject("hyperthreadInfo", False)


class HostDatastoreBrowser(ManagedObject):
    _valid_attrs = set(['datastore', 'supportedType'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def datastore(self):
       return self._get_mor("datastore", True)
    @cached_property
    def supportedType(self):
       return self._get_dataobject("supportedType", True)


class HostDatastoreSystem(ManagedObject):
    _valid_attrs = set(['capabilities', 'datastore'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def capabilities(self):
       return self._get_dataobject("capabilities", False)
    @cached_property
    def datastore(self):
       return self._get_mor("datastore", True)


class HostDateTimeSystem(ManagedObject):
    _valid_attrs = set(['dateTimeInfo'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def dateTimeInfo(self):
       return self._get_dataobject("dateTimeInfo", False)


class HostDiagnosticSystem(ManagedObject):
    _valid_attrs = set(['activePartition'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def activePartition(self):
       return self._get_dataobject("activePartition", False)

class HostEsxAgentHostManager(ManagedObject):
    _valid_attrs = set(['configInfo'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def configInfo(self):
       return self._get_dataobject("configInfo", False)

class HostFirewallSystem(ExtensibleManagedObject):
    _valid_attrs = set(['firewallInfo'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def firewallInfo(self):
       return self._get_dataobject("firewallInfo", False)


class HostFirmwareSystem(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class HostHealthStatusSystem(ManagedObject):
    _valid_attrs = set(['runtime'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def runtime(self):
       return self._get_dataobject("runtime", False)

class HostImageConfigManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)

class HostKernelModuleSystem(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class HostLocalAccountManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class HostLocalAuthentication(HostAuthenticationStore):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        HostAuthenticationStore.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, HostAuthenticationStore._valid_attrs)


class HostMemorySystem(ExtensibleManagedObject):
    _valid_attrs = set(['consoleReservationInfo', 'virtualMachineReservationInfo'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def consoleReservationInfo(self):
       return self._get_dataobject("consoleReservationInfo", False)
    @cached_property
    def virtualMachineReservationInfo(self):
       return self._get_dataobject("virtualMachineReservationInfo", False)


class HostNetworkSystem(ExtensibleManagedObject):
    _valid_attrs = set(['capabilities', 'consoleIpRouteConfig', 'dnsConfig', 'ipRouteConfig', 'networkConfig', 'networkInfo', 'offloadCapabilities'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def capabilities(self):
       return self._get_dataobject("capabilities", False)
    @cached_property
    def consoleIpRouteConfig(self):
       return self._get_dataobject("consoleIpRouteConfig", False)
    @cached_property
    def dnsConfig(self):
       return self._get_dataobject("dnsConfig", False)
    @cached_property
    def ipRouteConfig(self):
       return self._get_dataobject("ipRouteConfig", False)
    @cached_property
    def networkConfig(self):
       return self._get_dataobject("networkConfig", False)
    @cached_property
    def networkInfo(self):
       return self._get_dataobject("networkInfo", False)
    @cached_property
    def offloadCapabilities(self):
       return self._get_dataobject("offloadCapabilities", False)


class HostPatchManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class HostPciPassthruSystem(ExtensibleManagedObject):
    _valid_attrs = set(['pciPassthruInfo'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def pciPassthruInfo(self):
       return self._get_dataobject("pciPassthruInfo", True)


class HostPowerSystem(ManagedObject):
    _valid_attrs = set(['capability', 'info'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def capability(self):
       return self._get_dataobject("capability", False)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)


class HostProfile(Profile):
    _valid_attrs = set(['referenceHost'])
    def __init__(self, mo_ref, client):
        Profile.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, Profile._valid_attrs)
    @cached_property
    def referenceHost(self):
       return self._get_mor("referenceHost", False)


class HostProfileManager(ProfileManager):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ProfileManager.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ProfileManager._valid_attrs)


class HostServiceSystem(ExtensibleManagedObject):
    _valid_attrs = set(['serviceInfo'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def serviceInfo(self):
       return self._get_dataobject("serviceInfo", False)


class HostSnmpSystem(ManagedObject):
    _valid_attrs = set(['configuration', 'limits'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def configuration(self):
       return self._get_dataobject("configuration", False)
    @cached_property
    def limits(self):
       return self._get_dataobject("limits", False)


class HostStorageSystem(ExtensibleManagedObject):
    _valid_attrs = set(['fileSystemVolumeInfo', 'multipathStateInfo', 'storageDeviceInfo', 'systemFile'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def fileSystemVolumeInfo(self):
       return self._get_dataobject("fileSystemVolumeInfo", False)
    @cached_property
    def multipathStateInfo(self):
       return self._get_dataobject("multipathStateInfo", False)
    @cached_property
    def storageDeviceInfo(self):
       return self._get_dataobject("storageDeviceInfo", False)
    @cached_property
    def systemFile(self):
       return self._get_dataobject("systemFile", True)


class HostSystem(ManagedEntity):
    _valid_attrs = set(['capability', 'config', 'configManager', 'datastore', 'datastoreBrowser', 'hardware', 'licensableResource', 'network', 'runtime', 'summary', 'systemResources', 'vm'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def capability(self):
       return self._get_dataobject("capability", False)
    @cached_property
    def config(self):
       return self._get_dataobject("config", False)
    @cached_property
    def configManager(self):
       return self._get_dataobject("configManager", False)
    @cached_property
    def datastore(self):
       return self._get_mor("datastore", True)
    @cached_property
    def datastoreBrowser(self):
       return self._get_mor("datastoreBrowser", False)
    @cached_property
    def licensableResource(self):
       return self._get_dataobject("licensableResource", False)
    @cached_property
    def hardware(self):
       return self._get_dataobject("hardware", False)
    @cached_property
    def network(self):
       return self._get_mor("network", True)
    @cached_property
    def runtime(self):
       return self._get_dataobject("runtime", False)
    @cached_property
    def summary(self):
       return self._get_dataobject("summary", False)
    @cached_property
    def systemResources(self):
       return self._get_dataobject("systemResources", False)
    @cached_property
    def vm(self):
       return self._get_mor("vm", True)


class HostVirtualNicManager(ExtensibleManagedObject):
    _valid_attrs = set(['info'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)


class HostVMotionSystem(ExtensibleManagedObject):
    _valid_attrs = set(['ipConfig', 'netConfig'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def ipConfig(self):
       return self._get_dataobject("ipConfig", False)
    @cached_property
    def netConfig(self):
       return self._get_dataobject("netConfig", False)


class HttpNfcLease(ManagedObject):
    _valid_attrs = set(['error', 'info', 'initializeProgress', 'state'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def error(self):
       return self._get_dataobject("error", False)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)
    @cached_property
    def initializeProgress(self):
       return self._get_dataobject("initializeProgress", False)
    @cached_property
    def state(self):
       return self._get_dataobject("state", False)


class InventoryView(ManagedObjectView):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObjectView.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObjectView._valid_attrs)


class IpPoolManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)

class IscsiManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)

class LicenseAssignmentManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class LicenseManager(ManagedObject):
    _valid_attrs = set(['diagnostics', 'evaluation', 'featureInfo', 'licenseAssignmentManager', 'licensedEdition', 'licenses', 'source', 'sourceAvailable'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def diagnostics(self):
       return self._get_dataobject("diagnostics", False)
    @cached_property
    def evaluation(self):
       return self._get_dataobject("evaluation", False)
    @cached_property
    def featureInfo(self):
       return self._get_dataobject("featureInfo", True)
    @cached_property
    def licenseAssignmentManager(self):
       return self._get_mor("licenseAssignmentManager", False)
    @cached_property
    def licensedEdition(self):
       return self._get_dataobject("licensedEdition", False)
    @cached_property
    def licenses(self):
       return self._get_dataobject("licenses", True)
    @cached_property
    def source(self):
       return self._get_dataobject("source", False)
    @cached_property
    def sourceAvailable(self):
       return self._get_dataobject("sourceAvailable", False)


class ListView(ManagedObjectView):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObjectView.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObjectView._valid_attrs)


class LocalizationManager(ManagedObject):
    _valid_attrs = set(['catalog'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def catalog(self):
       return self._get_dataobject("catalog", True)


class OptionManager(ManagedObject):
    _valid_attrs = set(['setting', 'supportedOption'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def setting(self):
       return self._get_dataobject("setting", True)
    @cached_property
    def supportedOption(self):
       return self._get_dataobject("supportedOption", True)


class OvfManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class PerformanceManager(ManagedObject):
    _valid_attrs = set(['description', 'historicalInterval', 'perfCounter'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def description(self):
       return self._get_dataobject("description", False)
    @cached_property
    def historicalInterval(self):
       return self._get_dataobject("historicalInterval", True)
    @cached_property
    def perfCounter(self):
       return self._get_dataobject("perfCounter", True)


class ProfileComplianceManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class PropertyCollector(ManagedObject):
    _valid_attrs = set(['filter'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def filter(self):
       return self._get_mor("filter", True)


class PropertyFilter(ManagedObject):
    _valid_attrs = set(['partialUpdates', 'spec'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def partialUpdates(self):
       return self._get_dataobject("partialUpdates", False)
    @cached_property
    def spec(self):
       return self._get_dataobject("spec", False)


class ResourcePlanningManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class ResourcePool(ManagedEntity):
    _valid_attrs = set(['childConfiguration', 'config', 'owner', 'resourcePool', 'runtime', 'summary', 'vm'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def childConfiguration(self):
       return self._get_dataobject("childConfiguration", True)
    @cached_property
    def config(self):
       return self._get_dataobject("config", False)
    @cached_property
    def owner(self):
       return self._get_mor("owner", False)
    @cached_property
    def resourcePool(self):
       return self._get_mor("resourcePool", True)
    @cached_property
    def runtime(self):
       return self._get_dataobject("runtime", False)
    @cached_property
    def summary(self):
       return self._get_dataobject("summary", False)
    @cached_property
    def vm(self):
       return self._get_mor("vm", True)


class ScheduledTask(ExtensibleManagedObject):
    _valid_attrs = set(['info'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)


class ScheduledTaskManager(ManagedObject):
    _valid_attrs = set(['description', 'scheduledTask'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def description(self):
       return self._get_dataobject("description", False)
    @cached_property
    def scheduledTask(self):
       return self._get_mor("scheduledTask", True)


class SearchIndex(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class ServiceInstance(ManagedObject):
    _valid_attrs = set(['capability', 'content', 'serverClock'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def capability(self):
       return self._get_dataobject("capability", False)
    @cached_property
    def content(self):
       return self._get_dataobject("content", False)
    @cached_property
    def serverClock(self):
       return self._get_dataobject("serverClock", False)


class SessionManager(ManagedObject):
    _valid_attrs = set(['currentSession', 'defaultLocale', 'message', 'messageLocaleList', 'sessionList', 'supportedLocaleList'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def currentSession(self):
       return self._get_dataobject("currentSession", False)
    @cached_property
    def defaultLocale(self):
       return self._get_dataobject("defaultLocale", False)
    @cached_property
    def message(self):
       return self._get_dataobject("message", False)
    @cached_property
    def messageLocaleList(self):
       return self._get_dataobject("messageLocaleList", True)
    @cached_property
    def sessionList(self):
       return self._get_dataobject("sessionList", True)
    @cached_property
    def supportedLocaleList(self):
       return self._get_dataobject("supportedLocaleList", True)

class StoragePod(Folder):
    _valid_attrs = set(['podStorageDrsEntry', 'summary'])
    def __init__(self, mo_ref, client):
        Folder.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, Folder._valid_attrs)
    @cached_property
    def podStorageDrsEntry(self):
       return self._get_dataobject("podStorageDrsEntry", False)
    @cached_property
    def summary(self):
       return self._get_dataobject("summary", False)

class StorageResourceManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class Task(ExtensibleManagedObject):
    _valid_attrs = set(['info'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def info(self):
       return self._get_dataobject("info", False)


class TaskHistoryCollector(HistoryCollector):
    _valid_attrs = set(['latestPage'])
    def __init__(self, mo_ref, client):
        HistoryCollector.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, HistoryCollector._valid_attrs)
    @cached_property
    def latestPage(self):
       return self._get_dataobject("latestPage", True)


class TaskManager(ManagedObject):
    _valid_attrs = set(['description', 'maxCollector', 'recentTask'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def description(self):
       return self._get_dataobject("description", False)
    @cached_property
    def maxCollector(self):
       return self._get_dataobject("maxCollector", False)
    @cached_property
    def recentTask(self):
       return self._get_mor("recentTask", True)


class UserDirectory(ManagedObject):
    _valid_attrs = set(['domainList'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def domainList(self):
       return self._get_dataobject("domainList", True)


class ViewManager(ManagedObject):
    _valid_attrs = set(['viewList'])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)
    @cached_property
    def viewList(self):
       return self._get_mor("viewList", True)


class VirtualApp(ResourcePool):
    _valid_attrs = set(['childLink', 'datastore', 'network', 'parentFolder', 'parentVApp', 'vAppConfig'])
    def __init__(self, mo_ref, client):
        ResourcePool.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ResourcePool._valid_attrs)
    @cached_property
    def childLink(self):
       return self._get_dataobject("childLink", True)
    @cached_property
    def datastore(self):
       return self._get_mor("datastore", True)
    @cached_property
    def network(self):
       return self._get_mor("network", True)
    @cached_property
    def parentFolder(self):
       return self._get_mor("parentFolder", False)
    @cached_property
    def parentVApp(self):
       return self._get_mor("parentVApp", False)
    @cached_property
    def vAppConfig(self):
       return self._get_dataobject("vAppConfig", False)


class VirtualDiskManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class VirtualizationManager(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class VirtualMachine(ManagedEntity):
    _valid_attrs = set(['capability', 'config', 'datastore', 'environmentBrowser', 'guest', 'guestHeartbeatStatus', 'layout', 'layoutEx', 'network', 'parentVApp', 'resourceConfig', 'resourcePool', 'rootSnapshot', 'runtime', 'snapshot', 'storage', 'summary'])
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedEntity._valid_attrs)
    @cached_property
    def capability(self):
       return self._get_dataobject("capability", False)
    @cached_property
    def config(self):
       return self._get_dataobject("config", False)
    @cached_property
    def datastore(self):
       return self._get_mor("datastore", True)
    @cached_property
    def environmentBrowser(self):
       return self._get_mor("environmentBrowser", False)
    @cached_property
    def guest(self):
       return self._get_dataobject("guest", False)
    @cached_property
    def guestHeartbeatStatus(self):
       return self._get_dataobject("guestHeartbeatStatus", False)
    @cached_property
    def layout(self):
       return self._get_dataobject("layout", False)
    @cached_property
    def layoutEx(self):
       return self._get_dataobject("layoutEx", False)
    @cached_property
    def network(self):
       return self._get_mor("network", True)
    @cached_property
    def parentVApp(self):
       return self._get_mor("parentVApp", False)
    @cached_property
    def resourceConfig(self):
       return self._get_dataobject("resourceConfig", False)
    @cached_property
    def resourcePool(self):
       return self._get_mor("resourcePool", False)
    @cached_property
    def rootSnapshot(self):
       return self._get_mor("rootSnapshot", True)
    @cached_property
    def runtime(self):
       return self._get_dataobject("runtime", False)
    @cached_property
    def snapshot(self):
       return self._get_dataobject("snapshot", False)
    @cached_property
    def storage(self):
       return self._get_dataobject("storage", False)
    @cached_property
    def summary(self):
       return self._get_dataobject("summary", False)


class VirtualMachineCompatibilityChecker(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class VirtualMachineProvisioningChecker(ManagedObject):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ManagedObject._valid_attrs)


class VirtualMachineSnapshot(ExtensibleManagedObject):
    _valid_attrs = set(['childSnapshot', 'config'])
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, ExtensibleManagedObject._valid_attrs)
    @cached_property
    def childSnapshot(self):
       return self._get_mor("childSnapshot", True)
    @cached_property
    def config(self):
       return self._get_dataobject("config", False)


class VmwareDistributedVirtualSwitch(DistributedVirtualSwitch):
    _valid_attrs = set([])
    def __init__(self, mo_ref, client):
        DistributedVirtualSwitch.__init__(self, mo_ref, client)
        self._valid_attrs = set.union(self._valid_attrs, DistributedVirtualSwitch._valid_attrs)


classmap = dict((x.__name__, x) for x in (
    ExtensibleManagedObject,
    Alarm,
    AlarmManager,
    AuthorizationManager,
    ManagedEntity,
    ComputeResource,
    ClusterComputeResource,
    Profile,
    ClusterProfile,
    ProfileManager,
    ClusterProfileManager,
    View,
    ManagedObjectView,
    ContainerView,
    CustomFieldsManager,
    CustomizationSpecManager,
    Datacenter,
    Datastore,
    DiagnosticManager,
    Network,
    DistributedVirtualPortgroup,
    DistributedVirtualSwitch,
    DistributedVirtualSwitchManager,
    EnvironmentBrowser,
    HistoryCollector,
    EventHistoryCollector,
    EventManager,
    ExtensionManager,
    FileManager,
    Folder,
    GuestAuthManager,
    GuestFileManager,
    GuestOperationsManager,
    GuestProcessManager,
    HostAuthenticationStore,
    HostDirectoryStore,
    HostActiveDirectoryAuthentication,
    HostAuthenticationManager,
    HostAutoStartManager,
    HostBootDeviceSystem,
    HostCacheConfigurationManager,
    HostCpuSchedulerSystem,
    HostDatastoreBrowser,
    HostDatastoreSystem,
    HostDateTimeSystem,
    HostDiagnosticSystem,
    HostEsxAgentHostManager,
    HostFirewallSystem,
    HostFirmwareSystem,
    HostHealthStatusSystem,
    HostImageConfigManager,
    HostKernelModuleSystem,
    HostLocalAccountManager,
    HostLocalAuthentication,
    HostMemorySystem,
    HostNetworkSystem,
    HostPatchManager,
    HostPciPassthruSystem,
    HostPowerSystem,
    HostProfile,
    HostProfileManager,
    HostServiceSystem,
    HostSnmpSystem,
    HostStorageSystem,
    HostSystem,
    HostVirtualNicManager,
    HostVMotionSystem,
    HttpNfcLease,
    InventoryView,
    IpPoolManager,
    IscsiManager,
    LicenseAssignmentManager,
    LicenseManager,
    ListView,
    LocalizationManager,
    OptionManager,
    OvfManager,
    PerformanceManager,
    ProfileComplianceManager,
    PropertyCollector,
    PropertyFilter,
    ResourcePlanningManager,
    ResourcePool,
    ScheduledTask,
    ScheduledTaskManager,
    SearchIndex,
    ServiceInstance,
    SessionManager,
    StoragePod,
    StorageResourceManager,
    Task,
    TaskHistoryCollector,
    TaskManager,
    UserDirectory,
    ViewManager,
    VirtualApp,
    VirtualDiskManager,
    VirtualizationManager,
    VirtualMachine,
    VirtualMachineCompatibilityChecker,
    VirtualMachineProvisioningChecker,
    VirtualMachineSnapshot,
    VmwareDistributedVirtualSwitch
))
def classmapper(name):
    return classmap[name]
