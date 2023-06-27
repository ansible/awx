import Base from '../Base';

class Root extends Base {
  constructor(http) {
    super(http);
    this.baseUrl = 'api/';
    this.redirectURL = 'api/v2/config/';
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

  readAssetVariables() {
    // TODO: There's better ways of doing this. Build tools, scripts,
    // automation etc. should relocate this variable file to an importable
    // location in src prior to building. That said, a raw http call
    // works for now.
    return this.http.get('static/media/default.strings.json');
  }
}

export default Root;
