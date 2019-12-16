import Base from '../Base';
import RelaunchMixin from '../mixins/Relaunch.mixin';

class WorkflowJobs extends RelaunchMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/workflow_jobs/';
  }

  readNodes(id, params) {
    return this.http.get(`${this.baseUrl}${id}/workflow_nodes/`, { params });
  }
}

export default WorkflowJobs;
