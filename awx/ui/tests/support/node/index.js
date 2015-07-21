/* jshint node: true */

(function() {
    var isNode = typeof window === 'undefined';

    if (!isNode) {
        window.expect = chai.expect;
        return;
    }

    require('./setup/jsdom');
    require('./setup/mocha');
    require('./setup/jquery');
    require('./setup/angular');
    require('./setup/angular-mocks');
    require('./setup/angular-templates');
    require('./setup/sinon');
    require('./setup/chai');
    require('./setup/chai-plugins');
    require('./setup/d3');
    require('./setup/nv');
    require('./setup/lodash');
    require('./setup/local-storage');
    require('./setup/moment');

})();
