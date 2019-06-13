
export function pluralize (str) {
  return str[str.length - 1] === 's' ? `${str}es` : `${str}s`;
}

export function getArticle (str) {
  const first = str[0];
  if (('aeiou').includes(first)) {
    return 'an';
  }
  return 'a';
}

export function ucFirst (str) {
  return `${str[0].toUpperCase()}${str.substr(1)}`;
}

export const toTitleCase = (type) => type
  .toLowerCase()
  .split('_')
  .map(word => word.charAt(0).toUpperCase() + word.slice(1))
  .join(' ');

