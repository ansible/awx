import path from 'path';

import chromedriver from 'chromedriver';

import { test_workers } from './settings.js';


const resolve = location => path.resolve(__dirname, location);


module.exports = {
    src_folders: [resolve('tests')],
    output_folder: resolve('reports'),
    custom_commands_path: resolve('commands'),
    page_objects_path: resolve('objects'),
    globals_path: resolve('settings.js'),
    test_settings: {
        default: {
            test_workers,
            skip_testcases_on_fail: false,
            desiredCapabilities: {
                browserName: 'chrome'
            }
        },
        debug: {
            selenium_port: 9515,
            selenium_host: 'localhost',
            default_path_prefix: '',
            test_workers: { enabled: false },
            globals: {
                before(done) {
                    chromedriver.start();
                    done();
                },
                after(done) {
                    chromedriver.stop();
                    done();
                }
            }
        }
    }
};
