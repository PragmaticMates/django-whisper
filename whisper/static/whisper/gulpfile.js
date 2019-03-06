'use strict';

var gulp = require( './node_modules/gulp' );
var sass = require( './node_modules/gulp-sass' );
var sourcemaps = require('./node_modules/gulp-sourcemaps');

gulp.task('compile', function(done) {
	gulp.src( './scss/chat.scss' )
        .pipe( sourcemaps.init() )
		.pipe( sass() )
        .pipe( sourcemaps.write( './' ) )
		.pipe( gulp.dest( './css/' ) );
	done();
});

gulp.task('watch', function() {
	gulp.watch( './scss/chat.scss', gulp.series('compile') );
});
