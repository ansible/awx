import Base from '../Base';
import NotificationsMixin from '../mixins/Notifications.mixin';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';
import SchedulesMixin from '../mixins/Schedules.mixin';

class JobTemplates extends SchedulesMixin(
  InstanceGroupsMixin(NotificationsMixin(Base))
) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/job_templates/';

    this.launch = this.launch.bind(this);
    this.readLaunch = this.readLaunch.bind(this);
    this.associateLabel = this.associateLabel.bind(this);
    this.disassociateLabel = this.disassociateLabel.bind(this);
    this.readCredentials = this.readCredentials.bind(this);
    this.readAccessList = this.readAccessList.bind(this);
    this.readAccessOptions = this.readAccessOptions.bind(this);
    this.readWebhookKey = this.readWebhookKey.bind(this);
  }

  launch(id, data) {
    return this.http.post(`${this.baseUrl}${id}/launch/`, data);
  }

  readTemplateOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/`);
  }

  readLaunch(id) {
    return this.http.get(`${this.baseUrl}${id}/launch/`);
  }

  associateLabel(id, label, orgId) {
    return this.http.post(`${this.baseUrl}${id}/labels/`, {
      name: label.name,
      organization: orgId,
    });
  }

  disassociateLabel(id, label) {
    return this.http.post(`${this.baseUrl}${id}/labels/`, {
      id: label.id,
      disassociate: true,
    });
  }

  readCredentials(id, params) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`, {
      params,
    });
  }

  associateCredentials(id, credentialId) {
    return this.http.post(`${this.baseUrl}${id}/credentials/`, {
      id: credentialId,
    });
  }

  disassociateCredentials(id, credentialId) {
    return this.http.post(`${this.baseUrl}${id}/credentials/`, {
      id: credentialId,
      disassociate: true,
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

  readScheduleList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/schedules/`, {
      params,
    });
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

  readWebhookKey(id) {
    return this.http.get(`${this.baseUrl}${id}/webhook_key/`);
  }

  updateWebhookKey(id) {
    return this.http.post(`${this.baseUrl}${id}/webhook_key/`);
  }
}

export default JobTemplates;
