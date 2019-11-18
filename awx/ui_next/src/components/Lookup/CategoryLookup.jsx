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
  ToolbarItem,
} from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

import AnsibleSelect from '../AnsibleSelect';
import PaginatedDataList from '../PaginatedDataList';
import VerticalSeperator from '../VerticalSeparator';
import DataListToolbar from '../DataListToolbar';
import CheckboxListItem from '../CheckboxListItem';
import SelectedList from '../SelectedList';
import { ChipGroup, CredentialChip } from '../Chip';
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

class CategoryLookup extends React.Component {
  constructor(props) {
    super(props);

    // this.assertCorrectValueType();
    let selectedItems = [];
    if (props.value) {
      selectedItems = props.multiple ? [...props.value] : [props.value];
    }
    this.state = {
      isModalOpen: false,
      selectedItems,
      error: null,
    };
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.addItem = this.addItem.bind(this);
    this.removeItem = this.removeItem.bind(this);
    this.saveModal = this.saveModal.bind(this);
    this.clearQSParams = this.clearQSParams.bind(this);
  }

  // assertCorrectValueType() {
  //   const { multiple, value, selectCategoryOptions } = this.props;
  //   if (selectCategoryOptions) {
  //     return;
  //   }
  //   if (!multiple && Array.isArray(value)) {
  //     throw new Error(
  //       'CategoryLookup value must not be an array unless `multiple` is set'
  //     );
  //   }
  //   if (multiple && !Array.isArray(value)) {
  //     throw new Error(
  //       'CategoryLookup value must be an array if `multiple` is set'
  //     );
  //   }
  // }

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

  // TODO: clean up
  handleModalToggle() {
    const { isModalOpen } = this.state;
    const { value, multiple, selectCategory } = this.props;
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
      if (selectCategory) {
        selectCategory(null, 'Machine');
      }
    }
    this.setState(prevState => ({
      isModalOpen: !prevState.isModalOpen,
    }));
  }

  removeItemAndSave(row) {
    const { value, onChange, multiple } = this.props;
    if (multiple) {
      onChange(value.filter(item => item.id !== row.id));
    } else if (value.id === row.id) {
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
    const { isModalOpen, selectedItems, error } = this.state;
    const {
      id,
      items,
      count,
      lookupHeader,
      value,
      columns,
      multiple,
      name,
      onBlur,
      qsConfig,
      required,
      selectCategory,
      selectCategoryOptions,
      selectedCategory,
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
            <ChipGroup>
              {(multiple ? value : [value]).map(chip => (
                <CredentialChip
                  key={chip.id}
                  onClick={() => this.removeItemAndSave(chip)}
                  isReadOnly={!canDelete}
                  credential={chip}
                />
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
          {selectCategoryOptions && selectCategoryOptions.length > 0 && (
            <ToolbarItem css=" display: flex; align-items: center;">
              <span css="flex: 0 0 25%;">Selected Category</span>
              <VerticalSeperator />
              <AnsibleSelect
                css="flex: 1 1 75%;"
                id="multiCredentialsLookUp-select"
                label="Selected Category"
                data={selectCategoryOptions}
                value={selectedCategory.label}
                onChange={selectCategory}
              />
            </ToolbarItem>
          )}
          {selectedItems.length > 0 && (
            <SelectedList
              label={i18n._(t`Selected`)}
              selected={selectedItems}
              showOverflowAfter={5}
              onRemove={this.removeItem}
              isReadOnly={!canDelete}
              isCredentialList={
                selectCategoryOptions && selectCategoryOptions.length > 0
              }
            />
          )}
          <PaginatedDataList
            items={items}
            itemCount={count}
            pluralizedItemName={lookupHeader}
            qsConfig={qsConfig}
            toolbarColumns={columns}
            renderItem={item => (
              <CheckboxListItem
                key={item.id}
                itemId={item.id}
                name={multiple ? item.name : name}
                label={item.name}
                isSelected={selectedItems.some(i => i.id === item.id)}
                onSelect={() => this.addItem(item)}
                isRadio={
                  !multiple ||
                  (selectCategoryOptions &&
                    selectCategoryOptions.length &&
                    selectedCategory.value !== 'Vault')
                }
              />
            )}
            renderToolbar={props => <DataListToolbar {...props} fillWidth />}
            showPageSizeOptions={false}
          />
          {error ? <div>error: {error.message}</div> : ''}
        </Modal>
      </Fragment>
    );
  }
}

const Item = shape({
  id: number.isRequired,
});

CategoryLookup.propTypes = {
  id: string,
  items: arrayOf(shape({})).isRequired,
  // TODO: change to `header`
  lookupHeader: string,
  name: string,
  onChange: func.isRequired,
  value: oneOfType([Item, arrayOf(Item)]),
  multiple: bool,
  required: bool,
  qsConfig: QSConfig.isRequired,
  selectCategory: func.isRequired,
  selectCategoryOptions: oneOfType(shape({})).isRequired,
  selectedCategory: shape({}).isRequired,
};

CategoryLookup.defaultProps = {
  id: 'lookup-search',
  lookupHeader: null,
  name: null,
  value: null,
  multiple: false,
  required: false,
};

export { CategoryLookup as _CategoryLookup };
export default withI18n()(withRouter(CategoryLookup));
