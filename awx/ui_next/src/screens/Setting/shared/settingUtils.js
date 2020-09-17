export function sortNestedDetails(obj = {}) {
  const nestedTypes = ['nested object', 'list'];
  const notNested = Object.entries(obj).filter(
    ([, value]) => !nestedTypes.includes(value.type)
  );
  const nested = Object.entries(obj).filter(([, value]) =>
    nestedTypes.includes(value.type)
  );
  return [...notNested, ...nested];
}

export function pluck(sourceObject, ...keys) {
  return Object.assign({}, ...keys.map(key => ({ [key]: sourceObject[key] })));
}
