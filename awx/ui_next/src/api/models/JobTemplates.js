import Base from '../Base';
import InstanceGroupsMixin from '../mixins/InstanceGroups.mixin';

class JobTemplates extends InstanceGroupsMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/job_templates/';

    this.launch = this.launch.bind(this);
    this.readLaunch = this.readLaunch.bind(this);
    this.associateLabel = this.associateLabel.bind(this);
    this.disassociateLabel = this.disassociateLabel.bind(this);
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
    return this.http.post(`${this.baseUrl}${id}/labels/`, label);
  }

  generateLabel(orgId, label) {
    return this.http.post(`${this.baseUrl}${orgId}/labels/`, label);
  }
}

export default JobTemplates;
