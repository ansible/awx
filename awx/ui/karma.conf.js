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
            './client/src/app.js',
            './node_modules/angular-mocks/angular-mocks.js',
            { pattern: './tests/**/*-test.js' },
            'client/src/**/*.html'
        ],
        preprocessors: {
            './client/src/vendor.js': ['webpack', 'sourcemap'],
            './client/src/app.js': ['webpack', 'sourcemap'],
            './tests/**/*-test.js': ['webpack', 'sourcemap'],
            'client/src/**/*.html': ['html2js']
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
