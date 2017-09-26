import https from 'https';

import axios from 'axios';

import {
    awxURL,
    awxUsername,
    awxPassword
} from './settings.js';


let authenticated;

const session = axios.create({
    baseURL: awxURL,
    xsrfHeaderName: 'X-CSRFToken',
    xsrfCookieName: 'csrftoken',
    httpsAgent: new https.Agent({
        rejectUnauthorized: false
    })
});


const endpoint = function(location) {

    if (location.indexOf('/api/v') === 0) {
        return location;
    }

    if (location.indexOf('://') > 0) {
        return location;
    }

    return `${awxURL}/api/v2${location}`;
};


const authenticate = function() {
    if (authenticated) {
        return Promise.resolve();
    }

    let uri = endpoint('/authtoken/');

    let credentials = {
        username: awxUsername,
        password: awxPassword
    };

    return session.post(uri, credentials).then(res => {
        session.defaults.headers.Authorization = `Token ${res.data.token}`;
        authenticated = true;
        return res
    });
};


const request = function(method, location, data) {
    let uri = endpoint(location);
    let action = session[method.toLowerCase()];
    
    return authenticate().then(() => action(uri, data)).then(res => {
        console.log([
            res.config.method.toUpperCase(),
            uri,
            res.status,
            res.statusText
        ].join(' '));

        return res; 
    });
};


const get = function(endpoint, data) {
    return request('GET', endpoint, data);
};

const options = function(endpoint) {
    return request('OPTIONS', endpoint);
};

const post = function(endpoint, data) {
    return request('POST', endpoint, data);
};

const patch = function(endpoint, data) {
    return request('PATCH', endpoint, data)
};

const put = function(endpoint, data) {
    return request('PUT', endpoint, data);
};


module.exports = {
    get,
    options,
    post,
    patch,
    put,
    all: axios.all,
    spread: axios.spread
};
