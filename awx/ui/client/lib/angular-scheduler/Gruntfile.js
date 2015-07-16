module.exports = function(grunt) {

    grunt.initConfig({

        pkg: grunt.file.readJSON('./package.json'),

        jshint: {
            options: {
                jshintrc: '.jshintrc'
            },
            uses_defaults: ['lib/angular-scheduler.js', 'app/js/sampleApp.js']
        },

        uglify: {
            options: {
                banner: '/*! <%= pkg.name %> - v<%= pkg.version %> - ' +
                    '<%= grunt.template.today("yyyy-mm-dd") %> */'
            },
            my_target: {
                files: {
                    'lib/angular-scheduler.min.js': ['lib/angular-scheduler.js']
                }
            }
        },

        less: {
            production: {
                options: {
                    cleancss: true
                },
                files: {
                    "lib/angular-scheduler.min.css": "lib/angular-scheduler.css"
                }
            }
        }
    });
   
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-less');

    grunt.registerTask('default', ['jshint', 'uglify', 'less']);
}
