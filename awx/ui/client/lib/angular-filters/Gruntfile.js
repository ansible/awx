'use strict';

module.exports = function(grunt) {
  require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);

  // configurable paths
  var yeomanConfig = {
    src: 'src',
    dist: 'dist',
    test: 'test'
  };

  grunt.initConfig({
    yeoman: yeomanConfig,
    pkg: grunt.file.readJSON('package.json'),
    dev: {
      reporters: 'dots'
    },
    karma : {
      options: {
        configFile: 'karma.conf.js',
        singleRun: true
      },
      travis: {
        browsers: ['PhantomJS']
      },
      local: {
        browsers: ['Chrome']
      },
      dev: {
        singleRun: false
      }
    },
    jshint: {
      options: {
        jshintrc: '.jshintrc'
      },
      src: [
        'Gruntfile.js',
        '<%= yeoman.src %>/**/*.js'
      ],
      test: {
        src: ['<%= yeoman.test %>/**/*.js'],
        options: {
          jshintrc: 'test/.jshintrc'
        }
      }
    },
    meta: {
      banner: '/**\n' + ' * <%= pkg.description %>\n' +
        ' * @version v<%= pkg.version %> - <%= grunt.template.today("yyyy-mm-dd") %>\n' +
        ' * @author <%= pkg.author.name %>\n' +
        ' * @link <%= pkg.homepage %>\n' +
        ' * @license <%= _.pluck(pkg.licenses, "type").join(", ") %>\n**/\n\n'
    },
    clean: {
      dist: {
        files: [{
          dot: true,
          src: [
            '<%= yeoman.dist %>/*',
            '!<%= yeoman.dist %>/.git*'
          ]
        }]
      },
      temp: {
        src: ['<%= yeoman.dist %>/.temp']
      }
    },
    ngmin: {
      dist: {
        expand: true,
        cwd: '<%= yeoman.src %>',
        src: ['**/*.js'],
        dest: '<%= yeoman.dist %>/.temp'
      }
    },
    concat: {
      options: {
        banner: '<%= meta.banner %>\'use strict\';\n',
        process: function(src, filepath) {
          return '// Source: ' + filepath + '\n' +
            src.replace(/(^|\n)[ \t]*('use strict'|"use strict");?\s*/g, '$1');
        }
      },
      build: {
        src: ['common/*.js', '<%= yeoman.dist %>/.temp/**/*.js'],
        dest: '<%= yeoman.dist %>/<%= pkg.name %>.js'
      }
    },
    uglify: {
      options: {
        banner: '<%= meta.banner %>'
      },
      build: {
        src: ['<%= yeoman.dist %>/<%= pkg.name %>.js'],
        dest: '<%= yeoman.dist %>/<%= pkg.name %>.min.js'
      }
    }
  });

  grunt.registerTask('test', ['jshint', 'karma:local']);
  grunt.registerTask('test-travis', ['jshint', 'karma:travis']);

  grunt.registerTask('build', ['clean', 'ngmin', 'concat', 'uglify', 'clean:temp']);
  grunt.registerTask('travis', ['test-travis', 'build']);
  grunt.registerTask('default', ['test-travis', 'build']);

};