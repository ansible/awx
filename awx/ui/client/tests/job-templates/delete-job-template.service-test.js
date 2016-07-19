import '../support/node';

import jobTemplatesModule from 'job-templates/main';
import RestStub from '../support/rest-stub';

//import RestStub from '../support/rest-stub';

describe('jobTemplates.service', function(){
    var $httpBackend, jobTemplates, service, Rest, $q, $stateExtender;

    before('instantiate RestStub', function(){
    	Rest = new RestStub();
    });

    beforeEach('instantiate the jobTemplates module', function(){
    	angular.mock.module(jobTemplatesModule.name);
    });

    beforeEach('mock dependencies', angular.mock.module(['$provide', function(_$provide_){
        var $provide = _$provide_;
    	$provide.value('GetBasePath', angular.noop);
    	$provide.value('$stateExtender', {addState: angular.noop});
    	$provide.value('Rest', Rest);
    }]));

     beforeEach('put $q into the scope', window.inject(['$q', function($q){
    	Rest.$q = $q;
    }]))

    beforeEach('inject real dependencies', inject(function($injector){
     	$httpBackend = $injector.get('$httpBackend');
     	service = $injector.get('deleteJobTemplate');
    }));

    describe('deleteJobTemplate', function(){
       	it('deletes a job template', function() {
       		var result = {};
       		var actual = service.deleteJobTemplate(1);
    
        	$httpBackend.when('DELETE', 'url').respond(200)
        	expect(actual).to.eventually.equal(result);
        });
    });
});
