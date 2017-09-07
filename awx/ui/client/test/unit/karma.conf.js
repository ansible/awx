let path = require('path');

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
          './index.js',
          '../../lib/components/**/*.html'
        ],
        plugins: [
            'karma-webpack',
            'karma-jasmine',
            'karma-phantomjs-launcher',
            'karma-ng-html2js-preprocessor'
        ],
        preprocessors: {
            '../../lib/components/**/*.html': 'ng-html2js',
            './index.js': 'webpack'
        },
        ngHtml2JsPreprocessor: {
            moduleName: 'at.test.templates',
            cacheIdFromPath: function (filepath) {
                filepath = filepath.replace(path.join(__dirname, '../../lib'), '');
                return '/static/partials' + filepath;
            }
        },
        webpack: {
            module: {
                loaders: [
                    {
                        test: /\.js$/,
                        loader: 'babel',
                        exclude: /node_modules/
                    },
                    {
                        test: /\.json$/,
                        loader: 'json',
                        exclude: /node_modules/
                    },
                ]
            }
        },
        webpackMiddleware: {
            noInfo: 'errors-only'
        }
    });
};
