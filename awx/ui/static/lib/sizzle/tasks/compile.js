"use strict";

module.exports = function( grunt ) {
	grunt.registerMultiTask(
		"compile",
		"Compile sizzle.js to the dist directory. Embed date/version.",
		function() {
			var data = this.data,
				dest = data.dest,
				src = data.src,
				version = grunt.config( "pkg.version" ),
				compiled = grunt.file.read( src );

			// Embed version and date
			compiled = compiled
				.replace( /@VERSION/g, version )
				.replace( "@DATE", function() {
					var date = new Date();

					// YYYY-MM-DD
					return [
						date.getFullYear(),
						( "0" + ( date.getMonth() + 1 ) ).slice( -2 ),
						( "0" + date.getDate() ).slice( -2 )
					].join( "-" );
				});

			// Write source to file
			grunt.file.write( dest, compiled );

			grunt.log.ok( "File written to " + dest );
		}
	);
};
