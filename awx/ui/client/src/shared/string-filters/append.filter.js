export default function() {
    return function(string, append) {
        if (string) {
            return string + append;
        }

        return "";
    };
}

