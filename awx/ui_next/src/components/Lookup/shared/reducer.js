export default function reducer(state, action) {
  // console.log(action, state);
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
  return {
    ...state,
    isModalOpen: !isModalOpen,
    selectedItems: multiple ? [...value] : [value],
  };
}

function closeModal(state) {
  // TODO clear QSParams & push history state?
  // state.clearQSParams();
  return {
    ...state,
    isModalOpen: false,
  };
}
// clearQSParams() {
//   const { qsConfig, history } = this.props;
//   const parts = history.location.search.replace(/^\?/, '').split('&');
//   const ns = qsConfig.namespace;
//   const otherParts = parts.filter(param => !param.startsWith(`${ns}.`));
//   history.push(`${history.location.pathname}?${otherParts.join('&')}`);
// }

export function initReducer({
  id,
  items,
  count,
  header,
  name,
  onChange,
  value,
  multiple = false,
  required = false,
  qsConfig,
}) {
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
    onChange,
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
