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

  createUser(id, data) {
    return this.http.post(`${this.baseUrl}${id}/users/`, data);
  }

  readNotificationTemplatesApprovals(id, params) {
    return this.http.get(
      `${this.baseUrl}${id}/notification_templates_approvals/`,
      { params }
    );
  }

  associateNotificationTemplatesApprovals(resourceId, notificationId) {
    return this.http.post(
      `${this.baseUrl}${resourceId}/notification_templates_approvals/`,
      { id: notificationId }
    );
  }

  disassociateNotificationTemplatesApprovals(resourceId, notificationId) {
    return this.http.post(
      `${this.baseUrl}${resourceId}/notification_templates_approvals/`,
      { id: notificationId, disassociate: true }
    );
  }
}

export default Organizations;
