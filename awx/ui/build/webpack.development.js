const _ = require('lodash');

const base = require('./webpack.base');

const development = {
    devtool: 'source-map'
};

module.exports = _.merge(base, development);
