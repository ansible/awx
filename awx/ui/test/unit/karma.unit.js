const path = require('path');
const webpackConfig = require('../../build/webpack.test.js');

process.env.CHROME_BIN = process.env.CHROME_BIN || require('puppeteer').executablePath();

const SRC_PATH = path.resolve(__dirname, '../../client/src');

module.exports = config => {
    config.set({
        basePath: '',
        singleRun: true,
        autoWatch: false,
        colors: true,
        frameworks: ['jasmine'],
        browsers: ['chromeHeadless'],
        reporters: ['progress', 'junit'],
        files: [
            path.join(SRC_PATH, 'vendor.js'),
            path.join(SRC_PATH, 'app.js'),
            path.join(SRC_PATH, '**/*.html'),
            'index.js'
        ],
        plugins: [
            'karma-webpack',
            'karma-jasmine',
            'karma-junit-reporter',
            'karma-chrome-launcher',
            'karma-html2js-preprocessor'
        ],
        preprocessors: {
            [path.join(SRC_PATH, 'vendor.js')]: 'webpack',
            [path.join(SRC_PATH, 'app.js')]: 'webpack',
            [path.join(SRC_PATH, '**/*.html')]: 'html2js',
            'index.js': 'webpack'
        },
        webpack: webpackConfig,
        webpackMiddleware: {
            noInfo: 'errors-only'
        },
        junitReporter: {
            outputDir: 'reports',
            outputFile: 'results.unit.xml',
            useBrowserName: false
        },
        customLaunchers: {
            chromeHeadless: {
                base: 'Chrome',
                flags: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--headless',
                    '--disable-gpu',
                    '--remote-debugging-port=9222',
                ],
            },
        },
    });
};
