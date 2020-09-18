import Base from '../Base';

class Notifications extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/v2/notifications/';
  }
}

export default Notifications;
