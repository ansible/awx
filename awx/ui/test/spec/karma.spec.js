const path = require('path');

const SRC_PATH = path.resolve(__dirname, '../../client/src');
const NODE_MODULES = path.resolve(__dirname, '../../node_modules');

const webpackConfig = require('./webpack.spec');

module.exports = function(config) {
    config.set({
        autoWatch: true,
        colors: true,
        browsers: ['Chrome', 'Firefox'],
        coverageReporter: {
            reporters: [
                { type: 'html', subdir: 'html' },
            ]
        },
        frameworks: [
            'jasmine',
        ],
        reporters: ['progress', 'coverage', 'junit'],
        files:[
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
            outputDir: 'coverage',
            outputFile: 'ui-unit-test-results.xml',
            useBrowserName: false
        }
    });
};
