import Base from '../Base';

const BASE_URLS = {
  playbook: '/jobs/',
  project: '/project_updates/',
  system: '/system_jobs/',
  inventory: '/inventory_updates/',
  command: '/ad_hoc_commands/',
  workflow: '/workflow_jobs/',
};

class Jobs extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/jobs/';
  }

  readDetail(id, type) {
    return this.http.get(`/api/v2${BASE_URLS[type]}${id}/`);
  }

  readJobEvents(id, params = {}) {
    return this.http.get(`${this.baseUrl}${id}/job_events/`, {
      params,
    });
  }
}

export default Jobs;
