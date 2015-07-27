/*global module*/
module.exports = function (grunt) {
	grunt.initConfig({
    pkg: '<json:package.json>',
    meta: {
      banner: '/*! <%= pkg.name %> - v<%= pkg.version %> - ' + '<%= grunt.template.today("yyyy-mm-dd") %> */'
    },		
    lint: {
			all: ['jstz.js']
		},
		min: {
			dist: {
        src: ['<banner>','jstz.js'],
        dest: 'jstz.min.js'
      }
		}
	});
	
	// Default task.
	grunt.registerTask('default', 'lint min');

};
