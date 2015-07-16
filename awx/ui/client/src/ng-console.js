/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// THIS FILE ONLY INCLUDED IN DEBUG BUILDS
//
// To use:
//
// Open a console in Chrome DevTools and load this
// script with:
//
//      require('tower/ng-console');
//
// Then go to the Elements tab and drill down to any
// element within the angular app. Go back to the console
// and you can access the scope for the selected element
// using the variable $scope.
//
var ngAppElem = angular.element(document.querySelector('[ng-app]') || document);

window.injector = ngAppElem.injector();
window.inject = window.injector.invoke;
window.$rootScope = ngAppElem.scope();

// getService('auth') will create a variable `auth` assigned to the service `auth`.
//
window.getService = function getService(serviceName) {
    window.inject([serviceName, function (s) {window[serviceName] = s;}]);
};

Object.defineProperty(window, '$scope', {
    get: function () {
        var elem = angular.element(window.__commandLineAPI.$0);
        return elem.isolateScope() || elem.scope();
    },
});

/**
 * USAGE
 *
 * First copy the script and paste it in Chrome DevTools in Sources -> left pane -> Snippets.
 * Then, after loading an Angular page, right click on the snippet and choose "run".
 * Afterwards, you have the following available in the console:
 *
 * 1) $rootScope
 * 2) inject(function ($q, $compile) { ...use $q and $compile here... });
 * 3) click on an element in DevTools; now $scope in the console points at the element scope (isolate if one exists).
 *
 * Enjoy!
 */
