import Config from './models/Config';
import InstanceGroups from './models/InstanceGroups';
import Me from './models/Me';
import Organizations from './models/Organizations';
import Root from './models/Root';
import Teams from './models/Teams';
import Users from './models/Users';

const ConfigAPI = new Config();
const InstanceGroupsAPI = new InstanceGroups();
const MeAPI = new Me();
const OrganizationsAPI = new Organizations();
const RootAPI = new Root();
const TeamsAPI = new Teams();
const UsersAPI = new Users();

export {
  ConfigAPI,
  InstanceGroupsAPI,
  MeAPI,
  OrganizationsAPI,
  RootAPI,
  TeamsAPI,
  UsersAPI
};
