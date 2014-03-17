/* GetRRule.js 
 *
 * Unit tests for scheduler widget
 *
 */

'use strict';

describe("Get RRule without timezone", function() {
    
    var SchedulerInit,
        $scope,
        schedules;

    schedules = [{
        schedulerStartDt: '2013-12-12',
        schedulerStartHour: '13',
        schedulerStartMinute: '00',
        schedulerStartSecond: '00',
        schedulerFrequency: { name: 'Daily', value: 'daily' },
        schedulerInterval: 3,
        schedulerEnd: { name: 'On Day', value: 'on' },
        schedulerEndDt: '2014-03-28',
        result: "FREQ=DAILY;DTSTART=20131212T130000Z;INTERVAL=3;UNTIL=20140328T130000Z"
    },
    {
        schedulerStartDt: '2014-03-03',
        schedulerStartHour: '17',
        schedulerStartMinute: '00',
        schedulerStartSecond: '00',
        schedulerFrequency: { name: 'Weekly', value: 'weekly' },
        schedulerInterval: 1,
        weekDays: ["su","mo","sa"],
        schedulerEnd: { name: 'After', value: 'after' },
        schedulerOccurrenceCount: 5,
        result: "FREQ=WEEKLY;DTSTART=20140303T170000Z;INTERVAL=1;COUNT=5;BYDAY=SU,MO,SA"
    },
    {
        schedulerStartDt: '2014-03-13',
        schedulerStartHour: '00',
        schedulerStartMinute: '00',
        schedulerStartSecond: '00',
        schedulerFrequency: { name: 'Monthly', value: 'monthly' },
        schedulerInterval: 1,
        monthlyRepeatOption: 'day',
        monthDay: 1,
        schedulerEnd: { name: 'Never', value: 'never' },
        result: "FREQ=MONTHLY;DTSTART=20140313T000000Z;INTERVAL=1;BYMONTHDAY=1"
    },
    {
        schedulerStartDt: '2014-03-13',
        schedulerStartHour: '00',
        schedulerStartMinute: '00',
        schedulerStartSecond: '00',
        schedulerFrequency: { name: 'Monthly', value: 'monthly' },
        schedulerInterval: 1,
        monthlyRepeatOption: 'other',
        monthlyOccurrence: { name: 'third', value: 3 },
        monthlyWeekDay: { name: 'Weekend day', value: ["sa","su"] },
        schedulerEnd: { name: 'Never', value: 'never' },
        result: "FREQ=MONTHLY;DTSTART=20140313T000000Z;INTERVAL=1;BYSETPOS=3;BYDAY=SA,SU"
    },
    {
        schedulerStartDt: '2014-03-19',
        schedulerStartHour: '00',
        schedulerStartMinute: '00',
        schedulerStartSecond: '00',
        schedulerFrequency: { name: 'Yearly', value: 'yearly' },
        schedulerInterval: 5,
        yearlyRepeatOption: 'month',
        yearlyMonth: { name: 'April', value: 4 },
        yearlyMonthDay: 1,
        schedulerEnd: { name: 'Never', value: 'never' },
        result: "FREQ=YEARLY;DTSTART=20140319T000000Z;INTERVAL=5;BYMONTH=4;BYMONTHDAY=1"
    },
    {
        schedulerStartDt: '2014-03-19',
        schedulerStartHour: '00',
        schedulerStartMinute: '00',
        schedulerStartSecond: '00',
        schedulerFrequency: { name: 'Yearly', value: 'yearly' },
        schedulerInterval: 1,
        yearlyRepeatOption: 'other',
        yearlyOccurrence: { name: 'last', value: -1 },
        yearlyWeekDay: { name: 'Monday', value: 'mo' },
        yearlyOtherMonth: { name: 'July', value: 7 },
        schedulerEnd: { name: 'After', value: 'after' },
        schedulerOccurrenceCount: 5,
        result: "FREQ=YEARLY;DTSTART=20140319T000000Z;INTERVAL=1;COUNT=5;BYSETPOS=-1;BYMONTH=7;BYDAY=MO"
    }];

    beforeEach(function() {
        module('Timezones', function($provide) {
            $provide.constant('$timezones.definitions.location', '/base/bower_components/angular-tz-extensions/tz/data');
        });
        module('AngularScheduler', function($provide) {
            $provide.constant('AngularScheduler.partials', '/lib/');
        });
        inject( function($rootScope, _SchedulerInit_) {
            SchedulerInit = _SchedulerInit_;
            $scope = $rootScope.$new(true);
        });
    });

    afterEach(function() {
        $scope.$destroy();
    });

    it('should return an object', function() {
        var scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false });
        expect(scheduler.inject).toBeDefined();
    });

    schedules.forEach(function(sched, idx) {
        it('should return ' + sched.result, function() {
            var scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false}),
                result, key;
            for(key in sched) {
                $scope[key] = sched[key];
            }
            $scope.scheduleTimeChange();
            result = scheduler.getValue(),
            //console.log('Test ' + idx + ' ' + sched.result);
            expect(result.rrule).toEqual(sched.result);
        });
    });
});

/* Make sure timezone conversion works. Will have to adjust later for DST */
describe("Get RRule with timezone", function() {
    
    var SchedulerInit,
        $scope,
        schedules,
        scheduler;

    schedules = [{
        schedulerStartDt: '2014-03-01',
        schedulerStartHour: '18',
        schedulerStartMinute: '00',
        schedulerStartSecond: '00',
        schedulerTimeZone: { name: 'America/New_York' },
        schedulerFrequency: { name: 'Daily', value: 'daily' },
        schedulerInterval: 1,
        schedulerEnd: { name: 'Never', value: 'never' },
        result: "FREQ=DAILY;DTSTART=20140301T230000Z;INTERVAL=1"
    }
    ];

    beforeEach(function() {
        module('Timezones', function($provide) {
            $provide.constant('$timezones.definitions.location', '/base/bower_components/angular-tz-extensions/tz/data');
        });
        module('AngularScheduler', function($provide) {
            $provide.constant('AngularScheduler.useTimezone',true);
            $provide.constant('AngularScheduler.partials', '/lib/');
        });
        inject( function($rootScope, _SchedulerInit_) {
            SchedulerInit = _SchedulerInit_;
            $scope = $rootScope;
            //.$new(true);
        });
    });

    afterEach(function() {
        $scope.$destroy();
    });

    it('should return an object', function() {
        var scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false });
        expect(scheduler.inject).toBeDefined();
    });

    it('should get the local timezone', function() {
        var scheduler = SchedulerInit({ scope: $scope }),
            user_timezone = scheduler.getUserTimezone();
        expect(user_timezone).toBeDefined();
    });

    schedules.forEach(function(sched, idx) {
        it('should return ' + sched.result, function() {
            var scheduler = SchedulerInit({ scope: $scope, requireFutureStartTime: false }),
                result, key;
            for(key in sched) {
                $scope[key] = sched[key];
            }
            $scope.scheduleTimeChange();
            result = scheduler.getValue(),
            //console.log('Test ' + idx + ' ' + sched.result);
            expect(result.rrule).toEqual(sched.result);
        });
    });
});
    

