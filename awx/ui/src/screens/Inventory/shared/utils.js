const parseHostFilter = (value) => {
  if (value.host_filter && value.host_filter.includes('host_filter=')) {
    return {
      ...value,
      host_filter: value.host_filter.slice('host_filter='.length),
    };
  }
  return value;
};
export default parseHostFilter;

export function getInventoryPath(inventory) {
  const url = {
    '': `/inventories/inventory/${inventory.id}`,
    smart: `/inventories/smart_inventory/${inventory.id}`,
    constructed: `/inventories/constructed_inventory/${inventory.id}`,
  };
  return url[inventory.kind];
}
