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

    readNotificationTemplatesSuccess(id, params) {
      return this.http.get(
        `${this.baseUrl}${id}/notification_templates_success/`,
        params
      );
    }

    readNotificationTemplatesError(id, params) {
      return this.http.get(
        `${this.baseUrl}${id}/notification_templates_error/`,
        params
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
     * This is a helper method meant to simplify setting the "on" or "off" status of
     * a related notification.
     *
     * @param[resourceId] - id of the base resource
     * @param[notificationId] - id of the notification
     * @param[notificationType] - the type of notification, options are "success" and "error"
     * @param[associationState] - Boolean for associating or disassociating, options are true or false
     */
    // eslint-disable-next-line max-len
    updateNotificationTemplateAssociation(
      resourceId,
      notificationId,
      notificationType,
      associationState
    ) {
      if (notificationType === 'success' && associationState === true) {
        return this.associateNotificationTemplatesSuccess(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'success' && associationState === false) {
        return this.disassociateNotificationTemplatesSuccess(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'error' && associationState === true) {
        return this.associateNotificationTemplatesError(
          resourceId,
          notificationId
        );
      }

      if (notificationType === 'error' && associationState === false) {
        return this.disassociateNotificationTemplatesError(
          resourceId,
          notificationId
        );
      }

      throw new Error(
        `Unsupported notificationType, associationState combination: ${notificationType}, ${associationState}`
      );
    }
  };

export default NotificationsMixin;
