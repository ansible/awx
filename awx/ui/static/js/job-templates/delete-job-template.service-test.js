import jobTemplates from 'tower/job-templates/main';
import {describeModule} from '../describe-module';

describeModule(jobTemplates.name)
    .testService('deleteJobTemplate', function(test, restStub) {

        var service;

        test.withService(function(_service) {
            service = _service;
        });

        it('deletes the job template', function() {
            var result = {};

            var actual = service();

            restStub.succeedOn('destroy', result);
            restStub.flush();

            expect(actual).to.eventually.equal(result);

        });
    });
