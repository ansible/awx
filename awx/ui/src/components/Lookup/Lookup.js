import React, { useReducer, useEffect, useState } from 'react';
import {
  string,
  bool,
  arrayOf,
  func,
  number,
  oneOfType,
  shape,
  node,
  object,
} from 'prop-types';
import { withRouter } from 'react-router-dom';
import { useField } from 'formik';
import { SearchIcon } from '@patternfly/react-icons';
import {
  Button,
  ButtonVariant,
  Chip,
  InputGroup,
  Modal,
  TextInput,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import useDebounce from 'hooks/useDebounce';
import { QSConfig } from 'types';
import ChipGroup from '../ChipGroup';
import reducer, { initReducer } from './shared/reducer';

const ChipHolder = styled.div`
  --pf-c-form-control--Height: auto;
  background-color: ${(props) =>
    props.isDisabled ? 'var(--pf-global--disabled-color--300)' : null};
`;
function Lookup(props) {
  const {
    id,
    header,
    onChange,
    onBlur,
    isLoading,
    value,
    multiple,
    required,
    qsConfig,
    renderItemChip,
    renderOptionsList,
    history,
    isDisabled,
    onDebounce,
    fieldName,
    validate,
    modalDescription,
    onUpdate,
  } = props;
  const [typedText, setTypedText] = useState('');
  const debounceRequest = useDebounce(onDebounce, 1000);
  useField({
    name: fieldName,
    validate: (val) => {
      if (!multiple && !val && typedText && typedText !== '') {
        return t`That value was not found. Please enter or select a valid value.`;
      }
      return validate(val);
    },
  });

  const [state, dispatch] = useReducer(
    reducer,
    { value, multiple, required },
    initReducer
  );

  useEffect(() => {
    dispatch({ type: 'SET_MULTIPLE', value: multiple });
  }, [multiple]);

  useEffect(() => {
    dispatch({ type: 'SET_VALUE', value });
    if (value?.name) {
      setTypedText(value.name);
    } else {
      setTypedText('');
    }
  }, [value, multiple]);

  useEffect(() => {
    if (!multiple) {
      setTypedText(state.selectedItems[0] ? state.selectedItems[0].name : '');
    }
  }, [state.selectedItems, multiple]);

  const clearQSParams = () => {
    if (!history.location.search) {
      // This prevents "Warning: Hash history cannot PUSH the same path;
      // a new entry will not be added to the history stack" from appearing in the console.
      return;
    }
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const ns = qsConfig.namespace;
    const otherParts = parts.filter((param) => !param.startsWith(`${ns}.`));
    history.push(`${history.location.pathname}?${otherParts.join('&')}`);
  };

  const save = () => {
    const { selectedItems } = state;
    if (multiple) {
      onChange(selectedItems);
    } else {
      onChange(selectedItems[0] || null);
    }
    clearQSParams();
    dispatch({ type: 'CLOSE_MODAL' });
  };

  const removeItem = (item) => onChange(value.filter((i) => i.id !== item.id));

  const closeModal = () => {
    clearQSParams();
    dispatch({ type: 'CLOSE_MODAL' });
  };

  const onClick = () => {
    onUpdate();
    dispatch({ type: 'TOGGLE_MODAL' });
  };

  const { isModalOpen, selectedItems } = state;
  const canDelete =
    (!required || (multiple && value.length > 1)) && !isDisabled;
  let items = [];
  if (multiple) {
    items = value;
  } else if (value) {
    items.push(value);
  }

  return (
    <>
      <InputGroup onBlur={onBlur}>
        <Button
          aria-label={t`Search`}
          id={`${id}-open`}
          ouiaId={`${id}-open`}
          onClick={onClick}
          variant={ButtonVariant.control}
          isDisabled={isLoading || isDisabled}
        >
          <SearchIcon />
        </Button>
        {multiple ? (
          <ChipHolder isDisabled={isDisabled} className="pf-c-form-control">
            <ChipGroup
              numChips={5}
              totalChips={items.length}
              ouiaId={`${id}-chips`}
            >
              {items.map((item) =>
                renderItemChip({
                  item,
                  removeItem,
                  canDelete,
                })
              )}
            </ChipGroup>
          </ChipHolder>
        ) : (
          <TextInput
            id={id}
            ouiaId={`${id}-input`}
            value={typedText}
            onChange={(inputValue) => {
              setTypedText(inputValue);
              if (value?.name !== inputValue) {
                debounceRequest(inputValue);
              }
            }}
            isDisabled={isLoading || isDisabled}
          />
        )}
      </InputGroup>

      <Modal
        variant="large"
        title={t`Select ${header || t`Items`}`}
        aria-label={t`Lookup modal`}
        isOpen={isModalOpen}
        onClose={closeModal}
        description={state?.selectedItems?.length > 0 && modalDescription}
        ouiaId={`${id}-modal`}
        actions={[
          <Button
            ouiaId="modal-select-button"
            key="select"
            variant="primary"
            onClick={save}
            isDisabled={required && selectedItems.length === 0}
          >
            {t`Select`}
          </Button>,
          <Button
            ouiaId="modal-cancel-button"
            key="cancel"
            variant="link"
            onClick={closeModal}
            aria-label={t`Cancel lookup`}
          >
            {t`Cancel`}
          </Button>,
        ]}
      >
        {renderOptionsList({
          state,
          dispatch,
          canDelete,
        })}
      </Modal>
    </>
  );
}

const Item = shape({
  id: number.isRequired,
});
const InstanceItem = shape({
  id: number.isRequired,
  hostname: string.isRequired,
});

Lookup.propTypes = {
  id: string,
  header: string,
  modalDescription: oneOfType([string, node]),
  onChange: func.isRequired,
  onUpdate: func,
  value: oneOfType([
    Item,
    arrayOf(Item),
    object,
    InstanceItem,
    arrayOf(InstanceItem),
  ]),
  multiple: bool,
  required: bool,
  onBlur: func,
  qsConfig: QSConfig.isRequired,
  renderItemChip: func,
  renderOptionsList: func.isRequired,
  fieldName: string.isRequired,
  validate: func,
  onDebounce: func,
  isDisabled: bool,
};

Lookup.defaultProps = {
  id: 'lookup-search',
  header: null,
  value: null,
  multiple: false,
  required: false,
  modalDescription: '',
  onBlur: () => {},
  renderItemChip: ({ item, removeItem, canDelete }) => (
    <Chip
      key={item.id}
      onClick={() => removeItem(item)}
      isReadOnly={!canDelete}
    >
      {item.name}
    </Chip>
  ),
  validate: () => undefined,
  onDebounce: () => undefined,
  onUpdate: () => {},
  isDisabled: false,
};

export { Lookup as _Lookup };
export default withRouter(Lookup);
