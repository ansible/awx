const normalizeURL = s => s
    .replace(/([^:]\/)\/+/g, '$1') // remove duplicate slashes
    .replace(/\/+$/, ''); // remove trailing slash if there is one

const AWX_E2E_CLUSTER_HOST = process.env.AWX_E2E_CLUSTER_HOST || 'localhost';
const AWX_E2E_CLUSTER_PORT = process.env.AWX_E2E_CLUSTER_PORT || 4444;
const AWX_E2E_CLUSTER_WORKERS = process.env.AWX_E2E_CLUSTER_WORKERS || 0;
const AWX_E2E_PASSWORD = process.env.AWX_E2E_PASSWORD || 'password';
const AWX_E2E_URL = normalizeURL(process.env.AWX_E2E_URL || 'https://localhost:8043');
const AWX_E2E_USERNAME = process.env.AWX_E2E_USERNAME || 'awx-e2e';
const AWX_E2E_TIMEOUT_ASYNC = process.env.AWX_E2E_TIMEOUT_ASYNC || 120000;
const AWX_E2E_TIMEOUT_LONG = process.env.AWX_E2E_TIMEOUT_LONG || 10000;
const AWX_E2E_TIMEOUT_MEDIUM = process.env.AWX_E2E_TIMEOUT_MEDIUM || 5000;
const AWX_E2E_TIMEOUT_SHORT = process.env.AWX_E2E_TIMEOUT_SHORT || 1000;
const AWX_E2E_LAUNCH_URL = normalizeURL(process.env.AWX_E2E_LAUNCH_URL || AWX_E2E_URL);

// Screenshot capture settings
const AWX_E2E_SCREENSHOTS_ENABLED = process.env.AWX_E2E_SCREENSHOTS_ENABLED || false;
const AWX_E2E_SCREENSHOTS_ON_ERROR = process.env.AWX_E2E_SCREENSHOTS_ON_ERROR || true;
const AWX_E2E_SCREENSHOTS_ON_FAILURE = process.env.AWX_E2E_SCREENSHOTS_ON_FAILURE || true;
const AWX_E2E_SCREENSHOTS_PATH = process.env.AWX_E2E_SCREENSHOTS_PATH || '';

module.exports = {
    AWX_E2E_CLUSTER_HOST,
    AWX_E2E_CLUSTER_PORT,
    AWX_E2E_CLUSTER_WORKERS,
    AWX_E2E_LAUNCH_URL,
    AWX_E2E_PASSWORD,
    AWX_E2E_URL,
    AWX_E2E_USERNAME,
    AWX_E2E_TIMEOUT_ASYNC,
    AWX_E2E_TIMEOUT_LONG,
    AWX_E2E_TIMEOUT_MEDIUM,
    AWX_E2E_TIMEOUT_SHORT,
    AWX_E2E_SCREENSHOTS_ENABLED,
    AWX_E2E_SCREENSHOTS_ON_ERROR,
    AWX_E2E_SCREENSHOTS_ON_FAILURE,
    AWX_E2E_SCREENSHOTS_PATH,
};
