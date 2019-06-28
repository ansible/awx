import Base from '../Base';

class Root extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = '/api/';
    this.redirectURL = '/api/v2/config/';
  }

  async login(username, password, redirect = this.redirectURL) {
    const loginUrl = `${this.baseUrl}login/`;
    const un = encodeURIComponent(username);
    const pw = encodeURIComponent(password);
    const next = encodeURIComponent(redirect);

    const data = `username=${un}&password=${pw}&next=${next}`;
    const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };

    await this.http.get(loginUrl, { headers });
    const response = await this.http.post(loginUrl, data, { headers });

    return response;
  }

  logout() {
    return this.http.get(`${this.baseUrl}logout/`);
  }
}

export default Root;
