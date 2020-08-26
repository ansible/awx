import Base from '../Base';
import RelaunchMixin from '../mixins/Relaunch.mixin';

const getBaseURL = type => {
  switch (type) {
    case 'playbook':
    case 'job':
      return '/jobs/';
    case 'project':
    case 'project_update':
      return '/project_updates/';
    case 'system':
    case 'system_job':
      return '/system_jobs/';
    case 'inventory':
    case 'inventory_update':
      return '/inventory_updates/';
    case 'command':
    case 'ad_hoc_command':
      return '/ad_hoc_commands/';
    case 'workflow':
    case 'workflow_job':
      return '/workflow_jobs/';
    default:
      throw new Error('Unable to find matching job type');
  }
};

class Jobs extends RelaunchMixin(Base) {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/jobs/';
  }

  cancel(id, type) {
    return this.http.post(`/api/v2${getBaseURL(type)}${id}/cancel/`);
  }

  readDetail(id, type) {
    return this.http.get(`/api/v2${getBaseURL(type)}${id}/`);
  }

  readEvents(id, type = 'playbook', params = {}) {
    let endpoint;
    if (type === 'playbook') {
      endpoint = `/api/v2${getBaseURL(type)}${id}/job_events/`;
    } else {
      endpoint = `/api/v2${getBaseURL(type)}${id}/events/`;
    }
    return this.http.get(endpoint, { params });
  }
}

export default Jobs;
