module.exports = {
    dev: {
        tasks: ['copy:vendor', 'copy:assets', 'copy:partials', 'copy:languages', 'copy:config', 'less:dev'],
    },
    prod: {
    	tasks: ['newer:copy:vendor', 'newer:copy:assets', 'newer:copy:partials', 'newer:copy:languages', 'newer:copy:config', 'newer:less:prod']
    },
    watch: {
        tasks: ['watch:css', 'watch:partials', 'watch:assets', ['webpack:dev', 'watch:config']],
        options: {
            logConcurrentOutput: true
        }
    }
};
