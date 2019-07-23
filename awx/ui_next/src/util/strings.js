// TODO: switch to using Lingui i18n for pluralization
export function pluralize(str) {
  const lastChar = str[str.length - 1];
  if (lastChar === 's') {
    return `${str}es`;
  }
  if (lastChar === 'y') {
    return `${str.substr(0, str.length - 1)}ies`;
  }
  return `${str}s`;
}

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
