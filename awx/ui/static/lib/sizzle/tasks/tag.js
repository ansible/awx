"use strict";

var exec = require( "child_process" ).exec;

module.exports = function( grunt ) {
	grunt.registerTask( "tag", "Tag the specified version", function( version ) {
		exec( "git tag " + version, this.async() );
	});
};
