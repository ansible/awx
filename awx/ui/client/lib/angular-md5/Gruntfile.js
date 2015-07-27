'use strict';

module.exports = function(grunt) {

  require('load-grunt-tasks')(grunt);
  require('time-grunt')(grunt);

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    bwr: grunt.file.readJSON('bower.json'),
    nodeunit: {
      files: ['test/**/*_test.js']
    },
    jshint: {
      options: {
        jshintrc: '.jshintrc'
      },
      gruntfile: {
        src: 'Gruntfile.js'
      },
      lib: {
        src: ['<%= bwr.name %>']
      },
      test: {
        src: ['test/**/*.js']
      }
    },
    clean: ['.tmp/'],
    concat: {
      dist:{}
    },
    ngmin: {
      dist: {
        files: {
          '.tmp/<%= bwr.name %>.js': ['./lib/index.js', './lib/*/*.js']
        }
      }
    },
    uglify: {
      options: {
        report: 'min',
        enclose: {
          'this': 'window',
          'this.angular': 'angular',
          'void 0': 'undefined'
        },
        banner: '/*\n  <%= bwr.name %> - v<%= bwr.version %> \n  ' +
          '<%= grunt.template.today("yyyy-mm-dd") %>\n*/\n'+
        '',
      },
      dist: {
        options: {
          beautify: false,
          mangle: true,
          compress: {
            global_defs: {
              'DEBUG': false
            },
            dead_code: true
          },
          sourceMap: '<%= bwr.name %>.min.js.map'
        },
        files: {
          '<%= bwr.name %>.min.js': ['./lib/index.js', './lib/*/*.js']
        }
      },
      src: {
        options: {
          beautify: true,
          mangle: false,
          compress: false
        },
        files: {
          '<%= bwr.name %>.js': ['./lib/index.js', './lib/*/*.js']
        }
      },
      buildDist: {
        options: {
          beautify: false,
          mangle: true,
          compress: {
            global_defs: {
              'DEBUG': false
            },
            dead_code: true
          },
          sourceMap: '<%= bwr.name %>.min.js.map'
        },
        files: {
          '<%= bwr.name %>.min.js': '.tmp/<%= bwr.name %>.js'
        }
      },
      buildSrc: {
        options: {
          beautify: {
            indent_level: 2,
            beautify: true
          },
          mangle: false,
          compress: false
        },
        files: {
          '<%= bwr.name %>.js': '.tmp/<%= bwr.name %>.js'
        }
      }

    }
  });

  // Testing task
  grunt.registerTask('test', [
  ]);

  // Build task
  grunt.registerTask('build', [
    'clean',
    'concat',
    'ngmin:dist',
    'uglify:buildSrc',
    'uglify:buildDist'
  ]);

  // Default task
  grunt.registerTask('default', [
    'build'
  ]);

};
