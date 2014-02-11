module.exports = function(grunt) {

    grunt.initConfig({

        pkg: grunt.file.readJSON('./package.json'),

        jshint: {
            options: {
                jshintrc: '.jshintrc'
            },
            uses_defaults: ['awx/ui/static/js/*','awx/ui/static/lib/ansible/*', '!awx/ui/static/js/awx-min.js']
        },

	uglify: {
            options: {
                banner: '/*! <%= pkg.name %> - v<%= pkg.version %> - ' +
                    '<%= grunt.template.today("yyyy-mm-dd") %> */'
            }, 
            my_target: {
                files: {
                    'awx/ui/static/js/awx-min.js': ['awx/ui/static/js/**/*.js', 'awx/ui/static/lib/ansible/*.js', 
                        '!awx/ui/static/js/awx-min.js']
                }
            }
        }
    });
   
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-uglify');

    grunt.registerTask('default', ['jshint', 'uglify']);
}
