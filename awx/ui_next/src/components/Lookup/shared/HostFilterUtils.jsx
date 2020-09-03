/**
 * Convert host filter string to params object
 * @param {string} string host filter string
 * @return {object} A string or array of strings keyed by query param key
 */
export function toSearchParams(string = '') {
  if (string === '') {
    return {};
  }
  return string
    .replace(/^\?/, '')
    .replace(/&/g, ' and ')
    .split(/ and | or /)
    .map(s => s.split('='))
    .reduce((searchParams, [k, v]) => {
      const key = decodeURIComponent(k);
      const value = decodeURIComponent(v);
      if (searchParams[key] === undefined) {
        searchParams[key] = value;
      } else if (Array.isArray(searchParams[key])) {
        searchParams[key] = [...searchParams[key], value];
      } else {
        searchParams[key] = [searchParams[key], value];
      }
      return searchParams;
    }, {});
}

/**
 * Convert params object to an encoded namespaced url query string
 * Used to put into url bar when modal opens
 * @param {object} config Config object for namespacing params
 * @param {object} searchParams A string or array of strings keyed by query param key
 * @return {string} URL query string
 */
export function toQueryString(config, searchParams = {}) {
  if (Object.keys(searchParams).length === 0) return '';

  return Object.keys(searchParams)
    .flatMap(key => {
      if (Array.isArray(searchParams[key])) {
        return searchParams[key].map(
          val =>
            `${config.namespace}.${encodeURIComponent(
              key
            )}=${encodeURIComponent(val)}`
        );
      }
      return `${config.namespace}.${encodeURIComponent(
        key
      )}=${encodeURIComponent(searchParams[key])}`;
    })
    .join('&');
}

/**
 * Convert params object to host filter string
 * @param {object} searchParams A string or array of strings keyed by query param key
 * @return {string} Host filter string
 */
export function toHostFilter(searchParams = {}) {
  return Object.keys(searchParams)
    .flatMap(key => {
      if (Array.isArray(searchParams[key])) {
        return searchParams[key].map(val => `${key}=${val}`);
      }
      return `${key}=${searchParams[key]}`;
    })
    .join(' and ');
}

/**
 * Helper function to remove namespace from params object
 * @param {object} config Config object with namespace param
 * @param {object} obj A string or array of strings keyed by query param key
 * @return {object} Params object without namespaced keys
 */
export function removeNamespacedKeys(config, obj = {}) {
  const clonedObj = Object.assign({}, obj);
  const newObj = {};
  Object.keys(clonedObj).forEach(nsKey => {
    let key = nsKey;
    if (nsKey.startsWith(config.namespace)) {
      key = nsKey.substr(config.namespace.length + 1);
    }
    newObj[key] = clonedObj[nsKey];
  });
  return newObj;
}

/**
 * Helper function to remove default params from params object
 * @param {object} config Config object with default params
 * @param {object} obj A string or array of strings keyed by query param key
 * @return {string} Params object without default params
 */
export function removeDefaultParams(config, obj = {}) {
  const clonedObj = Object.assign({}, obj);
  const defaultKeys = Object.keys(config.defaultParams);
  defaultKeys.forEach(keyToOmit => {
    delete clonedObj[keyToOmit];
  });
  return clonedObj;
}
