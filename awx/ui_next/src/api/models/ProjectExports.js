import Base from '../Base';

class ProjectExports extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/project_exports/';
  }
}

export default ProjectExports;
