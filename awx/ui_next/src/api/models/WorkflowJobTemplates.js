import Base from '../Base';
import SchedulesMixin from '../mixins/Schedules.mixin';
import NotificationsMixin from '../mixins/Notifications.mixin';

class WorkflowJobTemplates extends SchedulesMixin(NotificationsMixin(Base)) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/workflow_job_templates/';
  }

  readWebhookKey(id) {
    return this.http.get(`${this.baseUrl}${id}/webhook_key/`);
  }

  readWorkflowJobTemplateOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/`);
  }

  updateWebhookKey(id) {
    return this.http.post(`${this.baseUrl}${id}/webhook_key/`);
  }

  associateLabel(id, label, orgId) {
    return this.http.post(`${this.baseUrl}${id}/labels/`, {
      name: label.name,
      organization: orgId,
    });
  }

  createNode(id, data) {
    return this.http.post(`${this.baseUrl}${id}/workflow_nodes/`, data);
  }

  disassociateLabel(id, label) {
    return this.http.post(`${this.baseUrl}${id}/labels/`, {
      id: label.id,
      disassociate: true,
    });
  }

  launch(id, data) {
    return this.http.post(`${this.baseUrl}${id}/launch/`, data);
  }

  readLaunch(id) {
    return this.http.get(`${this.baseUrl}${id}/launch/`);
  }

  readNodes(id, params) {
    return this.http.get(`${this.baseUrl}${id}/workflow_nodes/`, {
      params,
    });
  }

  readAccessList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/access_list/`, {
      params,
    });
  }

  readAccessOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/access_list/`);
  }

  readSurvey(id) {
    return this.http.get(`${this.baseUrl}${id}/survey_spec/`);
  }

  updateSurvey(id, survey) {
    return this.http.post(`${this.baseUrl}${id}/survey_spec/`, survey);
  }

  destroySurvey(id) {
    return this.http.delete(`${this.baseUrl}${id}/survey_spec/`);
  }

  readNotificationTemplatesApprovals(id, params) {
    return this.http.get(
      `${this.baseUrl}${id}/notification_templates_approvals/`,
      {
        params,
      }
    );
  }

  associateNotificationTemplatesApprovals(resourceId, notificationId) {
    return this.http.post(
      `${this.baseUrl}${resourceId}/notification_templates_approvals/`,
      {
        id: notificationId,
      }
    );
  }

  disassociateNotificationTemplatesApprovals(resourceId, notificationId) {
    return this.http.post(
      `${this.baseUrl}${resourceId}/notification_templates_approvals/`,
      {
        id: notificationId,
        disassociate: true,
      }
    );
  }
}

export default WorkflowJobTemplates;
