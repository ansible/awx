module.exports = config => {
    config.set({
        basePath: '..',
        singleRun: true,
        autoWatch: true,
        frameworks: ['jasmine'],
        browsers: ['PhantomJS'],
        reporters: ['mocha'],
        files: [
            'components/**/*.js',
            'test/*.spec.js'
        ],
        plugins: [
            'karma-jasmine'
            'karma-mocha-reporter'
        ],
    });
};
