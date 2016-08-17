module.exports = {
    css: {
        files: 'client/**/*.less',
        tasks: ['newer:less:dev']
    },
    partials: {
        files: 'client/src/**/*.html',
        tasks: ['newer:copy:partials']
    },
    assets: {
        files: 'client/assets',
        tasks: ['newer:copy:assets']
    },
    config: {
        files: 'client/src/config.js',
        tasks: ['newer:copy:config']
    }
};
