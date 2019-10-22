import Base from '../Base';
import NotificationsMixin from '../mixins/Notifications.mixin';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class JobTemplates extends InstanceGroupsMixin(NotificationsMixin(Base)) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/job_templates/';

    this.launch = this.launch.bind(this);
    this.readLaunch = this.readLaunch.bind(this);
    this.associateLabel = this.associateLabel.bind(this);
    this.disassociateLabel = this.disassociateLabel.bind(this);
    this.readCredentials = this.readCredentials.bind(this);
    this.generateLabel = this.generateLabel.bind(this);
  }

  launch(id, data) {
    return this.http.post(`${this.baseUrl}${id}/launch/`, data);
  }

  readLaunch(id) {
    return this.http.get(`${this.baseUrl}${id}/launch/`);
  }

  associateLabel(id, label) {
    return this.http.post(`${this.baseUrl}${id}/labels/`, label);
  }

  disassociateLabel(id, label) {
    return this.http.post(`${this.baseUrl}${id}/labels/`, {
      id: label.id,
      disassociate: true,
    });
  }

  generateLabel(id, label, orgId) {
    return this.http.post(`${this.baseUrl}${id}/labels/`, {
      name: label.name,
      organization: orgId,
    });
  }

  readCredentials(id, params) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`, { params });
  }

  associateCredentials(id, credential) {
    return this.http.post(`${this.baseUrl}${id}/credentials/`, { id: credential });
  }

  disassociateCredentials(id, credential) {
    return this.http.post(`${this.baseUrl}${id}/credentials/`, { id: credential, disassociate: true  });
  }
}

export default JobTemplates;
