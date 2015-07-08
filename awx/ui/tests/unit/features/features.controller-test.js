import '../setup-browser';

import featuresController from 'tower/shared/features/features.controller';

describe('featuresController', function() {

    it('checks if a feature is enabled', window.inject(['$rootScope', function($rootScope) {
        var actual;

        $rootScope.features = {
            activity_streams: true,
            ldap: false
        };

        // TODO: extract into test controller in describeModule
        var Controller = featuresController[1];
        var controller = new Controller($rootScope);

        actual = controller.isFeatureEnabled('activity_streams');
        expect(actual).to.be.true;

        actual = controller.isFeatureEnabled('ldap');
        expect(actual).to.be.false;


    }]));
})
