import Base from '../Base';

class Schedules extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/schedules/';
  }
}

export default Schedules;
