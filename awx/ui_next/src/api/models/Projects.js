import Base from '../Base';

class Projects extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/projects/';
  }
}

export default Projects;
