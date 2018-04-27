const path = require('path');

const SRC_PATH = path.resolve(__dirname, '../../client/src');
const NODE_MODULES = path.resolve(__dirname, '../../node_modules');

const webpackConfig = require('./webpack.spec');

module.exports = config => {
    config.set({
        autoWatch: true,
        colors: true,
        browsers: ['Chrome', 'Firefox'],
        frameworks: ['jasmine'],
        reporters: ['progress', 'junit'],
        files:[
            './polyfills.js',
            path.join(SRC_PATH, '**/*.html'),
            path.join(SRC_PATH, 'vendor.js'),
            path.join(NODE_MODULES, 'angular-mocks/angular-mocks.js'),
            path.join(SRC_PATH, 'app.js'),
            '**/*-test.js',
        ],
        preprocessors: {
            [path.join(SRC_PATH, '**/*.html')]: 'html2js',
            [path.join(SRC_PATH, 'vendor.js')]: 'webpack',
            [path.join(SRC_PATH, 'app.js')]: 'webpack',
            '**/*-test.js': 'webpack'
        },
        webpack: webpackConfig,
        webpackMiddleware: {
            noInfo: true
        },
        junitReporter: {
            outputDir: 'reports',
            outputFile: 'results.spec.xml',
            useBrowserName: false
        }
    });
};
