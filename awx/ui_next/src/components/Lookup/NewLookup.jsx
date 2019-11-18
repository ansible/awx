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
  InputGroup as PFInputGroup,
  Modal,
} from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

import reducer, { initReducer } from './shared/reducer';
import SelectList from './shared/SelectList';
import { ChipGroup, Chip } from '../Chip';
import { QSConfig } from '@types';

const SearchButton = styled(Button)`
  ::after {
    border: var(--pf-c-button--BorderWidth) solid
      var(--pf-global--BorderColor--200);
  }
`;

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
  border-top-right-radius: 3px;
  border-bottom-right-radius: 3px;
`;

function Lookup(props) {
  const {
    id,
    items,
    count,
    header,
    name,
    onChange,
    onBlur,
    columns,
    value,
    multiple,
    required,
    qsConfig,
    i18n,
  } = props;
  const [state, dispatch] = useReducer(reducer, props, initReducer);

  useEffect(() => {
    dispatch({ type: 'SET_MULTIPLE', value: multiple });
  }, [multiple]);

  useEffect(() => {
    dispatch({ type: 'SET_VALUE', value });
  }, [value]);

  const save = () => {
    const { selectedItems } = state;
    const val = multiple ? selectedItems : selectedItems[0] || null;
    onChange(val);
    dispatch({ type: 'CLOSE_MODAL' });
  };

  const removeItem = item => {
    if (multiple) {
      onChange(value.filter(i => i.id !== item.id));
    } else {
      onChange(null);
    }
  };

  const { isModalOpen, selectedItems } = state;

  const canDelete = !required || (multiple && value.length > 1);
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
          <ChipGroup>
            {(multiple ? value : [value]).map(item => (
              <Chip
                key={item.id}
                onClick={() => removeItem(item)}
                isReadOnly={!canDelete}
              >
                {item.name}
              </Chip>
            ))}
          </ChipGroup>
        </ChipHolder>
      </InputGroup>
      <Modal
        className="awx-c-modal"
        title={i18n._(t`Select ${header || i18n._(t`Items`)}`)}
        isOpen={isModalOpen}
        onClose={() => dispatch({ type: 'TOGGLE_MODAL' })}
        actions={[
          <Button
            key="select"
            variant="primary"
            onClick={save}
            style={
              required && selectedItems.length === 0 ? { display: 'none' } : {}
            }
          >
            {i18n._(t`Select`)}
          </Button>,
          <Button
            key="cancel"
            variant="secondary"
            onClick={() => dispatch({ type: 'TOGGLE_MODAL' })}
          >
            {i18n._(t`Cancel`)}
          </Button>,
        ]}
      >
        <SelectList
          value={selectedItems}
          options={items}
          optionCount={count}
          columns={columns}
          multiple={multiple}
          header={header}
          name={name}
          qsConfig={qsConfig}
          readOnly={!canDelete}
          dispatch={dispatch}
        />
      </Modal>
    </Fragment>
  );
}

const Item = shape({
  id: number.isRequired,
});

Lookup.propTypes = {
  id: string,
  items: arrayOf(shape({})).isRequired,
  count: number.isRequired,
  // TODO: change to `header`
  header: string,
  name: string,
  onChange: func.isRequired,
  value: oneOfType([Item, arrayOf(Item)]),
  multiple: bool,
  required: bool,
  onBlur: func,
  qsConfig: QSConfig.isRequired,
};

Lookup.defaultProps = {
  id: 'lookup-search',
  header: null,
  name: null,
  value: null,
  multiple: false,
  required: false,
  onBlur: () => {},
};

export { Lookup as _Lookup };
export default withI18n()(withRouter(Lookup));
