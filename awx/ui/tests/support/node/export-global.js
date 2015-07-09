module.exports =
    function exportGlobal(varName, value) {
        global[varName] = global.window[varName] = value;
    };
