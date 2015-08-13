module.exports = function(grunt) {
  // Load all grunt tasks.
  require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);

  // Project configuration.
  grunt.initConfig({
    nodeunit: {
      all: ['tests/*_test.js']
    },

    sass: {
      options: {
        style: 'expanded',
        sourcemap: 'none',
        // Increase Sass' default (5) precision to 9 to match Less output.
        //
        // @see https://github.com/twbs/bootstrap-sass#sass-number-precision
        // @see https://github.com/sass/node-sass/issues/673#issue-57581701
        // @see https://github.com/sass/sass/issues/1122
        precision: 9
      },
      dist: {
        files: {
          'docs/css/select2-bootstrap.css': 'src/build.scss',
          'dist/select2-bootstrap.css': 'src/build.scss'
        }
      },
      test: {
        files: {
          'tmp/select2-bootstrap.css': 'src/build.scss'
        }
      }
    },

    cssmin: {
      target: {
        files: {
          'dist/select2-bootstrap.min.css': 'dist/select2-bootstrap.css'
        }
      }
    },

    jshint: {
      all: ['Gruntfile.js', '*.json']
    },

    bump: {
      options: {
        files: [
          'package.json',
          'bower.json'
        ],
        push: false,
        createTag: false
      }
    },

    copy: {
      main: {
        files: [
          {
            src: 'bower_components/bootstrap/dist/css/bootstrap.min.css',
            dest: 'docs/css/bootstrap.min.css',
            expand: false
          },
          {
            src: 'bower_components/bootstrap/dist/js/bootstrap.min.js',
            dest: 'docs/js/bootstrap.min.js',
            expand: false
          },
          {
            src: 'bower_components/respond/dest/respond.min.js',
            dest: 'docs/js/respond.min.js',
            expand: false
          },
          {
            cwd: 'bower_components/bootstrap/dist/fonts',
            src: ['**/*'],
            dest: 'docs/fonts',
            expand: true
          },
          {
            src: 'bower_components/anchor-js/anchor.min.js',
            dest: 'docs/js/anchor.min.js',
            expand: false
          }
        ]
      }
    },

    'gh-pages': {
      options: {
        base: 'docs/_site',
        message: 'Update gh-pages.'
      },
      src: ['**/*']
    },

    jekyll: {
      options: {
        src: 'docs',
        dest: 'docs/_site',
        sourcemaps: false
      },
      build: {
        d: null
      },
      serve: {
        options: {
          serve: true,
          watch: true
        }
      }
    },

    watch: {
      files: 'src/select2-bootstrap.scss',
      tasks: ['sass'],
      options: {
        livereload: true
      }
    }
  });

  // Default tasks.
  grunt.registerTask('build', ['sass', 'cssmin', 'copy', 'jekyll:build']);
  grunt.registerTask('serve', ['jekyll:serve']);
};
