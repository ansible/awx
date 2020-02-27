import Base from '../Base';

class WorkflowJobTemplates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/workflow_job_templates/';
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

  readWebhookKey(id) {
    return this.http.get(`${this.baseUrl}${id}/webhook_key/`);
  }

  createNode(id, data) {
    return this.http.post(`${this.baseUrl}${id}/workflow_nodes/`, data);
  }

  readScheduleList(id, params) {
    return this.http.get(`${this.baseUrl}${id}/schedules/`, { params });
  }
}

export default WorkflowJobTemplates;
