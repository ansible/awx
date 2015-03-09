/*********************************************
 * @ngdoc function
 * @name __deferLoadIfEnabled
 * @description
 *
 * This function only included in debug releases.
 *
 * This function exists to make it easier to debug when using sourcemaps.
 * There is currently an issue in Chrome (and possibly other browsers) where
 * breakpoints that hit before sourcemaps are downloaded do not work.
 *
 * Calling this function uses a feature in Angular that looks for a prefix on
 * the `window.name` property to tell it to disable automatic loading of the app.
 *
 * If you need to debug code that runs at load time, first add:
 *
 *      ?aw.suspend=true
 *
 * to the end of the URL. When you see the Tower logo loaded on an otherwise blank page,
 * open the Dev Tools console and execute the code:
 *
 *      angular.resumeBootstrap()
 *
 * This should continue loading the app and hit your breakpoint.
 *
 * For more information on how this works see https://docs.angularjs.org/guide/bootstrap
*/
export function __deferLoadIfEnabled() {

    var deferPattern = /aw\.suspend=true/;

    if (deferPattern.test(window.location.search) || deferPattern.test(window.location.hash)) {
        // console.log('Deferred load due to "aw.suspend=true" in URL. Please execute `angular.resumeBootstrap()` to continue.');
        window.name = 'NG_DEFER_BOOTSTRAP!' + (window.name || '');
    }

}
