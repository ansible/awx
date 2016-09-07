var path = require('path'),
    webpack = require('webpack');

module.exports = function(config) {
    config.set({
        autoWatch: true,
        colors: true,
        logLevel: config.LOG_INFO,
        browsers: ['Chrome', 'Firefox'],
        coverageReporter: {
            reporters: [
                { type: 'html', subdir: 'html' }
            ]
        },
        frameworks: [
            'jasmine',
        ],
        reporters: ['progress', 'coverage'],
        files: [
            './client/src/app.js',
            './node_modules/angular-mocks/angular-mocks.js',
            { pattern: './tests/**/*-test.js' },
        ],
        preprocessors: {
            './client/src/app.js': ['webpack', 'sourcemap'],
            './tests/**/*-test.js': ['webpack', 'sourcemap'],
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
