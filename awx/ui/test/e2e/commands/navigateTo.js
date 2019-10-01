const spinny = 'div.spinny';

exports.command = function navigateTo (url, expectSpinny = true) {
    this.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
    this.url(url);

    if (expectSpinny) {
        this.waitForElementVisible(spinny, () => {
            // If a process is running, give spinny a little more time before timing out.
            this.waitForElementNotVisible(spinny, 30000);
        });
    }

    return this;
};
