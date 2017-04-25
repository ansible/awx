module.exports = {
    css: {
        files: 'client/**/*.less',
        tasks: ['less:dev']
    },
    partials: {
        files: [
            'client/components/**/*.partial.html',
            'client/src/**/*.partial.html'
        ],
        tasks: ['newer:copy:partials']
    },
    views: {
        files: 'client/src/**/*.view.html',
        tasks: ['newer:copy:views']
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
