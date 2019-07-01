/**
 * Convert query param object to url query string
 *
 * @param {object} query param object
 * @return {string} url query string
 */
export const encodeQueryString = params => {
  if (!params) {
    return '';
  }

  return Object.keys(params)
    .sort()
    .filter(key => params[key] !== null)
    .map(key => [key, params[key]])
    .map(
      ([key, value]) =>
        `${encodeURIComponent(key)}=${encodeURIComponent(value)}`
    )
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
export const parseQueryString = (
  queryString,
  integerFields = ['page', 'page_size']
) => {
  if (!queryString) return {};

  const keyValuePairs = queryString
    .replace(/^\?/, '')
    .split('&')
    .map(s => s.split('='))
    .map(([key, value]) => {
      if (integerFields.includes(key)) {
        return [key, parseInt(value, 10)];
      }

      return [key, value];
    });

  return Object.assign(...keyValuePairs.map(([k, v]) => ({ [k]: v })));
};

export function getQSConfig(
  namespace,
  defaultParams = { page: 1, page_size: 5, order_by: 'name' },
  integerFields = ['page', 'page_size']
) {
  if (!namespace) {
    throw new Error('a QS namespace is required');
  }
  return {
    defaultParams,
    namespace,
    integerFields,
  };
}

export function encodeNamespacedQueryString(config, params) {
  return encodeQueryString(namespaceParams(config.namespace, params));
}

export function parseNamespacedQueryString(
  config,
  queryString,
  includeDefaults = true
) {
  const integerFields = prependNamespaceToArray(
    config.namespace,
    config.integerFields
  );
  const parsed = parseQueryString(queryString, integerFields);

  const namespace = {};
  Object.keys(parsed).forEach(field => {
    if (namespaceMatches(config.namespace, field)) {
      let fieldname = field;
      if (config.namespace) {
        fieldname = field.substr(config.namespace.length + 1);
      }
      namespace[fieldname] = parsed[field];
    }
  });
  return {
    ...(includeDefaults ? config.defaultParams : {}),
    ...namespace,
  };
}

export function updateNamespacedQueryString(config, queryString, newParams) {
  const params = parseQueryString(queryString);
  return encodeQueryString({
    ...params,
    ...namespaceParams(config.namespace, newParams),
  });
}

function namespaceParams(ns, params) {
  if (!ns) return params;

  const namespaced = {};
  Object.keys(params).forEach(key => {
    namespaced[`${ns}.${key}`] = params[key];
  });
  return namespaced;
}

function namespaceMatches(namespace, fieldname) {
  if (!namespace) {
    return !fieldname.includes('.');
  }
  return fieldname.startsWith(`${namespace}.`);
}

function prependNamespaceToArray(namespace, arr) {
  if (!namespace) {
    return arr;
  }
  return arr.map(f => `${namespace}.${f}`);
}
