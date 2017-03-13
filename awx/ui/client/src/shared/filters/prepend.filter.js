export default function() {
    return function(string, prepend) {
        if (string) {
            if(prepend) {
                return prepend + string;
            }
            else {
                return string;
            }
        }
        else {
            return "";
        }
    };
}
