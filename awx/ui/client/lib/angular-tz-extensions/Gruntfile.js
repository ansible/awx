module.exports = function(grunt) {

    grunt.initConfig({

        pkg: grunt.file.readJSON('./package.json'),

        jshint: {
            options: {
                jshintrc: '.jshintrc'
            },
            uses_defaults: ['lib/angular-tz-extensions.js']
        },

        uglify: {
            options: {
                banner: '/*! <%= pkg.name %> - v<%= pkg.version %> - ' +
                    '<%= grunt.template.today("yyyy-mm-dd") %> */'
            },
            my_target: {
                files: {
                    'lib/angular-tz-extensions.min.js': ['lib/angular-tz-extensions.js']
                }
            }
        }

    });
   
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-uglify');

    grunt.registerTask('default', ['jshint', 'uglify']);
}
