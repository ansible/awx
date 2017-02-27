module.exports = {
    source: {
        src: ['client/src/**/*.js', '*conf.js', '*.config.js', 'Gruntfile.js'],
        options: {
            reporter: require('jshint-stylish'),
            jshintrc: true
        }
    },

};
