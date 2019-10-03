export function getLanguage(nav) {
  if (nav.languages && nav.languages[0]) {
    return nav.languages[0];
  }
  if (nav.language) {
    return nav.language;
  }
  return nav.userLanguage;
}

export function getLanguageWithoutRegionCode(nav) {
  return getLanguage(nav)
    .toLowerCase()
    .split(/[_-]+/)[0];
}
