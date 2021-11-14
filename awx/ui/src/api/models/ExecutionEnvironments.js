import Base from '../Base';

class ExecutionEnvironments extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/execution_environments/';
  }

  readUnifiedJobTemplates(id, params) {
    return this.http.get(`${this.baseUrl}${id}/unified_job_templates/`, {
      params,
    });
  }

  readUnifiedJobTemplateOptions(id) {
    return this.http.options(`${this.baseUrl}${id}/unified_job_templates/`);
  }
}

export default ExecutionEnvironments;
