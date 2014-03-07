var TestUtils = require('./test-utils')
  , parseISO = TestUtils.parseISO
  , date = require('../src/date')
  , timezoneJS = TestUtils.getTimezoneJS({
    loadingScheme: date.timezone.loadingSchemes.MANUAL_LOAD
  });
describe('TimezoneJS', function () {
  it('should manually load everything correctly', function () {
    var i = 0
      , sampleTz;

    expect(timezoneJS.timezone.loadingScheme).toEqual(date.timezone.loadingSchemes.MANUAL_LOAD);
    //Let's load some stuff
    timezoneJS.timezone.loadZoneJSONData('lib/all_cities.json', true);
    expect(Object.keys(timezoneJS.timezone.zones).length > 100).toBeTruthy();
    sampleTz = timezoneJS.timezone.getTzInfo(new Date(), 'Asia/Bangkok');
    expect(sampleTz).toBeDefined();
    expect(sampleTz.tzAbbr).toEqual('ICT');
    dt = new timezoneJS.Date();
    dt.setTimezone('America/Chicago');
    expect(dt.getTimezoneAbbreviation()).toMatch(/C(S|D)T/);
    dt.setTimezone('America/New_York');
    expect(dt.getTimezoneAbbreviation()).toMatch(/E(S|D)T/);
  });
});
