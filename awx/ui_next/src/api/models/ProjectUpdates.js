import Base from '../Base';

class ProjectUpdates extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/project_updates/';
  }
}

export default ProjectUpdates;
