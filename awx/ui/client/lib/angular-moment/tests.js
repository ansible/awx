/* License: MIT.
 * Copyright (C) 2013, 2014, 2015, Uri Shaked.
 */

/* global describe, inject, module, beforeEach, afterEach, it, expect, spyOn, jasmine */

'use strict';

describe('module angularMoment', function () {
	var $rootScope, $compile, $window, $filter, moment, amTimeAgoConfig, originalTimeAgoConfig, angularMomentConfig,
		originalAngularMomentConfig, amMoment;

	beforeEach(module('angularMoment'));

	beforeEach(inject(function ($injector) {
		$rootScope = $injector.get('$rootScope');
		$compile = $injector.get('$compile');
		$window = $injector.get('$window');
		$filter = $injector.get('$filter');
		moment = $injector.get('moment');
		amMoment = $injector.get('amMoment');
		amTimeAgoConfig = $injector.get('amTimeAgoConfig');
		angularMomentConfig = $injector.get('angularMomentConfig');
		originalTimeAgoConfig = angular.copy(amTimeAgoConfig);
		originalAngularMomentConfig = angular.copy(angularMomentConfig);

		// Ensure the locale of moment.js is set to en by default
		(moment.locale || moment.lang)('en');
		// Add a sample timezones for tests
		moment.tz.add('UTC|UTC|0|0|');
		moment.tz.add('Pacific/Tahiti|LMT TAHT|9W.g a0|01|-2joe1.I');
	}));

	afterEach(function () {
		// Restore original configuration after each test
		angular.copy(originalTimeAgoConfig, amTimeAgoConfig);
		angular.copy(originalAngularMomentConfig, angularMomentConfig);
		jasmine.clock().uninstall();
	});


	describe('am-time-ago directive', function () {
		it('should change the text of the element to "a few seconds ago" when given unix timestamp', function () {
			$rootScope.testDate = new Date().getTime() / 1000;
			var element = angular.element('<span am-time-ago="testDate" am-preprocess="unix"></span>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds ago');
		});

		it('should change the text of the element to "a few seconds ago" when given current time', function () {
			$rootScope.testDate = new Date();
			var element = angular.element('<span am-time-ago="testDate"></span>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds ago');
		});

		it('should change the text of the div to "3 minutes ago" when given a date 3 minutes ago', function () {
			$rootScope.testDate = new Date(new Date().getTime() - 3 * 60 * 1000);
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('3 minutes ago');
		});

		it('should change the text of the div to "2 hours ago" when given a date 2 hours ago', function () {
			$rootScope.testDate = new Date(new Date().getTime() - 2 * 60 * 60 * 1000);
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('2 hours ago');
		});

		it('should change the text of the div to "one year ago" when given a date one year ago', function () {
			var today = new Date();
			$rootScope.testDate = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a year ago');
		});

		it('should parse correctly numeric dates as milliseconds since the epoch', function () {
			$rootScope.testDate = new Date().getTime();
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds ago');
		});

		it('should update the value if date changes on scope', function () {
			var today = new Date();
			$rootScope.testDate = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate()).getTime();
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a year ago');
			$rootScope.testDate = new Date();
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds ago');
		});

		it('should update the span text as time passes', function (done) {
			$rootScope.testDate = new Date(new Date().getTime() - 44000);
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds ago');

			var waitsInterval = setInterval(function () {
				// Wait until $rootScope.date is more than 45 seconds old
				if (new Date().getTime() - $rootScope.testDate.getTime() < 45000) {
					return;
				}

				clearInterval(waitsInterval);
				$rootScope.$digest();
				expect(element.text()).toBe('a minute ago');
				done();
			}, 50);
		});

		it('should schedule the update timer to one hour ahead for date in the far future (#73)', function () {
			$rootScope.testDate = new Date(new Date().getTime() + 86400000);
			jasmine.clock().install();
			spyOn($window, 'setTimeout');
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect($window.setTimeout).toHaveBeenCalledWith(jasmine.any(Function), 3600000);
		});

		describe('bindonce', function () {
			it('should change the text of the div to "3 minutes ago" when given a date 3 minutes ago with one time binding', function () {
				$rootScope.testDate = new Date(new Date().getTime() - 3 * 60 * 1000);
				var element = angular.element('<div am-time-ago="::testDate"></div>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('3 minutes ago');
			});

			it('should parse correctly numeric dates as milliseconds since the epoch with one time binding', function () {
				$rootScope.testDate = new Date().getTime();
				var element = angular.element('<div am-time-ago="::testDate"></div>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a few seconds ago');
			});

			it('should not update the value if date changes on scope when using one time binding', function () {
				var today = new Date();
				$rootScope.testDate = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate()).getTime();
				var element = angular.element('<div am-time-ago="::testDate"></div>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a year ago');
				$rootScope.testDate = new Date();
				$rootScope.$digest();
				expect(element.text()).toBe('a year ago');
			});
		});

		it('should handle undefined data', function () {
			$rootScope.testDate = null;
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			var digest = function () {
				$rootScope.$digest();
			};
			expect(digest).not.toThrow();
		});

		it('should remove the element text and cancel the timer when an empty string is given (#15)', function () {
			$rootScope.testDate = new Date().getTime();
			var element = angular.element('<div am-time-ago="testDate"></div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds ago');
			$rootScope.testDate = '';
			spyOn($window, 'clearTimeout').and.callThrough();
			$rootScope.$digest();
			expect($window.clearTimeout).toHaveBeenCalled();
			expect(element.text()).toBe('');
		});

		it('should not change the contents of the element until a date is given', function () {
			$rootScope.testDate = null;
			var element = angular.element('<div am-time-ago="testDate">Initial text</div>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('Initial text');
			$rootScope.testDate = new Date().getTime();
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds ago');
		});

		it('should cancel the timer when the scope is destroyed', function () {
			var scope = $rootScope.$new();
			$rootScope.testDate = new Date();
			var element = angular.element('<span am-time-ago="testDate"></span>');
			element = $compile(element)(scope);
			$rootScope.$digest();
			spyOn($window, 'clearTimeout').and.callThrough();
			scope.$destroy();
			expect($window.clearTimeout).toHaveBeenCalled();
		});

		it('should generate a time string without suffix when configured to do so', function () {
			amTimeAgoConfig.withoutSuffix = true;
			$rootScope.testDate = new Date();
			var element = angular.element('<span am-time-ago="testDate"></span>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds');
		});

		it('should generate update the text following a locale change via amMoment.changeLocale() method', function () {
			$rootScope.testDate = new Date();
			var element = angular.element('<span am-time-ago="testDate"></span>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.text()).toBe('a few seconds ago');
			amMoment.changeLocale('fr');
			expect(element.text()).toBe('il y a quelques secondes');
		});

		it('should update the `datetime` attr if applied to a TIME element', function () {
			$rootScope.testDate = Date.UTC(2012, 8, 20, 15, 20, 12);
			var element = angular.element('<time am-time-ago="testDate"></span>');
			element = $compile(element)($rootScope);
			$rootScope.$digest();
			expect(element.attr('datetime')).toBe('2012-09-20T15:20:12.000Z');
		});

		describe('setting the element title', function () {
			it('should not set the title attribute of the element to the date by default', function () {
				$rootScope.testDate = new Date().getTime() / 1000;
				var element = angular.element('<span am-time-ago="testDate"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.attr('title')).toBeUndefined();
			});

			it('should not change the title attribute of the element if the element already has a title', function () {
				amTimeAgoConfig.titleFormat = 'MMMM Do YYYY, h:mm:ss a';
				$rootScope.testDate = new Date().getTime() / 1000;
				var element = angular.element('<span am-time-ago="testDate" title="test"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.attr('title')).toBe('test');
			});

			it('should set the title attribute of the element to the formatted date as per the config', function () {
				amTimeAgoConfig.titleFormat = 'MMMM Do YYYY, h:mm:ss a';
				$rootScope.testDate = new Date().getTime() / 1000;
				var element = angular.element('<span am-time-ago="testDate"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				var testDateWithCustomFormatting = moment($rootScope.testDate).format(amTimeAgoConfig.titleFormat);
				expect(element.attr('title')).toBe(testDateWithCustomFormatting);
			});

			describe('full date support', function () {
				it('should display relative time if the date is recent', function () {
					amTimeAgoConfig.fullDateThreshold = 7;
					$rootScope.testDate = new Date(new Date().getTime() - 2 * 24 * 60 * 60 * 1000);
					var element = angular.element('<span am-time-ago="testDate"></span>');
					element = $compile(element)($rootScope);
					$rootScope.$digest();
					expect(element.text()).toBe('2 days ago');
				});

				it('should display full time if the date is past the threshold', function () {
					amTimeAgoConfig.fullDateThreshold = 7;
					$rootScope.testDate = new Date(2012, 5, 5);
					var element = angular.element('<span am-time-ago="testDate"></span>');
					element = $compile(element)($rootScope);
					$rootScope.$digest();
					expect(element.text()).toMatch(/^2012-06-05T00:00:00\+\d\d:\d\d$/);
				});

				it('should display full time using the given format', function () {
					amTimeAgoConfig.fullDateThreshold = 7;
					amTimeAgoConfig.fullDateFormat = 'YYYY,DD,MM';
					$rootScope.testDate = new Date(2010, 1, 8);
					var element = angular.element('<span am-time-ago="testDate"></span>');
					element = $compile(element)($rootScope);
					$rootScope.$digest();
					expect(element.text()).toBe('2010,08,02');
				});

				it('should support changing the full date threshold through attribute', function () {
					$rootScope.threshold = 7;
					$rootScope.testDate = new Date(new Date().getTime() - 12 * 24 * 60 * 60 * 1000);
					var element = angular.element('<span am-time-ago="testDate" am-full-date-threshold="{{threshold}}"></span>');
					element = $compile(element)($rootScope);
					$rootScope.$digest();
					expect(element.text()).toBe(moment($rootScope.testDate).format());

					$rootScope.threshold = 20;
					$rootScope.$digest();
					expect(element.text()).toBe('12 days ago');
				});

				it('should support setting the full date format through attribute', function () {
					amTimeAgoConfig.fullDateThreshold = 7;
					$rootScope.testDate =  new Date(2013, 11, 15);
					var element = angular.element('<span am-time-ago="testDate" am-full-date-format="YYYY-MM-DD"></span>');
					element = $compile(element)($rootScope);
					$rootScope.$digest();
					expect(element.text()).toBe('2013-12-15');
				});
			});
		});

		describe('am-without-suffix attribute', function () {
			it('should generate a time string without suffix when true', function () {
				$rootScope.testDate = new Date();
				var element = angular.element('<span am-time-ago="testDate" am-without-suffix="true"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a few seconds');
			});

			it('should generate a time string with suffix when false', function () {
				amTimeAgoConfig.withoutSuffix = true;
				$rootScope.testDate = new Date();
				var element = angular.element('<span am-time-ago="testDate" am-without-suffix="false"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a few seconds ago');
			});

			it('should support expressions', function () {
				$rootScope.testDate = new Date();
				$rootScope.withSuffix = false;
				var element = angular.element('<span am-time-ago="testDate" am-without-suffix="!withSuffix"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a few seconds');
				$rootScope.withSuffix = true;
				$rootScope.$digest();
				expect(element.text()).toBe('a few seconds ago');
			});

			it('should ignore non-boolean values', function () {
				$rootScope.testDate = new Date();
				$rootScope.withoutSuffix = 'string';
				var element = angular.element('<span am-time-ago="testDate" am-without-suffix="withoutSuffix"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a few seconds ago');
			});
		});

		describe('am-format attribute', function () {
			it('should support custom date format', function () {
				var today = new Date();
				$rootScope.testDate = today.getFullYear() + '#' + today.getDate() + '#' + today.getMonth();
				var element = angular.element('<span am-time-ago="testDate" am-format="YYYY#DD#MM"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a month ago');
			});

			it('should support angular expressions in date format', function () {
				var today = new Date();
				$rootScope.testDate = today.getMonth() + '@' + today.getFullYear() + '@' + today.getDate();
				var element = angular.element('<span am-time-ago="testDate" am-format="{{dateFormat}}"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				$rootScope.dateFormat = 'MM@YYYY@DD';
				$rootScope.$digest();
				expect(element.text()).toBe('a month ago');
			});
		});

		describe('format config property', function () {
			it('should be used when no `am-format` attribute is found', function () {
				angularMomentConfig.format = 'MM@YYYY@DD';
				var today = new Date();
				$rootScope.testDate = today.getMonth() + '@' + today.getFullYear() + '@' + today.getDate();
				var element = angular.element('<span am-time-ago="testDate"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a month ago');
			});

			it('should be overridable by `am-format` attribute', function () {
				angularMomentConfig.format = 'YYYY@MM@@DD';
				var today = new Date();
				$rootScope.testDate = today.getMonth() + '@' + today.getFullYear() + '@' + today.getDate();
				var element = angular.element('<span am-format="MM@YYYY@DD" am-time-ago="testDate"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('a month ago');
			});
		});

		describe('serverTime configuration', function () {
			it('should calculate time ago in respect to the configured server time', function () {
				amTimeAgoConfig.serverTime = Date.UTC(2014, 5, 12, 5, 22, 11);
				$rootScope.testDate = Date.UTC(2014, 5, 12, 9, 22, 11);
				var element = angular.element('<span am-time-ago="testDate"></span>');
				element = $compile(element)($rootScope);
				$rootScope.$digest();
				expect(element.text()).toBe('in 4 hours');
			});
		});
	});

	describe('amCalendar filter', function () {
		var amCalendar;

		beforeEach(function () {
			amCalendar = $filter('amCalendar');
		});

		it('should convert today date to calendar form', function () {
			var today = new Date();
			var testDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 13, 33, 33);
			expect(amCalendar(testDate)).toBe('Today at 1:33 PM');
		});

		it('should convert date in long past to calendar form', function () {
			expect(amCalendar(new Date(2012, 2, 25, 13, 14, 15))).toBe('03/25/2012');
		});

		it('should gracefully handle undefined values', function () {
			expect(amCalendar()).toBe('');
		});

		it('should accept a numeric unix timestamp (milliseconds since the epoch) as input', function () {
			expect(amCalendar(new Date(2012, 0, 22, 4, 46, 54).getTime())).toBe('01/22/2012');
		});

		it('should respect the configured timezone', function () {
			angularMomentConfig.timezone = 'Pacific/Tahiti';
			expect(amCalendar(Date.UTC(2012, 0, 22, 4, 46, 54))).toBe('01/21/2012');
		});

		it('should apply the "utc" preprocessor when the string "utc" is given in the second argument', function () {
			expect(amCalendar(Date.UTC(2012, 0, 22, 0, 0, 0), 'utc')).toBe('01/22/2012');
			expect(amCalendar(Date.UTC(2012, 0, 22, 23, 59, 59), 'utc')).toBe('01/22/2012');
		});

		it('should apply the "unix" preprocessor if angularMomentConfig.preprocess is set to "unix" and no preprocessor is given', function () {
			var unixDate = new Date(1970, 0, 2, 10, 0, 0).getTime() / 1000;
			angularMomentConfig.preprocess = 'unix';
			expect(amCalendar(unixDate)).toBe('01/02/1970');
		});

		it('should ignore the default preprocessor if we explicity give it null in the second argument', function () {
			var unixDate = new Date(1970, 0, 1, 10, 0, 0).getTime();
			angularMomentConfig.preprocess = 'unix';
			expect(amCalendar(unixDate, null)).toBe('01/01/1970');
		});

		it('should gracefully handle the case where timezone is given but moment-timezone is not loaded', function () {
			angularMomentConfig.timezone = 'Pacific/Tahiti';
			var originalMomentTz = moment.fn.tz;
			try {
				delete moment.fn.tz;
				expect(amCalendar(new Date(2012, 0, 22, 4, 46, 54).getTime())).toBe('01/22/2012');
			} finally {
				moment.fn.tz = originalMomentTz;
				moment.fn.tz = originalMomentTz;
			}
		});

		it('should return an empty string for invalid input', function () {
			expect(amCalendar('blah blah')).toBe('');
		});
	});

	describe('amDifference filter', function () {
		var amDifference;

		beforeEach(function () {
			amDifference = $filter('amDifference');
		});

		it('should take the difference of two dates in milliseconds', function () {
			var today = new Date(2012, 0, 22, 0, 0, 0);
			var testDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 13, 33, 33);
			expect(amDifference(testDate, today)).toBe(48813000);
		});

		it('should support passing "years", "months", "days", etc as a units parameter', function () {
			var test = new Date(2012, 0, 22, 4, 46, 54);
			var testDate1 = new Date(2013, 0, 22, 4, 46, 54);
			expect(amDifference(testDate1, test, 'years')).toBe(1);
			var testDate2 = new Date(2012, 1, 22, 4, 46, 54);
			expect(amDifference(testDate2, test, 'months')).toBe(1);
			var testDate3 = new Date(2012, 0, 23, 4, 46, 54);
			expect(amDifference(testDate3, test, 'days')).toBe(1);
		});

		it('should allow rounding to be disabled via parameter', function () {
			var test = new Date(2012, 0, 22, 4, 46, 54);
			var testDate1 = new Date(test.getFullYear() + 1, test.getMonth() + 6, test.getDate());
			expect(amDifference(testDate1, test, 'years')).toBe(1);
			expect(amDifference(testDate1, test, 'years', true)).toBeCloseTo(1.5);
		});

		it('dates from the future should return negative values', function () {
			var today = new Date(2012, 0, 22, 4, 46, 54);
			var testDate = new Date(2013, 0, 22, 4, 46, 54);
			expect(String(amDifference(today, testDate))).toContain('-');
		});

		it('should gracefully handle undefined values', function () {
			expect(amDifference()).toBe('');
		});

		it('should accept a numeric unix timestamp (milliseconds since the epoch) as input', function () {
			expect(amDifference(new Date(2012, 0, 22, 4, 46, 55).getTime(), new Date(2012, 0, 22, 4, 46, 54).getTime())).toBe(1000);
		});

		it('should apply the "utc" preprocessor when the string "utc" is given as a preprocessor argument', function () {
			expect(amDifference([2012, 0, 22, 0, 0, 1], Date.UTC(2012, 0, 22, 0, 0, 0), null, null, 'utc')).toBe(1000);
			expect(amDifference(Date.UTC(2012, 0, 22, 0, 0, 1), [2012, 0, 22, 0, 0, 0], null, null, null, 'utc')).toBe(1000);
		});

		it('should apply the "unix" preprocessor if angularMomentConfig.preprocess is set to "unix" and no preprocessor is given', function () {
			angularMomentConfig.preprocess = 'unix';
			expect(amDifference(100001, 100000)).toBe(1000);
		});

		it('should return an empty string for invalid input', function () {
			expect(amDifference('blah blah')).toBe('');
		});
	});

	describe('amDateFormat filter', function () {
		var amDateFormat;

		beforeEach(function () {
			amDateFormat = $filter('amDateFormat');
		});

		it('should support displaying format', function () {
			var today = new Date();
			var expectedResult = today.getDate() + '.' + (today.getMonth() + 1) + '.' + today.getFullYear();
			expect(amDateFormat(today, 'D.M.YYYY')).toBe(expectedResult);
		});

		it('should gracefully handle undefined values', function () {
			expect(amDateFormat(undefined, 'D.M.YYYY')).toBe('');
		});

		it('should accept a numeric unix timestamp (milliseconds since the epoch) as input', function () {
			var timestamp = new Date(2012, 0, 22, 12, 46, 54).getTime();
			expect(amDateFormat(timestamp, '(HH,mm,ss);MM.DD.YYYY')).toBe('(12,46,54);01.22.2012');
		});

		it('should gracefully handle string unix timestamp as input', function () {
			var strTimestamp = String(new Date(2012, 0, 22, 12, 46, 54).getTime());
			expect(amDateFormat(strTimestamp, '(HH,mm,ss);MM.DD.YYYY')).toBe('(12,46,54);01.22.2012');
		});

		it('should respect the configured timezone', function () {
			angularMomentConfig.timezone = 'Pacific/Tahiti';
			var timestamp = Date.UTC(2012, 0, 22, 12, 46, 54);
			expect(amDateFormat(timestamp, '(HH,mm,ss);MM.DD.YYYY')).toBe('(02,46,54);01.22.2012');
		});

		it('should respect the timezone parameter', function () {
			var timestamp = Date.UTC(2012, 0, 22, 12, 46, 54);
			expect(amDateFormat(timestamp, '(HH,mm,ss);MM.DD.YYYY', 'utc', 'Pacific/Tahiti')).toBe('(02,46,54);01.22.2012');
		});

		it('should return an empty string for invalid input', function () {
			expect(amDateFormat('blah blah', '(HH,mm,ss);MM.DD.YYYY')).toBe('');
		});
	});

	describe('amDurationFormat filter', function () {
		var amDurationFormat;

		beforeEach(function () {
			amDurationFormat = $filter('amDurationFormat');
		});

		it('should support return the given duration as text', function () {
			expect(amDurationFormat(1000, 'milliseconds')).toBe('a few seconds');
		});

		it('should support return a day given 24 hours', function () {
			expect(amDurationFormat(24, 'hours')).toBe('a day');
		});

		it('should add prefix the result with the word "in" if the third parameter (suffix) is true', function () {
			expect(amDurationFormat(1, 'minutes', true)).toBe('in a minute');
		});

		it('should add suffix the result with the word "ago" if the duration is negative and the third parameter is true', function () {
			expect(amDurationFormat(-1, 'minutes', true)).toBe('a minute ago');
		});

		it('should gracefully handle undefined values for duration', function () {
			expect(amDurationFormat(undefined, 'minutes')).toBe('');
		});
	});


	describe('amTimeAgo filter', function () {
		var amTimeAgo;

		beforeEach(function () {
			amTimeAgo = $filter('amTimeAgo');
		});

		it('should support return the time ago as text', function () {
			var date = new Date();
			expect(amTimeAgo(date)).toBe('a few seconds ago');
		});

		it('should remove suffix from the result if the third parameter (suffix) is true', function () {
			var date = new Date();
			expect(amTimeAgo(date, null, true)).toBe('a few seconds');
		});

		it('should gracefully handle undefined values', function () {
			expect(amTimeAgo()).toBe('');
		});

		it('should gracefully handle invalid input', function () {
			expect(amTimeAgo('noDate')).toBe('');
		});

	});

	describe('amMoment service', function () {
		describe('#changeLocale', function () {
			it('should convert today\'s date to custom calendar format', function () {
				var today = new Date();
				amMoment.changeLocale('en', {calendar: {sameDay: '[This Day]'}});
				var amCalendar = $filter('amCalendar');
				var testDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 13, 33, 33);
				expect(amCalendar(testDate)).toBe('This Day');
			});

			it('should return the current locale', function () {
				expect(amMoment.changeLocale()).toBe('en');
			});

			it('should broadcast an angularMoment:localeChanged event on the root scope if a locale is specified', function () {
				var eventBroadcasted = false;
				$rootScope.$on('amMoment:localeChanged', function () {
					eventBroadcasted = true;
				});
				amMoment.changeLocale('fr');
				expect(eventBroadcasted).toBe(true);
			});

			it('should not broadcast an angularMoment:localeChanged event on the root scope if no locale is specified', function () {
				var eventBroadcasted = false;
				$rootScope.$on('amMoment:localeChanged', function () {
					eventBroadcasted = true;
				});
				amMoment.changeLocale();
				expect(eventBroadcasted).toBe(false);
			});
		});

		describe('#changeTimezone', function () {
			it('Should update the current timezone', function () {
				amMoment.changeTimezone('UTC');
				expect(amMoment.applyTimezone(moment()).utcOffset()).toBe(0);

				amMoment.changeTimezone('Pacific/Tahiti');
				expect(amMoment.applyTimezone(moment()).utcOffset()).toBe(-600);
			});

			it('should broadcast an angularMoment:timezoneChanged event on the root scope with the new timezone value', function () {
				var eventBroadcasted = false;
				$rootScope.$on('amMoment:timezoneChanged', function () {
					eventBroadcasted = true;
				});
				amMoment.changeTimezone('UTC');
				expect(eventBroadcasted).toBe(true);
			});
		});

		describe('#preprocessDate', function () {
			it('should call a custom preprocessor that was registered on amMoment.preprocessors', function () {
				var testDate = new Date(2013, 0, 22, 12, 46, 54);
				var meeting = {
					name: 'Budget plan',
					date: testDate
				};

				amMoment.preprocessors.foobar = function (value) {
					return moment(value.date);
				};

				expect(amMoment.preprocessDate(meeting, 'foobar').valueOf()).toEqual(testDate.getTime());
			});

			it('should issue a warning if an unsupported preprocessor is used and fall-back to default processing', inject(function ($log) {
				var testDate = new Date(2014, 0, 22, 12, 46, 54);
				spyOn($log, 'warn');
				expect(amMoment.preprocessDate(testDate.getTime(), 'blabla').valueOf()).toEqual(testDate.getTime());
				expect($log.warn).toHaveBeenCalledWith('angular-moment: Ignoring unsupported value for preprocess: blabla');
			}));
		});
	});

	describe('amTimeAgoConfig constant', function () {
		it('should generate time with suffix by default', function () {
			expect(amTimeAgoConfig.withoutSuffix).toBe(false);
		});
	});

	describe('angularMomentConfig constant', function () {
		it('should have an empty timezone value by default', function () {
			expect(angularMomentConfig.timezone).toBe('');
		});
		it('should have an empty preprocess value by default', function () {
			expect(angularMomentConfig.preprocess).toBe(null);
		});
	});
});
