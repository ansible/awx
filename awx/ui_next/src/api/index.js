import AdHocCommands from './models/AdHocCommands';
import Config from './models/Config';
import CredentialTypes from './models/CredentialTypes';
import Credentials from './models/Credentials';
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
import SystemJobs from './models/SystemJobs';
import Teams from './models/Teams';
import UnifiedJobTemplates from './models/UnifiedJobTemplates';
import UnifiedJobs from './models/UnifiedJobs';
import Users from './models/Users';
import WorkflowJobs from './models/WorkflowJobs';
import WorkflowJobTemplates from './models/WorkflowJobTemplates';

const AdHocCommandsAPI = new AdHocCommands();
const ConfigAPI = new Config();
const CredentialsAPI = new Credentials();
const CredentialTypesAPI = new CredentialTypes();
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
const SystemJobsAPI = new SystemJobs();
const TeamsAPI = new Teams();
const UnifiedJobTemplatesAPI = new UnifiedJobTemplates();
const UnifiedJobsAPI = new UnifiedJobs();
const UsersAPI = new Users();
const WorkflowJobsAPI = new WorkflowJobs();
const WorkflowJobTemplatesAPI = new WorkflowJobTemplates();

export {
  AdHocCommandsAPI,
  ConfigAPI,
  CredentialsAPI,
  CredentialTypesAPI,
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
  SystemJobsAPI,
  TeamsAPI,
  UnifiedJobTemplatesAPI,
  UnifiedJobsAPI,
  UsersAPI,
  WorkflowJobsAPI,
  WorkflowJobTemplatesAPI,
};
