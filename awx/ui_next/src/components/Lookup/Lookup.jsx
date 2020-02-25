import React, { Fragment, useReducer, useEffect } from 'react';
import {
  string,
  bool,
  arrayOf,
  func,
  number,
  oneOfType,
  shape,
} from 'prop-types';
import { withRouter } from 'react-router-dom';
import { SearchIcon } from '@patternfly/react-icons';
import {
  Button,
  ButtonVariant,
  Chip,
  ChipGroup,
  InputGroup as PFInputGroup,
  Modal,
} from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

import reducer, { initReducer } from './shared/reducer';
import { QSConfig } from '@types';

const SearchButton = styled(Button)`
  ::after {
    border: var(--pf-c-button--BorderWidth) solid
      var(--pf-global--BorderColor--200);
  }
`;
SearchButton.displayName = 'SearchButton';

const InputGroup = styled(PFInputGroup)`
  ${props =>
    props.multiple &&
    `
    --pf-c-form-control--Height: 90px;
    overflow-y: auto;
  `}
`;

const ChipHolder = styled.div`
  --pf-c-form-control--BorderTopColor: var(--pf-global--BorderColor--200);
  --pf-c-form-control--BorderRightColor: var(--pf-global--BorderColor--200);
  --pf-c-form-control--Height: auto;
  border-top-right-radius: 3px;
  border-bottom-right-radius: 3px;
`;

function Lookup(props) {
  const {
    id,
    header,
    onChange,
    onBlur,
    value,
    multiple,
    required,
    qsConfig,
    renderItemChip,
    renderOptionsList,
    history,
    i18n,
  } = props;

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
  }, [value]);

  const clearQSParams = () => {
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const ns = qsConfig.namespace;
    const otherParts = parts.filter(param => !param.startsWith(`${ns}.`));
    history.push(`${history.location.pathname}?${otherParts.join('&')}`);
  };

  const save = () => {
    const { selectedItems } = state;
    const val = multiple ? selectedItems : selectedItems[0] || null;
    onChange(val);
    clearQSParams();
    dispatch({ type: 'CLOSE_MODAL' });
  };

  const removeItem = item => {
    if (multiple) {
      onChange(value.filter(i => i.id !== item.id));
    } else {
      onChange(null);
    }
  };

  const closeModal = () => {
    clearQSParams();
    dispatch({ type: 'CLOSE_MODAL' });
  };

  const { isModalOpen, selectedItems } = state;
  const canDelete = !required || (multiple && value.length > 1);
  let items = [];
  if (multiple) {
    items = value;
  } else if (value) {
    items.push(value);
  }
  return (
    <Fragment>
      <InputGroup onBlur={onBlur}>
        <SearchButton
          aria-label="Search"
          id={id}
          onClick={() => dispatch({ type: 'TOGGLE_MODAL' })}
          variant={ButtonVariant.tertiary}
        >
          <SearchIcon />
        </SearchButton>
        <ChipHolder className="pf-c-form-control">
          <ChipGroup numChips={5}>
            {items.map(item =>
              renderItemChip({
                item,
                removeItem,
                canDelete,
              })
            )}
          </ChipGroup>
        </ChipHolder>
      </InputGroup>
      <Modal
        isFooterLeftAligned
        isLarge
        title={i18n._(t`Select ${header || i18n._(t`Items`)}`)}
        isOpen={isModalOpen}
        onClose={closeModal}
        actions={[
          <Button
            key="select"
            variant="primary"
            onClick={save}
            isDisabled={required && selectedItems.length === 0}
          >
            {i18n._(t`Select`)}
          </Button>,
          <Button key="cancel" variant="secondary" onClick={closeModal}>
            {i18n._(t`Cancel`)}
          </Button>,
        ]}
      >
        {renderOptionsList({
          state,
          dispatch,
          canDelete,
        })}
      </Modal>
    </Fragment>
  );
}

const Item = shape({
  id: number.isRequired,
});

Lookup.propTypes = {
  id: string,
  header: string,
  onChange: func.isRequired,
  value: oneOfType([Item, arrayOf(Item)]),
  multiple: bool,
  required: bool,
  onBlur: func,
  qsConfig: QSConfig.isRequired,
  renderItemChip: func,
  renderOptionsList: func.isRequired,
};

Lookup.defaultProps = {
  id: 'lookup-search',
  header: null,
  value: null,
  multiple: false,
  required: false,
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
};

export { Lookup as _Lookup };
export default withI18n()(withRouter(Lookup));
