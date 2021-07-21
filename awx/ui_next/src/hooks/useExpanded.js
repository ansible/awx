import { useState, useCallback } from 'react';

export default function useExpanded(list = []) {
  const [expanded, setExpanded] = useState([]);
  const isAllExpanded = expanded.length > 0 && expanded.length === list.length;

  const handleExpand = (row) => {
    if (!row.id) {
      throw new Error(`Selected row does not have an id`);
    }
    if (expanded.some((s) => s.id === row.id)) {
      setExpanded((prevState) => [...prevState.filter((i) => i.id !== row.id)]);
    } else {
      setExpanded((prevState) => [...prevState, row]);
    }
  };

  const expandAll = useCallback(
    (isExpanded) => {
      setExpanded(isExpanded ? [...list] : []);
    },
    [list]
  );

  return {
    expanded,
    isAllExpanded,
    handleExpand,
    setExpanded,
    expandAll,
  };
}
