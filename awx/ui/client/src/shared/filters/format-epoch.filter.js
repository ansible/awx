export default
[   'moment',
    function(moment) {
        return function(seconds, formatStr) {
            if (!formatStr) {
                formatStr = 'll LT';
            }

            var millis = seconds * 1000;

            return moment(millis).format(formatStr);
        };
    }
];


