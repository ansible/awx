export default
    function RRuleToAPI() {

        // This function removes the 'Z' from the UNTIL portion of the
        // rrule. The API will default to using the timezone that is
        // specified in the TZID as the locale for the UNTIL. 
        function parseOutZ (rrule) {
            let until = rrule.split('UNTIL=');
            if(_.has(until, '1')){
                rrule = until[0];
                until = until[1].replace('Z', '');
                return `${rrule}UNTIL=${until}`;
            } else {
                return rrule;
            }
        }


        return function(rrule, scope) {
            let localTime = scope.schedulerLocalTime;
            let timeZone = scope.schedulerTimeZone.name;

            let response = rrule.replace(/(^.*(?=DTSTART))(DTSTART.*?)(=.*?;)(.*$)/, (str, p1, p2, p3, p4) => {
                return p2 + ';TZID=' + timeZone + ':' + localTime + ' ' + 'RRULE:' + p4;
            });

            response = parseOutZ(response);
            return response;
        };
    }
