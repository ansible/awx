var TestUtils = require('./test-utils')
  , parseISO = TestUtils.parseISO
  , timezoneJS = TestUtils.getTimezoneJS();
describe('TimezoneJS', function () {
  it('should get America/Chicago DST time correctly', function () {
    var testDstLeap = function (arr) {
      var expectedArr = [360, 300, 300, 360];
      var dt;
      var actual;
      var expected;
      for (var i = 0; i < arr.length; i++) {
        dt = timezoneJS.timezone.getTzInfo(parseISO(arr[i]), 'America/Chicago');
        actual = dt.tzOffset;
        expected = expectedArr[i];
        expect(actual).toEqual(expected);
      }
    };
    testDstLeap(['2004-04-04', '2004-04-05', '2004-10-31', '2004-11-01']);
    testDstLeap(['2005-04-03', '2005-04-04', '2005-10-30', '2005-10-31']);
    testDstLeap(['2006-04-02', '2006-04-03', '2006-10-29', '2006-10-30']);
    // 2007 -- new DST rules start here
    testDstLeap(['2007-03-11', '2007-03-12', '2007-11-04', '2007-11-05']);
    testDstLeap(['2008-03-09', '2008-03-10', '2008-11-02', '2008-11-03']);
    testDstLeap(['2009-03-08', '2009-03-09', '2009-11-01', '2009-11-02']);
    testDstLeap(['2010-03-14', '2010-03-15', '2010-11-07', '2010-11-08']);
    testDstLeap(['2011-03-13', '2011-03-14', '2011-11-06', '2011-11-07']);
  });

  it('should get tzOffset of America/Sao_Paulo correctly', function () {
    // Source: http://www.timeanddate.com/worldclock/clockchange.html?n=233
    // Standard: GMT-3 from Feb 16 - Nov 1
    // Daylight: GMT-2 from Nov 2 - Feb 16
    var dt;
    // 2008
    //dt = timezoneJS.timezone.getTzInfo(parseISO('2008-02-16-02:00'), 'America/Sao_Paulo');
    //expect(120, dt.tzOffset);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2008-02-17'), 'America/Sao_Paulo');
    expect(dt.tzOffset).toEqual(180);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2008-10-11'), 'America/Sao_Paulo');
    expect(dt.tzOffset).toEqual(180);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2008-10-19'), 'America/Sao_Paulo');
    expect(dt.tzOffset).toEqual(120);
  });

  it('should get New_York time correctly', function () {
    // Source: http://www.timeanddate.com/worldclock/city.html?n=179
    // Changes every year!
    var dt;
    // 2006
    dt = timezoneJS.timezone.getTzInfo(parseISO('2006-04-02T01:59:59'), 'America/New_York');
    expect(dt.tzOffset).toEqual(300);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2006-04-02T03:00:01'), 'America/New_York');
    expect(dt.tzOffset).toEqual(240);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2006-10-29T00:59:59'), 'America/New_York');
    expect(dt.tzOffset).toEqual(240);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2006-10-29T03:00:01'), 'America/New_York');
    expect(dt.tzOffset).toEqual(300);
    // 2009
    dt = timezoneJS.timezone.getTzInfo(parseISO('2009-03-08T01:59:59'), 'America/New_York');
    expect(dt.tzOffset).toEqual(300);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2009-03-08T03:00:01'), 'America/New_York');
    expect(dt.tzOffset).toEqual(240);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2009-11-01T00:59:59'), 'America/New_York');
    expect(dt.tzOffset).toEqual(240);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2009-11-01T03:00:01'), 'America/New_York');
    expect(dt.tzOffset).toEqual(300);
  });

  it('should get Jerusalem time correctly', function () {
    // Source: http://www.timeanddate.com/worldclock/city.html?n=110
    // Changes every year!
    var dt;
    // 2008
    dt = timezoneJS.timezone.getTzInfo(parseISO('2008-03-28T01:59:59'), 'Asia/Jerusalem');
    expect(dt.tzOffset).toEqual(-120);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2008-03-28T03:00:01'), 'Asia/Jerusalem');
    expect(dt.tzOffset).toEqual(-180);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2008-10-05T00:59:59'), 'Asia/Jerusalem');
    expect(dt.tzOffset).toEqual(-180);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2008-10-05T03:00:01'), 'Asia/Jerusalem');
    expect(dt.tzOffset).toEqual(-120);
    // 2009
    dt = timezoneJS.timezone.getTzInfo(parseISO('2009-03-27T01:59:59'), 'Asia/Jerusalem');
    expect(dt.tzOffset).toEqual(-120);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2009-03-27T03:00:01'), 'Asia/Jerusalem');
    expect(dt.tzOffset).toEqual(-180);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2009-09-27T00:59:59'), 'Asia/Jerusalem');
    expect(dt.tzOffset).toEqual(-180);
    dt = timezoneJS.timezone.getTzInfo(parseISO('2009-09-27T03:00:01'), 'Asia/Jerusalem');
    expect(dt.tzOffset).toEqual(-120);
  });

  it('should get abbreviation of central EU time correctly', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-01-01'), 'Europe/Berlin'); // winter time (CET) for sure
    expect(dt.tzAbbr).toEqual('CET');
  });

  it('should get abbr for central EU summer time correctly', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-07-01'), 'Europe/Berlin'); // summer time (CEST) for sure
    expect(dt.tzAbbr, 'CEST');
  });

  it('should get abbr for British Standard time correctly', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-01-01'), 'Europe/London'); // winter time (GMT) for sure
    expect(dt.tzAbbr, 'GMT');
  });

  it('should get abbr for British summer time correctly', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-07-01'), 'Europe/London'); // summer time (BST) for sure
    expect(dt.tzAbbr, 'BST');
  });

  it('should get abbr CET from tz info of 2010-03-28T01:59:59', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-03-28T01:59:59'), 'Europe/Berlin'); // CET, from local time
    expect(dt.tzAbbr).toEqual('CET');
  });

  it('should get abbr CEST from tz info of 2010-03-08T03:00:00', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-03-28T03:00:00'), 'Europe/Berlin'); // CEST, from local time
    expect(dt.tzAbbr, 'CEST');
  });

  it('should get abbr CET from tz info of 2010-03-08T00:59:59 UTC', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-03-28T00:59:59'), 'Europe/Berlin', true); // CEST, from local time
    expect(dt.tzAbbr, 'CET');
  });

  it('should get abbr CEST from tz info of 2010-03-08T01:00:00 UTC', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-03-28T01:00:00'), 'Europe/Berlin', true); // CEST, from local time
    expect(dt.tzAbbr, 'CEST');
  });

  it('should get abbr CST from 2010-03-14T01:59:59 Chicago', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-03-14T01:59:59'), 'America/Chicago'); // CST, from local time
    expect(dt.tzAbbr).toEqual('CST');
  });

  it('should get abbr CDT from 2010-03-14T03:00:00 Chicago', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-03-14T03:00:00'), 'America/Chicago'); // CST, from local time
    expect(dt.tzAbbr).toEqual('CDT');
  });

  it('should get abbr CST from 2010-03-14T07:59:59 UTC', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-03-14T07:59:59'), 'America/Chicago', true); // CST, from local time
    expect(dt.tzAbbr).toEqual('CST');
  });

  it('should get abbr CDT from 2010-03-14T08:00:00 Chicago', function () {
    var dt = timezoneJS.timezone.getTzInfo(parseISO('2010-03-14T08:00:00'), 'America/Chicago', true); // CST, from local time
    expect(dt.tzAbbr).toEqual('CDT');
  });

  //This is for issue #1 in github
  it('should not get null in getAllZones', function () {
    var zones = timezoneJS.timezone.getAllZones();
    for (var i = 0; i < zones; i++) {
      expect(zones[i]).not.toBe(null);
    }
  });

  it('should get tzInfo quickly', function () {
    var time = Date.now();
    for (var i = 0; i < 5000; i++) {
      timezoneJS.timezone.getTzInfo(new Date(), 'America/Chicago');
    }
    console.log('Took ' + (Date.now() - time) + 'ms to get 5000 same tzInfo');
  });

  it('should throw error with invalid zone', function () {
    var testFn = function () {
      timezoneJS.timezone.getTzInfo(new Date(), 'asd')
    }
    expect(testFn).toThrow(new Error('Timezone "asd" is either incorrect, or not loaded in the timezone registry.'));
  });

});
