"use strict";

var exec = require( "child_process" ).exec;

module.exports = function( grunt ) {
	var rpreversion = /(\d\.\d+\.\d+)-pre/;

	grunt.registerTask( "release",
		"Release a version of sizzle, updates a pre version to released, " +
		"inserts `next` as the new pre version", function( next ) {
		
		if ( !rpreversion.test( next ) ) {
			grunt.fatal( "Next version should be a -pre version (x.x.x-pre): " + next );
			return;
		}

		var done,
			version = grunt.config( "pkg.version" );
		if ( !rpreversion.test( version ) ) {
			grunt.fatal( "Existing version is not a pre version: " + version );
			return;
		}
		version = version.replace( rpreversion, "$1" );

		done = this.async();
		exec( "git diff --quiet HEAD", function( err ) {
			if ( err ) {
				grunt.fatal( "The working directory should be clean when releasing. Commit or stash changes." );
				return;
			}
			// Build to dist directories along with a map and tag the release
			grunt.task.run([
				// Commit new version
				"version:" + version,
				// Tag new version
				"tag:" + version,
				// Commit next version
				"version:" + next
			]);
			done();
		});
	});
};
