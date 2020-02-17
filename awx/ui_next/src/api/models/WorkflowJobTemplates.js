import Base from '../Base';

class WorkflowJobTemplates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/workflow_job_templates/';
  }

  readNodes(id, params) {
    return this.http.get(`${this.baseUrl}${id}/workflow_nodes/`, { params });
  }

  createNode(id, data) {
    return this.http.post(`${this.baseUrl}${id}/workflow_nodes/`, data);
  }
}

export default WorkflowJobTemplates;
