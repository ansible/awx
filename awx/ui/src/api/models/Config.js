import Base from '../Base';

class Config extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/v2/config/';
    this.read = this.read.bind(this);
  }

  readSubscriptions(username, password) {
    return this.http.post(`${this.baseUrl}subscriptions/`, {
      subscriptions_username: username,
      subscriptions_password: password,
    });
  }

  attach(data) {
    return this.http.post(`${this.baseUrl}attach/`, data);
  }
}

export default Config;
