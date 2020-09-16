import Base from '../Base';

class ExecutionEnvironments extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/execution_environments/';
  }
}

export default ExecutionEnvironments;
