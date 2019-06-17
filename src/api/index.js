import Config from './models/Config';
import InstanceGroups from './models/InstanceGroups';
import Jobs from './models/Jobs';
import Me from './models/Me';
import Organizations from './models/Organizations';
import Root from './models/Root';
import Teams from './models/Teams';
import UnifiedJobTemplates from './models/UnifiedJobTemplates';
import Users from './models/Users';

const ConfigAPI = new Config();
const InstanceGroupsAPI = new InstanceGroups();
const JobsAPI = new Jobs();
const MeAPI = new Me();
const OrganizationsAPI = new Organizations();
const RootAPI = new Root();
const TeamsAPI = new Teams();
const UnifiedJobTemplatesAPI = new UnifiedJobTemplates();
const UsersAPI = new Users();

export {
  ConfigAPI,
  InstanceGroupsAPI,
  JobsAPI,
  MeAPI,
  OrganizationsAPI,
  RootAPI,
  TeamsAPI,
  UnifiedJobTemplatesAPI,
  UsersAPI
};
