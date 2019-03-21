const spinny = 'div.spinny';

exports.command = function navigateTo (url, expectSpinny = true) {
    this.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
    this.url(url);

    if (expectSpinny) {
        this.waitForElementVisible(spinny, () => {
            this.waitForElementNotVisible(spinny);
        });
    }

    return this;
};
