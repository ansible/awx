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

export const arrayToString = value => value.join(',');

export const stringToArray = value => value.split(',').filter(val => !!val);
