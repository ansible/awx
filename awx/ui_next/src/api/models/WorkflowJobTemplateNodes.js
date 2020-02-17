import Base from '../Base';

class WorkflowJobTemplateNodes extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/workflow_job_template_nodes/';
  }

  createApprovalTemplate(id, data) {
    return this.http.post(
      `${this.baseUrl}${id}/create_approval_template/`,
      data
    );
  }

  associateSuccessNode(id, idToAssociate) {
    return this.http.post(`${this.baseUrl}${id}/success_nodes/`, {
      id: idToAssociate,
    });
  }

  associateFailureNode(id, idToAssociate) {
    return this.http.post(`${this.baseUrl}${id}/failure_nodes/`, {
      id: idToAssociate,
    });
  }

  associateAlwaysNode(id, idToAssociate) {
    return this.http.post(`${this.baseUrl}${id}/always_nodes/`, {
      id: idToAssociate,
    });
  }

  disassociateSuccessNode(id, idToDissociate) {
    return this.http.post(`${this.baseUrl}${id}/success_nodes/`, {
      id: idToDissociate,
      disassociate: true,
    });
  }

  disassociateFailuresNode(id, idToDissociate) {
    return this.http.post(`${this.baseUrl}${id}/failure_nodes/`, {
      id: idToDissociate,
      disassociate: true,
    });
  }

  disassociateAlwaysNode(id, idToDissociate) {
    return this.http.post(`${this.baseUrl}${id}/always_nodes/`, {
      id: idToDissociate,
      disassociate: true,
    });
  }

  readCredentials(id) {
    return this.http.get(`${this.baseUrl}${id}/credentials/`);
  }
}

export default WorkflowJobTemplateNodes;
