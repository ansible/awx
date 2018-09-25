import axios from 'axios';

const API_ROOT = '/api/';
const API_LOGIN = `${API_ROOT}login/`;
const API_V2 = `${API_ROOT}v2/`;
const API_CONFIG = `${API_V2}config/`;
const API_PROJECTS = `${API_V2}projects/`;
const API_ORGANIZATIONS = `${API_V2}organizations/`;

const CSRF_COOKIE_NAME = 'csrftoken';
const CSRF_HEADER_NAME = 'X-CSRFToken';

const http = axios.create({
  xsrfCookieName: CSRF_COOKIE_NAME,
  xsrfHeaderName: CSRF_HEADER_NAME,
});

let authenticated = false; // temporary

class APIClient {
  isAuthenticated() {
    return authenticated;
  }
  login(username, password, redirect = API_CONFIG) {
    const un = encodeURIComponent(username);
    const pw = encodeURIComponent(password);
    const next = encodeURIComponent(redirect);

    const data = `username=${un}&password=${pw}&next=${next}`;
    const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };

    return http.get(API_LOGIN, { headers })
      .then(() => http.post(API_LOGIN, data, { headers }))
      .then(res => {
        authenticated = true; // temporary

        return res;
      })
  }

  logout() {
    return http.delete(API_LOGIN);
  }

  getProjects() {
    return http.get(API_PROJECTS);
  }

  getOrganizations() {
    return http.get(API_ORGANIZATIONS);
  }
};

export default new APIClient();
