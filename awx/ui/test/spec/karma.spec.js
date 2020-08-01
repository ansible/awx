const path = require('path');
const webpackConfig = require('./webpack.spec');

process.env.CHROME_BIN = process.env.CHROME_BIN || require('puppeteer').executablePath();

const SRC_PATH = path.resolve(__dirname, '../../client/src');
const NODE_MODULES = path.resolve(__dirname, '../../node_modules');

module.exports = config => {
    config.set({
        basePath: '../..',
        autoWatch: true,
        colors: true,
        browsers: ['Chrome', 'Firefox'],
        frameworks: ['jasmine'],
        reporters: ['progress', 'junit'],
        files:[
            'client/src/vendor.js',
            path.join(NODE_MODULES, 'angular-mocks/angular-mocks.js'),
            path.join(SRC_PATH, 'app.js'),
            'client/src/**/*.html',
            'test/spec/**/*-test.js',
        ],
        preprocessors: {
            'client/src/vendor.js': 'webpack',
            [path.join(SRC_PATH, 'app.js')]: 'webpack',
            'client/src/**/*.html': 'html2js',
            'test/spec/**/*-test.js': 'webpack'
        },
        webpack: webpackConfig,
        webpackMiddleware: {
            noInfo: true
        },
        junitReporter: {
            outputDir: 'reports',
            outputFile: 'results.spec.xml',
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
