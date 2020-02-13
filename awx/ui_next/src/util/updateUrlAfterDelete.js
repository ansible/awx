import {
  parseQueryString,
  replaceParams,
  encodeNonDefaultQueryString,
} from './qs';

export default function updateUrlAfterDelete(
  qsConfig,
  location,
  items,
  selectedItems
) {
  const params = parseQueryString(qsConfig, location.search);
  if (params.page > 1 && selectedItems.length === items.length) {
    const newParams = encodeNonDefaultQueryString(
      qsConfig,
      replaceParams(params, { page: params.page - 1 })
    );
    return `${location.pathname}?${newParams}`;
  }
  return false;
}
