import Base from '../Base';
import RunnableMixin from '../mixins/Runnable.mixin';

class WorkflowJobs extends RunnableMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/workflow_jobs/';
  }

  readNodes(id, params) {
    return this.http.get(`${this.baseUrl}${id}/workflow_nodes/`, { params });
  }

  readCredentials(id) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`);
  }
}

export default WorkflowJobs;
