/* 
   Run this script with protractor against the sample app. It assumes the timezone option,
   AngularScheduler.useTimezone, is set to false.

 */

'use strict';

describe("Scheduler Widget", function() {

	it('should return the expected RRule', function() {
		var now = new Date(),
			tomorrow = new Date( now.getTime() + (24 * 60 * 60 * 1000) ),
			sendDateString = tomorrow.getFullYear() + '-' + ('00' + (tomorrow.getMonth() + 1)).substr(-2,2) + 
			'-' + ('00' + tomorrow.getDate()).substr(-2,2),
			receiveDateString = sendDateString.replace(/-/g,'') + 'T000000Z',
			result;
		browser.get('/app/index.html');
		element(by.model('schedulerName')).sendKeys('Schedule 1');
		element(by.model('schedulerStartDt')).clear();
		element(by.model('schedulerStartDt')).sendKeys(sendDateString);
		element(by.model('schedulerStartDt')).sendKeys(protractor.Key.ESCAPE);
		
		element(by.css('#schedulerFrequency option:nth-child(4)')).click()
			.then(function() {
				var interval = element(by.id('schedulerInterval'));
				interval.clear(); 
				interval.sendKeys('3');
				element(by.css('#scheduler-buttons #save-button')).click();
				browser.sleep(3000)
					.then(function() {
						element(by.css('#scheduler-detail #rrule')).getAttribute('value')
							.then(function(txt) {
								element(by.id('modal-ok-button')).click();
							 	expect(txt).toEqual('FREQ=DAILY;DTSTART=' + receiveDateString + ';INTERVAL=3');
							});
				    });
			});
	});

    //NOTE:  getText() on ng-model input returns an empty string. Resorted to getting value of attribute 'value'
			
	it('should translate given RRule', function() {
		var rrule = 'FREQ=WEEKLY;DTSTART=20140313T000000Z;INTERVAL=1;COUNT=1;BYDAY=MO,FR';

		browser.get('/app/index.html');
		element(by.model('inputRRule')).sendKeys(rrule);
		element(by.id('show-me-button')).click().then(function() {

			browser.sleep(1000).then(function() {
				var formDate, formHour, formMinute, formSecond, 
					formFrequencySelected, formInterval, formSchedulerEndSelected, weekDays=[], formCount;

				function checkDay(day) {
					element(by.css('button[data-value="' + day.toUpperCase() + '"]')).getAttribute('class')
						.then(function(cls){ console.log('check weekDay ' + day); expect(/active/.test(cls)).toBeTruthy(); },
							function(e) { console.log('check weekDay ' + day); console.log('Failed: ' + e); }
						);
				}
				
				element(by.css('#schedulerFrequency option:nth-child(5)')).isSelected()
					.then(function(selected) { console.log('schedulerFrequency'); expect(selected).toBeTruthy(); },
						function(e) { console.log('Failed: ' + e); });
				
				element(by.model('schedulerStartDt')).getAttribute('value')
					.then(function(txt) { console.log('schedulerStartDt'); expect(txt).toEqual('2014-03-13'); },
						function(e) { console.log('schedulerStartDt'); console.log('Failed: ' + e); });

				element(by.model('schedulerInterval')).getAttribute('value')
					.then(function(txt){ console.log('schedulerInterval'); expect(txt).toEqual('1'); },
						function(e) { console.log('schedulerInterval'); console.log('Failed: ' + e); });
				
				checkDay('MO');
				checkDay('FR');
				
				element(by.css('#schedulerEnd option:nth-child(2)')).isSelected()
					.then(function(selected) { console.log('schedulerEnd'); expect(selected).toBeTruthy(); },
						function(e) { console.log('schedulerEnd'); console.log('Failed: ' + e); });

				//element(by.id('schedulerOccurrenceCount')).getText().then(function(txt){ formCount = txt; });
				
			});
		});
	});
});
