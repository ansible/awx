import Base from '../Base';

class WorkflowJobs extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/workflow_jobs/';
  }
}

export default WorkflowJobs;
