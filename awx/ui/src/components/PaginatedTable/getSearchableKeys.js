export default function getSearchableKeys(keys = {}) {
  return Object.keys(keys)
    .filter((key) => keys[key].filterable)
    .map((key) => ({
      key,
      type: keys[key].type,
    }));
}
