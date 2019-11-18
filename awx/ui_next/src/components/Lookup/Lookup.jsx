import React, { Fragment } from 'react';
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
  --pf-c-form-control--Height: auto;
  border-top-right-radius: 3px;
  border-bottom-right-radius: 3px;
`;

class Lookup extends React.Component {
  constructor(props) {
    super(props);

    this.assertCorrectValueType();
    let selectedItems = [];
    if (props.value) {
      selectedItems = props.multiple ? [...props.value] : [props.value];
    }
    this.state = {
      isModalOpen: false,
      selectedItems,
    };
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.addItem = this.addItem.bind(this);
    this.removeItem = this.removeItem.bind(this);
    this.saveModal = this.saveModal.bind(this);
    this.clearQSParams = this.clearQSParams.bind(this);
  }

  assertCorrectValueType() {
    const { multiple, value } = this.props;
    if (!multiple && Array.isArray(value)) {
      throw new Error(
        'Lookup value must not be an array unless `multiple` is set'
      );
    }
    if (multiple && !Array.isArray(value)) {
      throw new Error('Lookup value must be an array if `multiple` is set');
    }
  }

  removeItem(row) {
    const { selectedItems } = this.state;
    const { onToggleItem } = this.props;
    if (onToggleItem) {
      this.setState({ selectedItems: onToggleItem(selectedItems, row) });
      return;
    }
    this.setState({
      selectedItems: selectedItems.filter(item => item.id !== row.id),
    });
  }

  addItem(row) {
    const { selectedItems } = this.state;
    const { multiple, onToggleItem } = this.props;
    if (onToggleItem) {
      this.setState({ selectedItems: onToggleItem(selectedItems, row) });
      return;
    }
    const index = selectedItems.findIndex(item => item.id === row.id);

    if (!multiple) {
      this.setState({ selectedItems: [row] });
      return;
    }
    if (index > -1) {
      return;
    }
    this.setState({ selectedItems: [...selectedItems, row] });
  }

  // TODO: cleanup
  handleModalToggle() {
    const { isModalOpen } = this.state;
    const { value, multiple } = this.props;
    // Resets the selected items from parent state whenever modal is opened
    // This handles the case where the user closes/cancels the modal and
    // opens it again
    if (!isModalOpen) {
      let selectedItems = [];
      if (value) {
        selectedItems = multiple ? [...value] : [value];
      }
      this.setState({ selectedItems });
    } else {
      this.clearQSParams();
    }
    this.setState(prevState => ({
      isModalOpen: !prevState.isModalOpen,
    }));
  }

  removeItemAndSave(item) {
    const { value, onChange, multiple } = this.props;
    if (multiple) {
      onChange(value.filter(i => i.id !== item.id));
    } else if (value.id === item.id) {
      onChange(null);
    }
  }

  saveModal() {
    const { onChange, multiple } = this.props;
    const { selectedItems } = this.state;
    const value = multiple ? selectedItems : selectedItems[0] || null;

    this.handleModalToggle();
    onChange(value);
  }

  clearQSParams() {
    const { qsConfig, history } = this.props;
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const ns = qsConfig.namespace;
    const otherParts = parts.filter(param => !param.startsWith(`${ns}.`));
    history.push(`${history.location.pathname}?${otherParts.join('&')}`);
  }

  render() {
    const { isModalOpen, selectedItems } = this.state;
    const {
      id,
      lookupHeader,
      value,
      items,
      count,
      columns,
      multiple,
      name,
      onBlur,
      required,
      qsConfig,
      i18n,
    } = this.props;
    const header = lookupHeader || i18n._(t`Items`);
    const canDelete = !required || (multiple && value.length > 1);
    return (
      <Fragment>
        <InputGroup onBlur={onBlur}>
          <SearchButton
            aria-label="Search"
            id={id}
            onClick={this.handleModalToggle}
            variant={ButtonVariant.tertiary}
          >
            <SearchIcon />
          </SearchButton>
          <ChipHolder className="pf-c-form-control">
            <ChipGroup defaultIsOpen numChips={5}>
              {(multiple ? value : [value]).map(chip => (
                <Chip
                  key={chip.id}
                  onClick={() => this.removeItemAndSave(chip)}
                  isReadOnly={!canDelete}
                >
                  {chip.name}
                </Chip>
              ))}
            </ChipGroup>
          </ChipHolder>
        </InputGroup>
        <Modal
          className="awx-c-modal"
          title={i18n._(t`Select ${header}`)}
          isOpen={isModalOpen}
          onClose={this.handleModalToggle}
          actions={[
            <Button
              key="select"
              variant="primary"
              onClick={this.saveModal}
              style={selectedItems.length === 0 ? { display: 'none' } : {}}
            >
              {i18n._(t`Select`)}
            </Button>,
            <Button
              key="cancel"
              variant="secondary"
              onClick={this.handleModalToggle}
            >
              {i18n._(t`Cancel`)}
            </Button>,
          ]}
        >
          <SelectList
            value={selectedItems}
            onChange={newVal => this.setState({ selectedItems: newVal })}
            options={items}
            optionCount={count}
            columns={columns}
            multiple={multiple}
            header={lookupHeader}
            name={name}
            qsConfig={qsConfig}
            readOnly={!canDelete}
          />
        </Modal>
      </Fragment>
    );
  }
}

const Item = shape({
  id: number.isRequired,
});

Lookup.propTypes = {
  id: string,
  items: arrayOf(shape({})).isRequired,
  count: number.isRequired,
  // TODO: change to `header`
  lookupHeader: string,
  name: string,
  onChange: func.isRequired,
  value: oneOfType([Item, arrayOf(Item)]),
  multiple: bool,
  required: bool,
  qsConfig: QSConfig.isRequired,
};

Lookup.defaultProps = {
  id: 'lookup-search',
  lookupHeader: null,
  name: null,
  value: null,
  multiple: false,
  required: false,
};

export { Lookup as _Lookup };
export default withI18n()(withRouter(Lookup));
