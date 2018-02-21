export default
    function RRuleToAPI() {
        return function(rrule, scope) {
            let localTime = scope.schedulerLocalTime;
            let timeZone = scope.schedulerTimeZone.name;

            let response = rrule.replace(/(^.*(?=DTSTART))(DTSTART.*?)(=.*?;)(.*$)/, (str, p1, p2, p3, p4) => {
                return p2 + ';TZID=' + timeZone + ':' + localTime + ' ' + 'RRULE:' + p4;
            });
            return response;
        };
    }
