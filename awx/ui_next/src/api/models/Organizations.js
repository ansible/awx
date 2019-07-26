import Base from '../Base';
import NotificationsMixin from '../mixins/Notifications.mixin';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class Organizations extends InstanceGroupsMixin(NotificationsMixin(Base)) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/organizations/';
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, { params });
  }

  readTeams(id, params) {
    return this.http.get(`${this.baseUrl}${id}/teams/`, { params });
  }
}

export default Organizations;
