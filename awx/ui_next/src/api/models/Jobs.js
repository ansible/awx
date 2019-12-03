import Base from '../Base';
import RelaunchMixin from '../mixins/Relaunch.mixin';

const BASE_URLS = {
  playbook: '/jobs/',
  project: '/project_updates/',
  system: '/system_jobs/',
  inventory: '/inventory_updates/',
  command: '/ad_hoc_commands/',
  workflow: '/workflow_jobs/',
};

class Jobs extends RelaunchMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/jobs/';
  }

  readDetail(id, type) {
    return this.http.get(`/api/v2${BASE_URLS[type]}${id}/`);
  }

  readEvents(id, type = 'playbook', params = {}) {
    let endpoint;
    if (type === 'playbook') {
      endpoint = `/api/v2${BASE_URLS[type]}${id}/job_events/`;
    } else {
      endpoint = `/api/v2${BASE_URLS[type]}${id}/events/`;
    }
    return this.http.get(endpoint, { params });
  }
}

export default Jobs;
