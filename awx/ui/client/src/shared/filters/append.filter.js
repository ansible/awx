export default function() {
    return function(string, append) {
        if (string) {
            if (append) {
                return string + append;
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
