module.exports = {
    source: {
        src: ['client/src/**/*.js', '*conf.js', '*.config.js', 'Gruntfile.js'],
        options: {
            reporter: 'jslint',
            reporterOutput: 'coverage/jshint.xml',
            jshintrc: true
        }
    },

};
