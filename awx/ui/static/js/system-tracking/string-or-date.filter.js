export default
    [   'amDateFormatFilter',
        function(dateFormat) {
            return function(string, format) {
                if (moment.isMoment(string)) {
                    return dateFormat(string, format);
                } else {
                    return string;
                }
            };
        }
    ]
