/**
 * Convert query param object to url query string
 *
 * @param {object} query param object
 * @return {string} url query string
 */
export const encodeQueryString = (params) => {
  if (!params) {
    return '';
  }

  return Object.keys(params)
    .sort()
    .map(key => ([key, params[key]]))
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');
};

/**
 * Convert url query string to query param object
 *
 * @param {string} url query string
 * @param {object} default params
 * @param {array} array of keys to parse as integers
 * @return {object} query param object
 */
export const parseQueryString = (queryString, integerFields = ['page', 'page_size']) => {
  if (!queryString) return {};

  const keyValuePairs = queryString.split('&')
    .map(s => s.split('='))
    .map(([key, value]) => {
      if (integerFields.includes(key)) {
        return [key, parseInt(value, 10)];
      }

      return [key, value];
    });

  return Object.assign(...keyValuePairs.map(([k, v]) => ({ [k]: v })));
};
