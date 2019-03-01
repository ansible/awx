const API_ROOT = '/api/';
const API_LOGIN = `${API_ROOT}login/`;
const API_LOGOUT = `${API_ROOT}logout/`;
const API_V2 = `${API_ROOT}v2/`;
const API_CONFIG = `${API_V2}config/`;
const API_ORGANIZATIONS = `${API_V2}organizations/`;
const API_INSTANCE_GROUPS = `${API_V2}instance_groups/`;
const API_USERS = `${API_V2}users/`;

const LOGIN_CONTENT_TYPE = 'application/x-www-form-urlencoded';

class APIClient {
  static getCookie () {
    return document.cookie;
  }

  constructor (httpAdapter) {
    this.http = httpAdapter;
  }

  isAuthenticated () {
    const cookie = this.constructor.getCookie();
    const parsed = (`; ${cookie}`).split('; userLoggedIn=');

    let authenticated = false;

    if (parsed.length === 2) {
      authenticated = parsed.pop().split(';').shift() === 'true';
    }

    return authenticated;
  }

  async login (username, password, redirect = API_CONFIG) {
    const un = encodeURIComponent(username);
    const pw = encodeURIComponent(password);
    const next = encodeURIComponent(redirect);

    const data = `username=${un}&password=${pw}&next=${next}`;
    const headers = { 'Content-Type': LOGIN_CONTENT_TYPE };

    await this.http.get(API_LOGIN, { headers });
    const response = await this.http.post(API_LOGIN, data, { headers });

    return response;
  }

  logout () {
    return this.http.get(API_LOGOUT);
  }

  getRoot () {
    return this.http.get(API_ROOT);
  }

  getConfig () {
    return this.http.get(API_CONFIG);
  }

  getOrganizations (params = {}) {
    return this.http.get(API_ORGANIZATIONS, { params });
  }

  createOrganization (data) {
    return this.http.post(API_ORGANIZATIONS, data);
  }

  getOrganzationAccessList (id, params = {}) {
    const endpoint = `${API_ORGANIZATIONS}${id}/access_list/`;

    return this.http.get(endpoint, { params });
  }

  getOrganizationDetails (id) {
    const endpoint = `${API_ORGANIZATIONS}${id}/`;

    return this.http.get(endpoint);
  }

  getOrganizationInstanceGroups (id, params = {}) {
    const endpoint = `${API_ORGANIZATIONS}${id}/instance_groups/`;

    return this.http.get(endpoint, { params });
  }

  getOrganizationNotifications (id, params = {}) {
    const endpoint = `${API_ORGANIZATIONS}${id}/notification_templates/`;

    return this.http.get(endpoint, { params });
  }

  getOrganizationNotificationSuccess (id, params = {}) {
    const endpoint = `${API_ORGANIZATIONS}${id}/notification_templates_success/`;

    return this.http.get(endpoint, { params });
  }

  getOrganizationNotificationError (id, params = {}) {
    const endpoint = `${API_ORGANIZATIONS}${id}/notification_templates_error/`;

    return this.http.get(endpoint, { params });
  }

  createOrganizationNotificationSuccess (id, data) {
    const endpoint = `${API_ORGANIZATIONS}${id}/notification_templates_success/`;

    return this.http.post(endpoint, data);
  }

  createOrganizationNotificationError (id, data) {
    const endpoint = `${API_ORGANIZATIONS}${id}/notification_templates_error/`;

    return this.http.post(endpoint, data);
  }

  getInstanceGroups (params) {
    return this.http.get(API_INSTANCE_GROUPS, { params });
  }

  createInstanceGroups (url, id) {
    return this.http.post(url, { id });
  }

  getUserRoles (id) {
    const endpoint = `${API_USERS}${id}/roles/`;

    return this.http.get(endpoint);
  }
}

export default APIClient;
