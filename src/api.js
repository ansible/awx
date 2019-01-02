import axios from 'axios';

import {
  API_CONFIG,
  API_LOGIN,
  API_ROOT,
} from './endpoints';

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

  getRoot () {
    return this.http.get(API_ROOT);
  }

  async login (username, password, redirect = API_CONFIG) {
    const un = encodeURIComponent(username);
    const pw = encodeURIComponent(password);
    const next = encodeURIComponent(redirect);

    const data = `username=${un}&password=${pw}&next=${next}`;
    const headers = { 'Content-Type': LOGIN_CONTENT_TYPE };

    await this.http.get(API_LOGIN, { headers });
    await this.http.post(API_LOGIN, data, { headers });
  }

  get = (endpoint, params = {}) => this.http.get(endpoint, { params });

  post = (endpoint, data) => this.http.post(endpoint, data);
}

export default new APIClient();
