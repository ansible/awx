import '../support/node';

import features from 'shared/features/main';
import {describeModule} from '../support/describe-module';

//test that it returns features, as well as test that it is returned in rootScope

describeModule(features.name)
    .testService('FeaturesService', function(test, restStub) {

        var service;

        test.withService(function(_service) {
            service = _service;
        });

        it('returns list of features', function() {
            var features = {},
            result = {
                data: {
                    license_info: {
                        features: features
                    }
                }
            };

            var actual = service.get();

            restStub.succeed(result);
            restStub.flush();

            return expect(actual).to.eventually.equal(features);

        });

        it('caches in rootScope', window.inject(['$rootScope',
            function($rootScope){
                var features = {},
                result = {
                    data: {
                        license_info: {
                            features: features
                        }
                    }
                };

                var actual = service.get();

                restStub.succeed(result);
                restStub.flush();

                return actual.then(function(){
                    expect($rootScope.features).to.equal(features);
                });
            }]));

    });
