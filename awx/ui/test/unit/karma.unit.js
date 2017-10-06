const path = require('path');

const SRC_PATH = path.resolve(__dirname, '../../client/src');

const webpackConfig = require('./webpack.unit');

module.exports = config => {
    config.set({
        basePath: '',
        singleRun: true,
        autoWatch: false,
        colors: true,
        frameworks: ['jasmine'],
        browsers: ['PhantomJS'],
        reporters: ['progress'],
        files: [
            path.join(SRC_PATH, 'vendor.js'),
            path.join(SRC_PATH, 'app.js'),
            path.join(SRC_PATH, '**/*.html'),
            'index.js'
        ],
        plugins: [
            'karma-webpack',
            'karma-jasmine',
            'karma-phantomjs-launcher',
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
        }
    });
};
