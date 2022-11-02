import Base from '../Base';

class ActivityStream extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/activity_stream/';
  }
}

export default ActivityStream;
