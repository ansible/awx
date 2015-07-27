module.exports = function(grunt){
    'use strict';

    // Force use of Unix newlines
    grunt.util.linefeed = '\n';

    // Project configuration.
    grunt.initConfig({
        //Metadata
        pkg: grunt.file.readJSON('package.json'),
        banner: [
            '/*!',
            ' * Datepicker for Bootstrap v<%= pkg.version %> (<%= pkg.homepage %>)',
            ' *',
            ' * Copyright 2012 Stefan Petre',
            ' * Improvements by Andrew Rowls',
            ' * Licensed under the Apache License v2.0 (http://www.apache.org/licenses/LICENSE-2.0)',
            ' */'
        ].join('\n'),

        // Task configuration.
        clean: {
            dist: ['dist', '*-dist.zip']
        },
        jshint: {
            options: {
                jshintrc: 'js/.jshintrc'
            },
            main: {
                src: 'js/bootstrap-datepicker.js'
            },
            locales: {
                src: 'js/locales/*.js'
            },
            gruntfile: {
                options: {
                    jshintrc: 'grunt/.jshintrc'
                },
                src: 'Gruntfile.js'
            }
        },
        jscs: {
            options: {
                config: 'js/.jscsrc'
            },
            main: {
                src: 'js/bootstrap-datepicker.js'
            },
            locales: {
                src: 'js/locales/*.js'
            },
            gruntfile: {
                src: 'Gruntfile.js'
            }
        },
        qunit: {
            all: 'tests/tests.html'
        },
        concat: {
            options: {
                banner: '<%= banner %>',
                stripBanners: true
            },
            main: {
                src: 'js/bootstrap-datepicker.js',
                dest: 'dist/js/<%= pkg.name %>.js'
            }
        },
        uglify: {
            options: {
                preserveComments: 'some'
            },
            main: {
                src: '<%= concat.main.dest %>',
                dest: 'dist/js/<%= pkg.name %>.min.js'
            },
            locales: {
                files: [{
                    expand: true,
                    cwd: 'js/locales/',
                    src: '*.js',
                    dest: 'dist/locales/',
                    rename: function(dest, name){
                        return dest + name.replace(/\.js$/, '.min.js');
                    }
                }]
            }
        },
        less: {
            standalone: {
                files: {
                    'dist/css/<%= pkg.name %>.standalone.css': 'build/build_standalone.less',
                    'dist/css/<%= pkg.name %>3.standalone.css': 'build/build_standalone3.less'
                }
            },
            css: {
                files: {
                    'dist/css/<%= pkg.name %>.css': 'build/build.less',
                    'dist/css/<%= pkg.name %>3.css': 'build/build3.less'
                }
            }
        },
        usebanner: {
            options: {
                position: 'top',
                banner: '<%= banner %>'
            },
            css: {
                files: {
                    src: 'dist/css/*.css'
                }
            }
        },
        cssmin: {
            options: {
                compatibility: 'ie8',
                keepSpecialComments: '*',
                noAdvanced: true
            },
            main: {
                files: {
                    'dist/css/<%= pkg.name %>.min.css': 'dist/css/<%= pkg.name %>.css',
                    'dist/css/<%= pkg.name %>3.min.css': 'dist/css/<%= pkg.name %>3.css'
                }
            },
            standalone: {
                files: {
                    'dist/css/<%= pkg.name %>.standalone.min.css': 'dist/css/<%= pkg.name %>.standalone.css',
                    'dist/css/<%= pkg.name %>3.standalone.min.css': 'dist/css/<%= pkg.name %>3.standalone.css'
                }
            }
        },
        csslint: {
            options: {
                csslintrc: 'less/.csslintrc'
            },
            dist: [
                'dist/css/bootstrap-datepicker.css',
                'dist/css/bootstrap-datepicker3.css',
                'dist/css/bootstrap-datepicker.standalone.css',
                'dist/css/bootstrap-datepicker3.standalone.css'
            ]
        },
        compress: {
            main: {
                options: {
                    archive: '<%= pkg.name %>-<%= pkg.version %>-dist.zip',
                    mode: 'zip',
                    level: 9,
                    pretty: true
                },
                files: [
                    {
                        expand: true,
                        cwd: 'dist/',
                        src: '**'
                    }
                ]
            }
        },
        'string-replace': {
            js: {
                files: [{
                    src: 'js/bootstrap-datepicker.js',
                    dest: 'js/bootstrap-datepicker.js'
                }],
                options: {
                    replacements: [{
                        pattern: '$.fn.datepicker.version =  "1.4.0";',
                        replacement: '$.fn.datepicker.version =  "' + grunt.option('newver') + '";'
                    }]
                }
            },
            npm: {
                files: [{
                    src: 'package.json',
                    dest: 'package.json'
                }],
                options: {
                    replacements: [{
                        pattern: '"version": "1.4.0",',
                        replacement: '"version": "' + grunt.option('newver') + '",'
                    }]
                }
            },
            bower: {
                files: [{
                    src: 'bower.json',
                    dest: 'bower.json'
                }],
                options: {
                    replacements: [{
                        pattern: '"version": "1.4.0",',
                        replacement: '"version": "' + grunt.option('newver') + '",'
                    }]
                }
            }
        }
    });

    // These plugins provide necessary tasks.
    require('load-grunt-tasks')(grunt, {scope: 'devDependencies'});
    require('time-grunt')(grunt);

    // JS distribution task.
    grunt.registerTask('dist-js', ['concat', 'uglify:main', 'uglify:locales']);

    // CSS distribution task.
    grunt.registerTask('less-compile', ['less:standalone', 'less:css']);
    grunt.registerTask('dist-css', ['less-compile', 'cssmin:main', 'cssmin:standalone', 'usebanner']);

    // Full distribution task.
    grunt.registerTask('dist', ['clean:dist', 'dist-js', 'dist-css']);

    // Code check tasks.
    grunt.registerTask('lint-js', 'Lint all js files with jshint and jscs', ['jshint', 'jscs']);
    grunt.registerTask('lint-css', 'Lint all css files', ['dist-css', 'csslint:dist']);
    grunt.registerTask('test', 'Lint files and run unit tests', ['lint-js', /*'lint-css',*/ 'qunit']);

    // Version numbering task.
    // grunt bump-version --newver=X.Y.Z
    grunt.registerTask('bump-version', 'string-replace');

    // Docs task.
    grunt.registerTask('screenshots', 'Rebuilds automated docs screenshots', function(){
        var phantomjs = require('phantomjs').path;

        grunt.file.recurse('docs/_static/screenshots/', function(abspath){
            grunt.file.delete(abspath);
        });

        grunt.file.recurse('docs/_screenshots/', function(abspath, root, subdir, filename){
            if (!/.html$/.test(filename))
                return;
            subdir = subdir || '';

            var outdir = "docs/_static/screenshots/" + subdir,
                outfile = outdir + filename.replace(/.html$/, '.png');

            if (!grunt.file.exists(outdir))
                grunt.file.mkdir(outdir);

            grunt.util.spawn({
                cmd: phantomjs,
                args: ['docs/_screenshots/script/screenshot.js', abspath, outfile]
            });
        });
    });
};
