const AWX_E2E_URL = process.env.AWX_E2E_URL || 'https://localhost:8043';
const AWX_E2E_USERNAME = process.env.AWX_E2E_USERNAME || 'awx-e2e';
const AWX_E2E_PASSWORD = process.env.AWX_E2E_PASSWORD || 'password';
const AWX_E2E_SELENIUM_HOST = process.env.AWX_E2E_SELENIUM_HOST || 'localhost';
const AWX_E2E_SELENIUM_PORT = process.env.AWX_E2E_SELENIUM_PORT || 4444;
const AWX_E2E_LAUNCH_URL = process.env.AWX_E2E_LAUNCH_URL || AWX_E2E_URL;
const AWX_E2E_TIMEOUT_SHORT = process.env.AWX_E2E_TIMEOUT_SHORT || 1000;
const AWX_E2E_TIMEOUT_MEDIUM = process.env.AWX_E2E_TIMEOUT_MEDIUM || 5000;
const AWX_E2E_TIMEOUT_LONG = process.env.AWX_E2E_TIMEOUT_LONG || 10000;
const AWX_E2E_TIMEOUT_ASYNC = process.env.AWX_E2E_TIMEOUT_ASYNC || 30000;
const AWX_E2E_WORKERS = process.env.AWX_E2E_WORKERS || 0;


module.exports = {
    awxURL: AWX_E2E_URL,
    awxUsername: AWX_E2E_USERNAME,
    awxPassword: AWX_E2E_PASSWORD,
    asyncHookTimeout: AWX_E2E_TIMEOUT_ASYNC,
    longTmeout: AWX_E2E_TIMEOUT_LONG,
    mediumTimeout: AWX_E2E_TIMEOUT_MEDIUM,
    retryAssertionTimeout: AWX_E2E_TIMEOUT_MEDIUM,
    selenium_host: AWX_E2E_SELENIUM_HOST,
    selenium_port: AWX_E2E_SELENIUM_PORT,
    launch_url: AWX_E2E_LAUNCH_URL,
    shortTimeout: AWX_E2E_TIMEOUT_SHORT,
    waitForConditionTimeout: AWX_E2E_TIMEOUT_MEDIUM,
    test_workers: {
        enabled: (AWX_E2E_WORKERS > 0),
        workers: AWX_E2E_WORKERS
    }
};
