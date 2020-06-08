import AdHocCommands from './models/AdHocCommands';
import Applications from './models/Applications';
import Config from './models/Config';
import CredentialInputSources from './models/CredentialInputSources';
import CredentialTypes from './models/CredentialTypes';
import Credentials from './models/Credentials';
import Groups from './models/Groups';
import Hosts from './models/Hosts';
import InstanceGroups from './models/InstanceGroups';
import Inventories from './models/Inventories';
import InventorySources from './models/InventorySources';
import InventoryUpdates from './models/InventoryUpdates';
import JobTemplates from './models/JobTemplates';
import Jobs from './models/Jobs';
import Labels from './models/Labels';
import Me from './models/Me';
import NotificationTemplates from './models/NotificationTemplates';
import Organizations from './models/Organizations';
import ProjectUpdates from './models/ProjectUpdates';
import Projects from './models/Projects';
import Root from './models/Root';
import Roles from './models/Roles';
import Schedules from './models/Schedules';
import SystemJobs from './models/SystemJobs';
import Teams from './models/Teams';
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
const GroupsAPI = new Groups();
const HostsAPI = new Hosts();
const InstanceGroupsAPI = new InstanceGroups();
const InventoriesAPI = new Inventories();
const InventorySourcesAPI = new InventorySources();
const InventoryUpdatesAPI = new InventoryUpdates();
const JobTemplatesAPI = new JobTemplates();
const JobsAPI = new Jobs();
const LabelsAPI = new Labels();
const MeAPI = new Me();
const NotificationTemplatesAPI = new NotificationTemplates();
const OrganizationsAPI = new Organizations();
const ProjectUpdatesAPI = new ProjectUpdates();
const ProjectsAPI = new Projects();
const RootAPI = new Root();
const RolesAPI = new Roles();
const SchedulesAPI = new Schedules();
const SystemJobsAPI = new SystemJobs();
const TeamsAPI = new Teams();
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
  GroupsAPI,
  HostsAPI,
  InstanceGroupsAPI,
  InventoriesAPI,
  InventorySourcesAPI,
  InventoryUpdatesAPI,
  JobTemplatesAPI,
  JobsAPI,
  LabelsAPI,
  MeAPI,
  NotificationTemplatesAPI,
  OrganizationsAPI,
  ProjectUpdatesAPI,
  ProjectsAPI,
  RootAPI,
  RolesAPI,
  SchedulesAPI,
  SystemJobsAPI,
  TeamsAPI,
  UnifiedJobTemplatesAPI,
  UnifiedJobsAPI,
  UsersAPI,
  WorkflowApprovalTemplatesAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
  WorkflowJobsAPI,
};
