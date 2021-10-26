/**
 * Convert host filter string to params object
 * @param {string} string host filter string
 * @return {object} A string or array of strings keyed by query param key
 */
export function toSearchParams(string = '') {
  if (string === '') {
    return {};
  }

  const readableParamsStr = string.replace(/^\?/, '').replace(/&/g, ' and ');
  const orArr = readableParamsStr.split(/ or /);

  if (orArr.length > 1) {
    orArr.forEach((str, index) => {
      orArr[index] = `or__${str}`;
    });
  }

  const unescapeString = (v) =>
    //  This is necessary when editing a string that was initially
    //  escaped to allow white space
    v ? v.replace(/"/g, '') : '';

  return orArr
    .join(' and ')
    .split(/ and | or /)
    .map((s) => s.split('='))
    .reduce((searchParams, [k, v]) => {
      const key = decodeURIComponent(k);
      const value = decodeURIComponent(unescapeString(v));
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
    .flatMap((key) => {
      if (Array.isArray(searchParams[key])) {
        return searchParams[key].map(
          (val) =>
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
 * Escape a string with double quote in case there was a white space
 * @param {string} value A string to be parsed
 * @return {string}  string
 */
const escapeString = (value) => {
  if (verifySpace(value)) {
    return `"${value}"`;
  }
  return value;
};

/**
 * Verify whether a string has white spaces
 * @param {string} value A string to be parsed
 * @return {bool} true if a string has white spaces
 */
const verifySpace = (value) => value.trim().indexOf(' ') >= 0;

/**
 * Convert params object to host filter string
 * @param {object} searchParams A string or array of strings keyed by query param key
 * @return {string} Host filter string
 */
export function toHostFilter(searchParams = {}) {
  const flattenSearchParams = Object.keys(searchParams)
    .sort()
    .flatMap((key) => {
      if (Array.isArray(searchParams[key])) {
        return searchParams[key].map((val) => `${key}=${escapeString(val)}`);
      }
      return `${key}=${escapeString(searchParams[key])}`;
    });

  const filteredSearchParams = flattenSearchParams.filter(
    (el) => el.indexOf('or__') === -1
  );

  const conditionalSearchParams = flattenSearchParams.filter(
    (el) => !filteredSearchParams.includes(el)
  );

  const conditionalQuery = conditionalSearchParams
    .map((el) => el.replace('or__', 'or '))
    .join(' ')
    .trim();

  if (filteredSearchParams.length === 0 && conditionalQuery) {
    // when there are just or operators the first one should be removed from the query
    // `name=foo or name__contains=bar or name__iexact=foo` instead of
    // `or name=foo or name__contains=bar or name__iexact=foo` that is the reason of the slice(3)
    return conditionalQuery.slice(3);
  }

  if (conditionalQuery) {
    return filteredSearchParams.join(' and ').concat(' ', conditionalQuery);
  }

  return filteredSearchParams.join(' and ').trim();
}

/**
 * Helper function to remove namespace from params object
 * @param {object} config Config object with namespace param
 * @param {object} obj A string or array of strings keyed by query param key
 * @return {object} Params object without namespaced keys
 */
export function removeNamespacedKeys(config, obj = {}) {
  const clonedObj = { ...obj };
  const newObj = {};
  Object.keys(clonedObj).forEach((nsKey) => {
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
  const clonedObj = { ...obj };
  const defaultKeys = Object.keys(config.defaultParams);
  defaultKeys.forEach((keyToOmit) => {
    delete clonedObj[keyToOmit];
  });
  return clonedObj;
}

/**
 * Helper function to update host_filter value
 * @param {string} value A string with host_filter value from querystring
 * @param {object} obj An object returned by toSearchParams - in which the
 * host_filter value was partially removed.
 * @return {object} An object with the value of host_filter modified
 */
export function modifyHostFilter(value, obj) {
  if (!value.includes('host_filter=')) return obj;
  const clonedObj = { ...obj };
  const host_filter = {};
  value.split(' ').forEach((item) => {
    if (item.includes('host_filter')) {
      host_filter.host_filter = item.slice('host_filter='.length);
    }
  });

  Object.keys(clonedObj).forEach((key) => {
    if (key.indexOf('host_filter') !== -1) {
      delete clonedObj[key];
    }
  });

  return {
    ...clonedObj,
    ...host_filter,
  };
}
