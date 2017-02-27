var path = require('path'),
    webpack = require('webpack');

var sauceLaunchers = {
    sl_chrome: {
        base: 'SauceLabs',
        browserName: 'chrome',
        platform: 'Windows 7',
        version: '35'
    },
    sl_firefox: {
        base: 'SauceLabs',
        browserName: 'firefox',
        version: '30'
    },
    sl_ios_safari: {
        base: 'SauceLabs',
        browserName: 'iphone',
        platform: 'OS X 10.9',
        version: '7.1'
    },
    sl_ie_11: {
        base: 'SauceLabs',
        browserName: 'internet explorer',
        platform: 'Windows 8.1',
        version: '11'
    }
}

module.exports = function(config) {
    config.set({
        singleRun: true,
        colors: true,
        logLevel: config.LOG_INFO,
        customLaunchers: sauceLaunchers,
        browsers: Object.keys(sauceLaunchers),
        coverageReporter: {
            reporters: [
                { type: 'html', subdir: 'html' }
            ]
        },
        frameworks: [
            'jasmine',
        ],
        reporters: ['dots', 'saucelabs'],
        files: [
            './client/src/app.js',
            './node_modules/angular-mocks/angular-mocks.js',
            { pattern: './tests/protractor/**/*-test.js' },
        ],
        preprocessors: {
            './client/src/app.js': ['webpack', 'sourcemap'],
            './tests/protractor/**/*-test.js': ['webpack', 'sourcemap'],
        },
        webpack: {
            plugins: [
                // Django-provided definitions
                new webpack.DefinePlugin({
                    $basePath: '/static/'
                }),
                // vendor shims:
                // [{expected_local_var : dependency}, ...]
                new webpack.ProvidePlugin({
                    $: 'jquery',
                    jQuery: 'jquery',
                    'window.jQuery': 'jquery',
                    _: 'lodash',
                    'CodeMirror': 'codemirror',
                    '$.fn.datepicker': 'bootstrap-datepicker'
                })
            ],
            module: {
                loaders: [{
                        test: /\.angular.js$/,
                        loader: 'expose?angular'
                    },
                    {
                        test: /\.js$/,
                        loader: 'babel-loader',
                        include: [path.resolve() + '/tests/'],
                        exclude: '/(node_modules)/',
                        query: {
                            presets: ['es2015']
                        }
                    }, {
                        test: /\.js$/,
                        loader: 'babel-loader',
                        include: [path.resolve() + '/client/src/'],
                        exclude: '/(node_modules)/',
                        query: {
                            presets: ['es2015'],
                            plugins: ['istanbul']
                        }
                    }
                ]
            },
            resolve: {
                root: [],
                modulesDirectory: ['node_modules'],
                alias: {
                    'jquery.resize': path.resolve() + '/node_modules/javascript-detect-element-resize/jquery.resize.js',
                    'select2': path.resolve() + '/node_modules/select2/dist/js/select2.full.js'
                }
            },
            devtool: 'inline-source-map',
            debug: true,
            cache: true
        },
        webpackMiddleware: {
            stats: {
                colors: true
            }
        },
        junitReporter: {
            outputFile: 'coverage/test-results.xml'
        }
    });
};
