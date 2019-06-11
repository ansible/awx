import path from 'path';

import chromedriver from 'chromedriver';

import {
    AWX_E2E_CLUSTER_HOST,
    AWX_E2E_CLUSTER_PORT,
    AWX_E2E_CLUSTER_WORKERS,
    AWX_E2E_LAUNCH_URL,
    AWX_E2E_TIMEOUT_ASYNC,
    AWX_E2E_TIMEOUT_MEDIUM,
    AWX_E2E_SCREENSHOTS_ENABLED,
    AWX_E2E_SCREENSHOTS_ON_ERROR,
    AWX_E2E_SCREENSHOTS_ON_FAILURE,
    AWX_E2E_SCREENSHOTS_PATH,
} from './settings';

const resolve = location => path.resolve(__dirname, location);

module.exports = {
    src_folders: [resolve('tests')],
    output_folder: resolve('reports'),
    custom_commands_path: resolve('commands'),
    page_objects_path: resolve('objects'),
    test_settings: {
        default: {
            selenium_host: 'localhost',
            selenium_port: 9515,
            default_path_prefix: '',
            desiredCapabilities: {
                browserName: 'chrome',
                chromeOptions: {
                    w3c: false,
                    args: [
                        'window-size=1024,768'
                    ]
                }
            },
            test_workers: { enabled: false },
            globals: {
                launch_url: AWX_E2E_LAUNCH_URL,
                retryAssertionTimeout: AWX_E2E_TIMEOUT_MEDIUM,
                waitForConditionTimeout: AWX_E2E_TIMEOUT_MEDIUM,
                asyncHookTimeout: AWX_E2E_TIMEOUT_ASYNC,
                before (done) {
                    chromedriver.start(['--port=9515']);
                    done();
                },
                after (done) {
                    chromedriver.stop();
                    done();
                }
            },
            screenshots: {
                enabled: AWX_E2E_SCREENSHOTS_ENABLED,
                on_error: AWX_E2E_SCREENSHOTS_ON_ERROR,
                on_failure: AWX_E2E_SCREENSHOTS_ON_FAILURE,
                path: AWX_E2E_SCREENSHOTS_PATH,
            }
        },
        headless: {
            desiredCapabilities: {
                browserName: 'chrome',
                chromeOptions: {
                    w3c: false,
                    args: [
                        'headless',
                        'disable-web-security',
                        'ignore-certificate-errors',
                        'no-sandbox',
                        'disable-gpu'
                    ]
                }
            },
        },
        // Note: These are environment-specific overrides to the default
        // test settings defined above.
        cluster: {
            selenium_host: AWX_E2E_CLUSTER_HOST,
            selenium_port: AWX_E2E_CLUSTER_PORT,
            default_path_prefix: '/wd/hub',
            test_workers: {
                enabled: (AWX_E2E_CLUSTER_WORKERS > 0),
                workers: AWX_E2E_CLUSTER_WORKERS
            },
            globals: { before: {}, after: {} }
        }
    }
};
