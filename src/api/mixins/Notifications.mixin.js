const NotificationsMixin = (parent) => class extends parent {
  readNotificationTemplates (id, params = {}) {
    return this.http.get(`${this.baseUrl}${id}/notification_templates/`, { params });
  }

  readNotificationTemplatesSuccess (id, params = {}) {
    return this.http.get(`${this.baseUrl}${id}/notification_templates_success/`, { params });
  }

  readNotificationTemplatesError (id, params = {}) {
    return this.http.get(`${this.baseUrl}${id}/notification_templates_error/`, { params });
  }

  associateNotificationTemplatesSuccess (resourceId, notificationId) {
    return this.http.post(`${this.baseUrl}${resourceId}/notification_templates_success/`, { id: notificationId });
  }

  disassociateNotificationTemplatesSuccess (resourceId, notificationId) {
    return this.http.post(`${this.baseUrl}${resourceId}/notification_templates_success/`, { id: notificationId, disassociate: true });
  }

  associateNotificationTemplatesError (resourceId, notificationId) {
    return this.http.post(`${this.baseUrl}${resourceId}/notification_templates_error/`, { id: notificationId });
  }

  disassociateNotificationTemplatesError (resourceId, notificationId) {
    return this.http.post(`${this.baseUrl}${resourceId}/notification_templates_error/`, { id: notificationId, disassociate: true });
  }
};

export default NotificationsMixin;
