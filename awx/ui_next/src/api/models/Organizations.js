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

  readAccessOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/access_list/`);
  }

  readTeams(id, params) {
    return this.http.get(`${this.baseUrl}${id}/teams/`, { params });
  }

  readTeamsOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/teams/`);
  }

  readGalaxyCredentials(id, params) {
    return this.http.get(`${this.baseUrl}${id}/galaxy_credentials/`, {
      params,
    });
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

  associateGalaxyCredential(resourceId, credentialId) {
    return this.http.post(`${this.baseUrl}${resourceId}/galaxy_credentials/`, {
      id: credentialId,
    });
  }

  disassociateGalaxyCredential(resourceId, credentialId) {
    return this.http.post(`${this.baseUrl}${resourceId}/galaxy_credentials/`, {
      id: credentialId,
      disassociate: true,
    });
  }
}

export default Organizations;
