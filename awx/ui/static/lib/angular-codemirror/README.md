AngularCodeMirror
=================

Incorporate [CodeMirror](http://www.codemirror.net) into your AngularJS app. Presents the editor in a resizable, draggable modal dialog styled with Twitter Bootstrap. Pass in any valid CodeMirror options to make the editor fit your app needs.

Installation:
-------------
bower install angular-codemirror

Example App:
------------
With [Node.js](http://nodejs.org) installed, you can run the sample app locally. Clone the repo to a local projects directory, install package dependencies, and then run with the included server:

    cd projects
    git clone git@github.com:chouseknecht/angular-codemirror.git
    cd angular-codemirror
    bower install
    node ./scripts/web-server.js

Point your browser to http://localhost:8000/app/index.html. Click the code editor link.

How To:
-------
If you installed with Bower, then all the dependencies will exist in bower_components. See app/index.html for a template of how to include all the needed .js and .css files. If you want to install dependencies manually, review bower.json for a list of what's needed.

Check the CodeMirror documentation to see what needs to be included for the mode and options you choose. Again, if you installed with Bower, then everything you need should be found under bower_components. 

Incorporate into your Angular app by following the example in app/js/sampleApp.js.

