export default function reducer(state, action) {
  switch (action.type) {
    case 'SELECT_ITEM':
      return selectItem(state, action.item);
    case 'DESELECT_ITEM':
      return deselectItem(state, action.item);
    case 'TOGGLE_MODAL':
      return toggleModal(state);
    case 'CLOSE_MODAL':
      return closeModal(state);
    case 'SET_MULTIPLE':
      return { ...state, multiple: action.value };
    case 'SET_VALUE':
      return { ...state, value: action.value };
    case 'SET_SELECTED_ITEMS':
      return { ...state, selectedItems: action.selectedItems };
    default:
      throw new Error(`Unrecognized action type: ${action.type}`);
  }
}

function selectItem(state, item) {
  const { selectedItems, multiple } = state;
  if (!multiple) {
    return {
      ...state,
      selectedItems: [item],
    };
  }
  const index = selectedItems.findIndex(i => i.id === item.id);
  if (index > -1) {
    return state;
  }
  return {
    ...state,
    selectedItems: [...selectedItems, item],
  };
}

function deselectItem(state, item) {
  return {
    ...state,
    selectedItems: state.selectedItems.filter(i => i.id !== item.id),
  };
}

function toggleModal(state) {
  const { isModalOpen, value, multiple } = state;
  if (isModalOpen) {
    return closeModal(state);
  }
  let selectedItems = [];
  if (multiple) {
    selectedItems = [...value];
  } else if (value) {
    selectedItems.push(value);
  }
  return {
    ...state,
    isModalOpen: !isModalOpen,
    selectedItems,
  };
}

function closeModal(state) {
  return {
    ...state,
    isModalOpen: false,
  };
}

export function initReducer({ value, multiple = false, required = false }) {
  assertCorrectValueType(value, multiple);
  let selectedItems = [];
  if (value) {
    selectedItems = multiple ? [...value] : [value];
  }
  return {
    selectedItems,
    value,
    multiple,
    isModalOpen: false,
    required,
  };
}

function assertCorrectValueType(value, multiple) {
  if (!multiple && Array.isArray(value)) {
    throw new Error(
      'Lookup value must not be an array unless `multiple` is set'
    );
  }
  if (multiple && !Array.isArray(value)) {
    throw new Error('Lookup value must be an array if `multiple` is set');
  }
}
