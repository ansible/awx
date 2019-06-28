import Config from './models/Config';
import InstanceGroups from './models/InstanceGroups';
import JobTemplates from './models/JobTemplates';
import Jobs from './models/Jobs';
import Me from './models/Me';
import Organizations from './models/Organizations';
import Root from './models/Root';
import Teams from './models/Teams';
import UnifiedJobTemplates from './models/UnifiedJobTemplates';
import UnifiedJobs from './models/UnifiedJobs';
import Users from './models/Users';
import WorkflowJobTemplates from './models/WorkflowJobTemplates';

const ConfigAPI = new Config();
const InstanceGroupsAPI = new InstanceGroups();
const JobTemplatesAPI = new JobTemplates();
const JobsAPI = new Jobs();
const MeAPI = new Me();
const OrganizationsAPI = new Organizations();
const RootAPI = new Root();
const TeamsAPI = new Teams();
const UnifiedJobTemplatesAPI = new UnifiedJobTemplates();
const UnifiedJobsAPI = new UnifiedJobs();
const UsersAPI = new Users();
const WorkflowJobTemplatesAPI = new WorkflowJobTemplates();

export {
  ConfigAPI,
  InstanceGroupsAPI,
  JobTemplatesAPI,
  JobsAPI,
  MeAPI,
  OrganizationsAPI,
  RootAPI,
  TeamsAPI,
  UnifiedJobTemplatesAPI,
  UnifiedJobsAPI,
  UsersAPI,
  WorkflowJobTemplatesAPI,
};
