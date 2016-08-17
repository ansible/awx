var config = require('../webpack.config.js');
module.exports = {
    dev: config.dev,
    prod: config.release
};
