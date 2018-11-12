import axios from 'axios';

import * as constant from './endpoints';

const CSRF_COOKIE_NAME = 'csrftoken';
const CSRF_HEADER_NAME = 'X-CSRFToken';

const LOGIN_CONTENT_TYPE = 'application/x-www-form-urlencoded';

class APIClient {
  constructor () {
    this.http = axios.create({
      xsrfCookieName: CSRF_COOKIE_NAME,
      xsrfHeaderName: CSRF_HEADER_NAME,
    });
  }

  /* eslint class-methods-use-this: ["error", { "exceptMethods": ["getCookie"] }] */
  getCookie () {
    return document.cookie;
  }

  isAuthenticated () {
    let authenticated = false;

    const parsed = (`; ${this.getCookie()}`).split('; userLoggedIn=');

    if (parsed.length === 2) {
      authenticated = parsed.pop().split(';').shift() === 'true';
    }

    return authenticated;
  }

  async login (username, password, redirect = constant.API_CONFIG) {
    const un = encodeURIComponent(username);
    const pw = encodeURIComponent(password);
    const next = encodeURIComponent(redirect);

    const data = `username=${un}&password=${pw}&next=${next}`;
    const headers = { 'Content-Type': LOGIN_CONTENT_TYPE };

    try {
      await this.http.get(constant.API_LOGIN, { headers });
      await this.http.post(constant.API_LOGIN, data, { headers });
    } catch (err) {
      alert(`There was a problem logging in: ${err}`);
    }
  }

  BaseGet = (endpoint) => this.http.get(endpoint);
}

export default new APIClient();
