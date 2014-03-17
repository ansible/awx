angular-scheduler
=================

A UI widget for creating or editing repeating calendar entries. Dynamically injects HTML anwhere in an Angular app. Provides methods for converting schedule entry to and from RRule format, based on the [iCalendar RFC](http://www.ietf.org/rfc/rfc2445.txt).

Intalling
---------

bower install angular-scheduler


Using
-----

Coming soon...


Sample App
----------

An example application is included along with a simple node based web server. With [node](http://nodejs.org) installed, run the following to start the server:

    node ./scripts/web-server.js 8000

Visit the sample by pointing your browser to http://localhost:8000/app/index.html


Contributing
------------
After cloning the repo, install the the bower packages listed in bower.json: 
  
    bower install

Install the npm packages listed in package.json:
    
    node install

Install [Grunt](http://www.gruntjs.com) command line:
    
    npm install -g grunt-cli

From the project root run the grunt command. This will execute the default steps found in Gruntfile.js, which will lint and minify the javascript and css files:

    grunt

You should see output similar to the following:

    Running "jshint:uses_defaults" (jshint) task
    >> 2 files lint free.

    Running "uglify:my_target" (uglify) task
    File "lib/angular-scheduler.min.js" created.

    Running "less:production" (less) task
    File lib/angular-scheduler.min.css created.

Run tests found in the ./tests directory. GetRRule.js provides a set of unit tests. Install [Karma](http://karma-runner.github.io/0.12/index.html), and launch with the folllowing:

    cd test
    karma start

SetRRule.js provides end-to-end tests that run with [Protractor](https://github.com/angular/protractor). Follow the instructions to install protractor and a local selenium server (assuming you don't have access to an existing selenium server). Launch the provided sample app (as described above) in a terminal session. In a separate terminal session launch a local selenium server. The test configuration file expects the web server to run at localhost:8000 and the selenium server to run at localhost:4444. In a third session luanch the tests:
 
Session 1:   
    node ./scripts/web-server.js 8000

Session 2:
    webdriver-manager start

Session 3:
    cd tests
    protractor protractorConf.js


