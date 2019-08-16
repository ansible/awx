import Config from './models/Config';
import InstanceGroups from './models/InstanceGroups';
import Inventories from './models/Inventories';
import JobTemplates from './models/JobTemplates';
import Jobs from './models/Jobs';
import Labels from './models/Labels';
import Me from './models/Me';
import Organizations from './models/Organizations';
import Projects from './models/Projects';
import Root from './models/Root';
import Teams from './models/Teams';
import UnifiedJobTemplates from './models/UnifiedJobTemplates';
import UnifiedJobs from './models/UnifiedJobs';
import Users from './models/Users';
import WorkflowJobTemplates from './models/WorkflowJobTemplates';

const ConfigAPI = new Config();
const InstanceGroupsAPI = new InstanceGroups();
const InventoriesAPI = new Inventories();
const JobTemplatesAPI = new JobTemplates();
const JobsAPI = new Jobs();
const LabelsAPI = new Labels();
const MeAPI = new Me();
const OrganizationsAPI = new Organizations();
const ProjectsAPI = new Projects();
const RootAPI = new Root();
const TeamsAPI = new Teams();
const UnifiedJobTemplatesAPI = new UnifiedJobTemplates();
const UnifiedJobsAPI = new UnifiedJobs();
const UsersAPI = new Users();
const WorkflowJobTemplatesAPI = new WorkflowJobTemplates();

export {
  ConfigAPI,
  InstanceGroupsAPI,
  InventoriesAPI,
  JobTemplatesAPI,
  JobsAPI,
  LabelsAPI,
  MeAPI,
  OrganizationsAPI,
  ProjectsAPI,
  RootAPI,
  TeamsAPI,
  UnifiedJobTemplatesAPI,
  UnifiedJobsAPI,
  UsersAPI,
  WorkflowJobTemplatesAPI,
};
