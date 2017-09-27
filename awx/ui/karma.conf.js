const webpackTestConfig = require('./build/webpack.test.js');

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
            './client/src/vendor.js',
            './node_modules/angular-mocks/angular-mocks.js',
            './client/src/app.js',
            './tests/**/*-test.js',
            './client/src/**/*.html'
        ],
        preprocessors: {
            './client/src/vendor.js': ['webpack'],
            './client/src/app.js': ['webpack'],
            './tests/**/*-test.js': ['webpack'],
            './client/src/**/*.html': ['html2js']
        },
        webpack: webpackTestConfig,
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
