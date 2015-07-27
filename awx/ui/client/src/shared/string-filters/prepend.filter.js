export default function() {
    return function(string, prepend) {
        if (string) {
            return prepend + string;
        }

        return "";
    };
}
