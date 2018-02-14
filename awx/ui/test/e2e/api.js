import https from 'https';

import axios from 'axios';

import {
    AWX_E2E_URL,
    AWX_E2E_USERNAME,
    AWX_E2E_PASSWORD
} from './settings';

let authenticated;

const session = axios.create({
    baseURL: AWX_E2E_URL,
    xsrfHeaderName: 'X-CSRFToken',
    xsrfCookieName: 'csrftoken',
    httpsAgent: new https.Agent({
        rejectUnauthorized: false
    })
});

const getEndpoint = location => {
    if (location.indexOf('/api/v') === 0 || location.indexOf('://') > 0) {
        return location;
    }

    return `${AWX_E2E_URL}/api/v2${location}`;
};

const authenticate = () => {
    if (authenticated) {
        return Promise.resolve();
    }

    const uri = getEndpoint('/authtoken/');

    const credentials = {
        username: AWX_E2E_USERNAME,
        password: AWX_E2E_PASSWORD
    };

    return session.post(uri, credentials).then(res => {
        session.defaults.headers.Authorization = `Token ${res.data.token}`;
        authenticated = true;

        return res;
    });
};

const request = (method, location, data) => {
    const uri = getEndpoint(location);
    const action = session[method.toLowerCase()];

    return authenticate()
        .then(() => action(uri, data))
        .then(res => {
            console.log([ // eslint-disable-line no-console
                res.config.method.toUpperCase(),
                uri,
                res.status,
                res.statusText
            ].join(' '));

            return res;
        });
};

const get = (endpoint, data) => request('GET', endpoint, data);
const options = endpoint => request('OPTIONS', endpoint);
const post = (endpoint, data) => request('POST', endpoint, data);
const patch = (endpoint, data) => request('PATCH', endpoint, data);
const put = (endpoint, data) => request('PUT', endpoint, data);

module.exports = {
    get,
    options,
    post,
    patch,
    put,
};
