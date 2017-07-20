module.exports = {
    dev: {
        tasks: ['copy:vendor', 'copy:assets', 'copy:partials', 'copy:views', 'copy:languages', 'copy:config'],
    },
    // This concurrent target is intended for development ui builds that do not require raising browser-sync or filesystem polling
    devNoSync: {
        tasks: ['copy:vendor', 'copy:assets', 'copy:partials', 'copy:views', 'copy:languages', 'copy:config', 'less:dev', 'webpack:dev'],
    },
    prod: {
    	tasks: ['newer:copy:vendor', 'newer:copy:assets', 'newer:copy:partials', 'newer:copy:views', 'newer:copy:languages', 'newer:copy:config', 'newer:less:prod']
    },
    watch: {
        tasks: ['watch:css', 'watch:partials', 'watch:views', 'watch:assets', ['webpack:dev', 'watch:config']],
        options: {
            logConcurrentOutput: true
        }
    }
};
