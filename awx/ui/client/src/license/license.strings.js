function LicenseStrings (BaseString) {
  BaseString.call(this, 'license');

  let t = this.t;
  let ns = this.license;

  ns.REPLACE_PASSWORD = t.s('Replace password');
  ns.CANCEL_LOOKUP = t.s('Cancel license lookup');
}

LicenseStrings.$inject = ['BaseStringService'];

export default LicenseStrings;
