import AdHocCommands from './models/AdHocCommands';
import Config from './models/Config';
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
import Projects from './models/Projects';
import ProjectUpdates from './models/ProjectUpdates';
import Root from './models/Root';
import Schedules from './models/Schedules';
import SystemJobs from './models/SystemJobs';
import Teams from './models/Teams';
import UnifiedJobTemplates from './models/UnifiedJobTemplates';
import UnifiedJobs from './models/UnifiedJobs';
import Users from './models/Users';
import WorkflowApprovalTemplates from './models/WorkflowApprovalTemplates';
import WorkflowJobs from './models/WorkflowJobs';
import WorkflowJobTemplateNodes from './models/WorkflowJobTemplateNodes';
import WorkflowJobTemplates from './models/WorkflowJobTemplates';

const AdHocCommandsAPI = new AdHocCommands();
const ConfigAPI = new Config();
const CredentialsAPI = new Credentials();
const CredentialTypesAPI = new CredentialTypes();
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
const ProjectsAPI = new Projects();
const ProjectUpdatesAPI = new ProjectUpdates();
const RootAPI = new Root();
const SchedulesAPI = new Schedules();
const SystemJobsAPI = new SystemJobs();
const TeamsAPI = new Teams();
const UnifiedJobTemplatesAPI = new UnifiedJobTemplates();
const UnifiedJobsAPI = new UnifiedJobs();
const UsersAPI = new Users();
const WorkflowApprovalTemplatesAPI = new WorkflowApprovalTemplates();
const WorkflowJobsAPI = new WorkflowJobs();
const WorkflowJobTemplateNodesAPI = new WorkflowJobTemplateNodes();
const WorkflowJobTemplatesAPI = new WorkflowJobTemplates();

export {
  AdHocCommandsAPI,
  ConfigAPI,
  CredentialsAPI,
  CredentialTypesAPI,
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
  ProjectsAPI,
  ProjectUpdatesAPI,
  RootAPI,
  SchedulesAPI,
  SystemJobsAPI,
  TeamsAPI,
  UnifiedJobTemplatesAPI,
  UnifiedJobsAPI,
  UsersAPI,
  WorkflowApprovalTemplatesAPI,
  WorkflowJobsAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
};
