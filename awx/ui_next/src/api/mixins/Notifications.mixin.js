const NotificationsMixin = parent =>
  class extends parent {
    readOptionsNotificationTemplates(id) {
      return this.http.options(`${this.baseUrl}${id}/notification_templates/`);
    }

    readNotificationTemplates(id, params) {
      return this.http.get(
        `${this.baseUrl}${id}/notification_templates/`,
        params
      );
    }

    readNotificationTemplatesStarted(id, params) {
      return this.http.get(
        `${this.baseUrl}${id}/notification_templates_started/`,
        { params }
      );
    }

    readNotificationTemplatesSuccess(id, params) {
      return this.http.get(
        `${this.baseUrl}${id}/notification_templates_success/`,
        { params }
      );
    }

    readNotificationTemplatesError(id, params) {
      return this.http.get(
        `${this.baseUrl}${id}/notification_templates_error/`,
        { params }
      );
    }

    associateNotificationTemplatesStarted(resourceId, notificationId) {
      return this.http.post(
        `${this.baseUrl}${resourceId}/notification_templates_started/`,
        { id: notificationId }
      );
    }

    disassociateNotificationTemplatesStarted(resourceId, notificationId) {
      return this.http.post(
        `${this.baseUrl}${resourceId}/notification_templates_started/`,
        { id: notificationId, disassociate: true }
      );
    }

    associateNotificationTemplatesSuccess(resourceId, notificationId) {
      return this.http.post(
        `${this.baseUrl}${resourceId}/notification_templates_success/`,
        { id: notificationId }
      );
    }

    disassociateNotificationTemplatesSuccess(resourceId, notificationId) {
      return this.http.post(
        `${this.baseUrl}${resourceId}/notification_templates_success/`,
        { id: notificationId, disassociate: true }
      );
    }

    associateNotificationTemplatesError(resourceId, notificationId) {
      return this.http.post(
        `${this.baseUrl}${resourceId}/notification_templates_error/`,
        { id: notificationId }
      );
    }

    disassociateNotificationTemplatesError(resourceId, notificationId) {
      return this.http.post(
        `${this.baseUrl}${resourceId}/notification_templates_error/`,
        { id: notificationId, disassociate: true }
      );
    }

    /**
     * This is a helper method meant to simplify setting the "on" status of
     * a related notification.
     *
     * @param[resourceId] - id of the base resource
     * @param[notificationId] - id of the notification
     * @param[notificationType] - the type of notification, options are "success" and "error"
     */
    associateNotificationTemplate(
      resourceId,
      notificationId,
      notificationType
    ) {
      if (notificationType === 'approvals') {
        return this.associateNotificationTemplatesApprovals(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'started') {
        return this.associateNotificationTemplatesStarted(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'success') {
        return this.associateNotificationTemplatesSuccess(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'error') {
        return this.associateNotificationTemplatesError(
          resourceId,
          notificationId
        );
      }

      throw new Error(
        `Unsupported notificationType for association: ${notificationType}`
      );
    }

    /**
     * This is a helper method meant to simplify setting the "off" status of
     * a related notification.
     *
     * @param[resourceId] - id of the base resource
     * @param[notificationId] - id of the notification
     * @param[notificationType] - the type of notification, options are "success" and "error"
     */
    disassociateNotificationTemplate(
      resourceId,
      notificationId,
      notificationType
    ) {
      if (notificationType === 'approvals') {
        return this.disassociateNotificationTemplatesApprovals(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'started') {
        return this.disassociateNotificationTemplatesStarted(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'success') {
        return this.disassociateNotificationTemplatesSuccess(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'error') {
        return this.disassociateNotificationTemplatesError(
          resourceId,
          notificationId
        );
      }

      throw new Error(
        `Unsupported notificationType for disassociation: ${notificationType}`
      );
    }
  };

export default NotificationsMixin;
