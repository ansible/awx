import { useState } from 'react';

/**
 * useSelected hook provides a way to read and update a selected list
 * Param: array of list items
 * Returns: {
 *  selected: array of selected list items
 *  isAllSelected: boolean that indicates if all items are selected
 *  handleSelect: function that adds and removes items from selected list
 *  setSelected: setter function
 * }
 */

export default function useSelected(list = []) {
  const [selected, setSelected] = useState([]);
  const isAllSelected = selected.length > 0 && selected.length === list.length;

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(prevState => [...prevState.filter(i => i.id !== row.id)]);
    } else {
      setSelected(prevState => [...prevState, row]);
    }
  };

  return { selected, isAllSelected, handleSelect, setSelected };
}
