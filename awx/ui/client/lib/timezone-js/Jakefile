var fs = require('fs')
  , path = require('path');

namespace('test', function () {

  desc('Sets up tests by downloading the timezone data.');
  task('init', ['updateTzData'], function () {
    complete();
  }, {async: true});

  task('clobberTzData', function () {
    console.log('Removing old timezone data.');
    jake.rmRf('lib/tz');
  });

  desc('Downloads the newest timezone data.');
  task('updateTzData', ['clobberTzData'], function () {
    var cmds = [
      'echo "Downloading new timezone data ..."'
    , 'curl ftp://ftp.iana.org/tz/tzdata-latest.tar.gz ' +
          '-o lib/tz/tzdata-latest.tar.gz'
    , 'echo "Expanding archive ..."'
    , 'tar -xvzf lib/tz/tzdata-latest.tar.gz -C lib/tz'
    ];
    jake.mkdirP('lib/tz');
    jake.exec(cmds, function () {
      console.log('Retrieved new timezone data');
      console.log('Parsing tz...');
      jake.exec('node src/node-preparse.js lib/tz > lib/all_cities.json', function () {
        console.log('Done parsing tz');
        complete();
      }, {printStdout: true, printStderr: true});
    }, {printStdout: true});
  }, {async: true});

  task('run', function () {
    //Comply to 0.8.0 and 0.6.x
    var existsSync = fs.existsSync || path.existsSync;
    if (!existsSync('lib/tz')) {
      fail('No timezone data. Please run "jake test:init".');
    }
    jake.exec(['jasmine-node spec'], function () {
      complete();
    }, {printStdout: true});

  }, {async: true});

  task('cli', ['init', 'run']);

});

desc('Runs the tests.');
task('test', ['test:run'], function () {});

namespace('doc', function () {
  task('generate', ['doc:clobber'], function () {
    var cmd = 'docco src/date.js';
    console.log('Generating docs ...');
    jake.exec([cmd], function () {
      console.log('Done.');
      complete();
    });
  }, {async: true});

  task('clobber', function () {
    var cmd = 'rm -fr ./docs';
    jake.exec([cmd], function () {
      console.log('Clobbered old docs.');
      complete();
    });
  }, {async: true});

});

desc('Generates docs.');
task('doc', ['doc:generate']);

var p = new jake.NpmPublishTask('timezone-js', [
  'Jakefile'
, 'README.md'
, 'package.json'
, 'spec/*'
, 'src/*'
]);

jake.Task['npm:definePackage'].invoke();

