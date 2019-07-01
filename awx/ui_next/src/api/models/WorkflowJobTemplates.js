import Base from '../Base';

class WorkflowJobTemplates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/workflow_job_templates/';
  }
}

export default WorkflowJobTemplates;
