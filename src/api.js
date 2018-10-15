import axios from 'axios';

const API_ROOT = '/api/';
const API_LOGIN = `${API_ROOT}login/`;
const API_LOGOUT = `${API_ROOT}logout/`;
const API_V2 = `${API_ROOT}v2/`;
const API_CONFIG = `${API_V2}config/`;
const API_PROJECTS = `${API_V2}projects/`;
const API_ORGANIZATIONS = `${API_V2}organizations/`;

const CSRF_COOKIE_NAME = 'csrftoken';
const CSRF_HEADER_NAME = 'X-CSRFToken';

class APIClient {
  constructor () {
    this.http = axios.create({
      xsrfCookieName: CSRF_COOKIE_NAME,
      xsrfHeaderName: CSRF_HEADER_NAME,
    });
  }

  isAuthenticated () {
    let authenticated = false;

    const parsed = (`; ${document.cookie}`).split('; userLoggedIn=');

    if (parsed.length === 2) {
      authenticated = parsed.pop().split(';').shift() === 'true';
    }

    return authenticated;
  }

  login (username, password, redirect = API_CONFIG) {
    const un = encodeURIComponent(username);
    const pw = encodeURIComponent(password);
    const next = encodeURIComponent(redirect);

    const data = `username=${un}&password=${pw}&next=${next}`;
    const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };

    return this.http.get(API_LOGIN, { headers })
      .then(() => this.http.post(API_LOGIN, data, { headers }));
  }

  logout () {
    return this.http.get(API_LOGOUT);
  }

  getConfig () {
    return this.http.get(API_CONFIG);
  }

  getProjects () {
    return this.http.get(API_PROJECTS);
  }

  getOrganizations () {
    return this.http.get(API_ORGANIZATIONS);
  }

  getRoot () {
    return this.http.get(API_ROOT);
  }
}

export default new APIClient();
