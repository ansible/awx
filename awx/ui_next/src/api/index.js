import AdHocCommands from './models/AdHocCommands';
import Applications from './models/Applications';
import Config from './models/Config';
import CredentialInputSources from './models/CredentialInputSources';
import CredentialTypes from './models/CredentialTypes';
import Credentials from './models/Credentials';
import Dashboard from './models/Dashboard';
import Groups from './models/Groups';
import Hosts from './models/Hosts';
import InstanceGroups from './models/InstanceGroups';
import Instances from './models/Instances';
import Inventories from './models/Inventories';
import InventoryScripts from './models/InventoryScripts';
import InventorySources from './models/InventorySources';
import InventoryUpdates from './models/InventoryUpdates';
import JobTemplates from './models/JobTemplates';
import Jobs from './models/Jobs';
import Labels from './models/Labels';
import Me from './models/Me';
import NotificationTemplates from './models/NotificationTemplates';
import Notifications from './models/Notifications';
import Organizations from './models/Organizations';
import ProjectUpdates from './models/ProjectUpdates';
import Projects from './models/Projects';
import Roles from './models/Roles';
import Root from './models/Root';
import Schedules from './models/Schedules';
import Settings from './models/Settings';
import SystemJobs from './models/SystemJobs';
import Teams from './models/Teams';
import Tokens from './models/Tokens';
import UnifiedJobTemplates from './models/UnifiedJobTemplates';
import UnifiedJobs from './models/UnifiedJobs';
import Users from './models/Users';
import WorkflowApprovalTemplates from './models/WorkflowApprovalTemplates';
import WorkflowJobTemplateNodes from './models/WorkflowJobTemplateNodes';
import WorkflowJobTemplates from './models/WorkflowJobTemplates';
import WorkflowJobs from './models/WorkflowJobs';

const AdHocCommandsAPI = new AdHocCommands();
const ApplicationsAPI = new Applications();
const ConfigAPI = new Config();
const CredentialInputSourcesAPI = new CredentialInputSources();
const CredentialTypesAPI = new CredentialTypes();
const CredentialsAPI = new Credentials();
const DashboardAPI = new Dashboard();
const GroupsAPI = new Groups();
const HostsAPI = new Hosts();
const InstanceGroupsAPI = new InstanceGroups();
const InstancesAPI = new Instances();
const InventoriesAPI = new Inventories();
const InventoryScriptsAPI = new InventoryScripts();
const InventorySourcesAPI = new InventorySources();
const InventoryUpdatesAPI = new InventoryUpdates();
const JobTemplatesAPI = new JobTemplates();
const JobsAPI = new Jobs();
const LabelsAPI = new Labels();
const MeAPI = new Me();
const NotificationTemplatesAPI = new NotificationTemplates();
const NotificationsAPI = new Notifications();
const OrganizationsAPI = new Organizations();
const ProjectUpdatesAPI = new ProjectUpdates();
const ProjectsAPI = new Projects();
const RolesAPI = new Roles();
const RootAPI = new Root();
const SchedulesAPI = new Schedules();
const SettingsAPI = new Settings();
const SystemJobsAPI = new SystemJobs();
const TeamsAPI = new Teams();
const TokensAPI = new Tokens();
const UnifiedJobTemplatesAPI = new UnifiedJobTemplates();
const UnifiedJobsAPI = new UnifiedJobs();
const UsersAPI = new Users();
const WorkflowApprovalTemplatesAPI = new WorkflowApprovalTemplates();
const WorkflowJobTemplateNodesAPI = new WorkflowJobTemplateNodes();
const WorkflowJobTemplatesAPI = new WorkflowJobTemplates();
const WorkflowJobsAPI = new WorkflowJobs();

export {
  AdHocCommandsAPI,
  ApplicationsAPI,
  ConfigAPI,
  CredentialInputSourcesAPI,
  CredentialTypesAPI,
  CredentialsAPI,
  DashboardAPI,
  GroupsAPI,
  HostsAPI,
  InstanceGroupsAPI,
  InstancesAPI,
  InventoriesAPI,
  InventoryScriptsAPI,
  InventorySourcesAPI,
  InventoryUpdatesAPI,
  JobTemplatesAPI,
  JobsAPI,
  LabelsAPI,
  MeAPI,
  NotificationTemplatesAPI,
  NotificationsAPI,
  OrganizationsAPI,
  ProjectUpdatesAPI,
  ProjectsAPI,
  RolesAPI,
  RootAPI,
  SchedulesAPI,
  SettingsAPI,
  SystemJobsAPI,
  TeamsAPI,
  TokensAPI,
  UnifiedJobTemplatesAPI,
  UnifiedJobsAPI,
  UsersAPI,
  WorkflowApprovalTemplatesAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
  WorkflowJobsAPI,
};
