exports.compileScss = function(test){
  var grunt = require('grunt'),
      fs = require('fs'),
      jsdiff = require('diff'),
      t = test,
      filename = 'select2-bootstrap.css',
      patchfile = 'tests/support/scss.patch',

      child = grunt.util.spawn({
        cmd: 'grunt',
        args: ['sass:test']
      }, function() {
        var readFile = function(name) { return fs.readFileSync(name, {encoding: 'utf8'}) },
            orig = readFile('dist/'+filename),
            generated = readFile('tmp/'+filename),
            patch = readFile(patchfile),
            diff = jsdiff.createPatch(filename, orig, generated);

        // Save the output for future tests.
        // fs.writeFileSync(patchfile, diff);

        t.equal(patch, diff);
        t.done();
      });
};
