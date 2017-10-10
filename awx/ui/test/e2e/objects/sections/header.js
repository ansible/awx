const header = {
    selector: 'div[class="at-Layout-topNav"]',
    elements: {
        logo: 'div[class$="logo"] img',
        user: 'i[class="fa fa-user"] + span',
        documentation: 'i[class="fa fa-book"]',
        logout: 'i[class="fa fa-power-off"]',
    }
};

module.exports = header;
