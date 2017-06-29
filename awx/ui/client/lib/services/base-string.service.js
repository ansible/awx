let i18n;

function BaseStringService (namespace) {
    let t = i18n._;

    this.t = t;
    this[namespace] = {};

    this.CANCEL = t('CANCEL');
    this.SAVE = t('SAVE');
    this.OK = t('OK');
}


function BaseStringServiceLoader (_i18n_) {
    i18n = _i18n_;

    return BaseStringService;
}

BaseStringServiceLoader.$inject = ['i18n'];

export default BaseStringServiceLoader;
