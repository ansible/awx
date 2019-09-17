
// TODO: switch to using Lingui i18n for articles
export function getArticle(str) {
  const first = str[0];
  if ('aeiou'.includes(first)) {
    return 'an';
  }
  return 'a';
}

export function ucFirst(str) {
  return `${str[0].toUpperCase()}${str.substr(1)}`;
}

export const toTitleCase = string => {
  if (!string) {
    return '';
  }
  return string
    .toLowerCase()
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};
