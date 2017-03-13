export default
    function RRuleToAPI() {
        return function(rrule) {
            var response;
            response = rrule.replace(/(^.*(?=DTSTART))(DTSTART=.*?;)(.*$)/, function(str, p1, p2, p3) {
                return p2.replace(/\;/,'').replace(/=/,':') + ' ' + 'RRULE:' + p1 + p3;
            });
            return response;
        };
    }
