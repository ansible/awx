export function sortNestedDetails(obj = {}) {
  const nestedTypes = ['nested object', 'list'];
  const notNested = Object.entries(obj).filter(
    ([, value]) => !nestedTypes.includes(value.type)
  );
  const nestedList = Object.entries(obj).filter(
    ([, value]) => value.type === 'list'
  );
  const nestedObject = Object.entries(obj).filter(
    ([, value]) => value.type === 'nested object'
  );
  return [...notNested, ...nestedList, ...nestedObject];
}

export function pluck(sourceObject, ...keys) {
  return Object.assign({}, ...keys.map(key => ({ [key]: sourceObject[key] })));
}
