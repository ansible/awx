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
