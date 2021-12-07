/**
 * Returns queryset config with defaults, if needed
 * @param {string} namespace for appending to url querystring
 * @param {object} default params that are not handled with search (page, page_size and order_by)
 * @param {array} params that are number fields
 * @return {object} query param object
 */
export function getQSConfig(
  namespace,
  defaultParams = { page: 1, page_size: 5, order_by: 'name' },
  integerFields = ['page', 'page_size'],
  dateFields = ['modified', 'created']
) {
  if (!namespace) {
    throw new Error('a QS namespace is required');
  }
  // if order_by isn't passed, default to name
  if (!defaultParams.order_by) {
    defaultParams.order_by = 'name';
  }
  return {
    namespace,
    defaultParams,
    integerFields,
    dateFields,
  };
}

/**
 * Convert url query string to query param object
 * @param {object} qs config object (used for getting defaults, current query params etc.)
 * @param {string} url query string
 * @return {object} query param object
 */
export function parseQueryString(config, queryString) {
  if (!queryString) {
    return config.defaultParams || {};
  }
  const params = stringToObject(config, queryString);
  return addDefaultsToObject(config, params);
}

function stringToObject(config, qs) {
  const params = {};
  qs.replace(/^\?/, '')
    .split('&')
    .map((s) => s.split('='))
    .forEach(([nsKey, rawValue]) => {
      if (!nsKey || !namespaceMatches(config.namespace, nsKey)) {
        return;
      }
      const key = config.namespace
        ? decodeURIComponent(nsKey.substr(config.namespace.length + 1))
        : decodeURIComponent(nsKey);
      const value = parseValue(config, key, rawValue);
      params[key] = mergeParam(params[key], value);
    });
  return params;
}
export { stringToObject as _stringToObject };

/**
 * helper function to check the namespace of a param is what you expect
 * @param {string} namespace to append to params
 * @param {object} params object to append namespace to
 * @return {object} params object with namespaced keys
 */
const namespaceMatches = (namespace, fieldname) => {
  if (!namespace) return !fieldname.includes('.');

  return fieldname.startsWith(`${namespace}.`);
};

function parseValue(config, key, rawValue) {
  if (config.integerFields && config.integerFields.some((v) => v === key)) {
    return parseInt(rawValue, 10);
  }
  // TODO: parse dateFields into date format?
  return decodeURIComponent(rawValue);
}

function addDefaultsToObject(config, params) {
  return {
    ...config.defaultParams,
    ...params,
  };
}
export { addDefaultsToObject as _addDefaultsToObject };

/**
 * Convert query param object to url query string
 * Used to encode params for interacting with the api
 * @param {object} query param object
 * @return {string} url query string
 */
export const encodeQueryString = (params) => {
  if (!params) return '';

  return Object.keys(params)
    .sort()
    .filter((key) => params[key] !== null)
    .map((key) => [key, params[key]])
    .map(([key, value]) => encodeValue(key, value))
    .join('&');
};

function encodeValue(key, value) {
  if (Array.isArray(value)) {
    return value
      .map((val) => `${encodeURIComponent(key)}=${encodeURIComponent(val)}`)
      .join('&');
  }
  return `${encodeURIComponent(key)}=${encodeURIComponent(value)}`;
}

/**
 * Removes params from the search string and returns the updated list of params
 * @param {object} qs config object (used for getting defaults, current query params etc.)
 * @param {object} object with params from existing search
 * @param {object} object with new params to remove
 * @return {object} query param object
 */
export function removeParams(config, oldParams, paramsToRemove) {
  const updated = {
    ...config.defaultParams,
  };
  Object.keys(oldParams).forEach((key) => {
    const valToRemove = paramsToRemove[key];
    const isInt = config.integerFields?.includes(key);
    const updatedValue = removeParam(
      oldParams[key],
      isInt ? parseInt(valToRemove, 10) : valToRemove
    );
    if (
      updatedValue == null &&
      Object.prototype.hasOwnProperty.call(updated, key)
    ) {
      return;
    }
    updated[key] = updatedValue;
  });
  return updated;
}

function removeParam(oldVal, deleteVal) {
  if (oldVal === deleteVal) {
    return null;
  }
  if (Array.isArray(deleteVal)) {
    return deleteVal.reduce(removeParam, oldVal);
  }
  if (Array.isArray(oldVal)) {
    const index = oldVal.indexOf(deleteVal);
    if (index > -1) {
      oldVal.splice(index, 1);
    }
    if (oldVal.length === 1) {
      return oldVal[0];
    }
  }
  return oldVal;
}

/**
 * Merge old and new params together, joining values into arrays where necessary
 * @param {object} namespaced params object of old params
 * @param {object} namespaced params object of new params
 * @return {object} merged namespaced params object
 */
export function mergeParams(oldParams, newParams) {
  const merged = {};
  Object.keys(oldParams).forEach((key) => {
    merged[key] = mergeParam(oldParams[key], newParams[key]);
  });
  Object.keys(newParams).forEach((key) => {
    if (!merged[key]) {
      merged[key] = newParams[key];
    }
  });
  return merged;
}

function mergeParam(oldVal, newVal) {
  if (!newVal && newVal !== '') {
    return oldVal;
  }
  if (!oldVal && oldVal !== '') {
    return newVal;
  }
  let merged;
  if (Array.isArray(oldVal)) {
    merged = oldVal.concat(newVal);
  } else {
    merged = [oldVal].concat(newVal);
  }
  return dedupeArray(merged);
}

function dedupeArray(arr) {
  const deduped = [...new Set(arr)];
  if (deduped.length === 1) {
    return deduped[0];
  }
  return deduped;
}

/**
 * Update namespaced param(s), returning a new query string. Leaves params
 * from other namespaces unaltered
 * @param {object} qs config object for namespacing params, filtering defaults
 * @param {string} the url query string to update
 * @param {object} namespaced params to add or update. use null to indicate
 *        a param that should be deleted from the query string
 * @return {string} url query string
 */
export function updateQueryString(config, queryString, newParams) {
  const allParams = parseFullQueryString(queryString);
  const { namespace = null, defaultParams = {} } = config || {};
  Object.keys(newParams).forEach((key) => {
    const val = newParams[key];
    const fullKey = namespace ? `${namespace}.${key}` : key;
    if (val === null || val === defaultParams[key]) {
      delete allParams[fullKey];
    } else {
      allParams[fullKey] = newParams[key];
    }
  });
  return encodeQueryString(allParams);
}

function parseFullQueryString(queryString = '') {
  const allParams = {};
  queryString
    .replace(/^\?/, '')
    .split('&')
    .map((s) => s.split('='))
    .forEach(([rawKey, rawValue]) => {
      if (!rawKey) {
        return;
      }
      const key = decodeURIComponent(rawKey);
      const value = decodeURIComponent(rawValue);
      allParams[key] = mergeParam(allParams[key], value);
    });
  return allParams;
}
