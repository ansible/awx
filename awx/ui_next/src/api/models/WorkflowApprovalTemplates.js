import Base from '../Base';

class WorkflowApprovalTemplates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/workflow_approval_templates/';
  }
}

export default WorkflowApprovalTemplates;
