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
import { ChipGroup, Chip, CredentialChip } from '../Chip';
import { getQSConfig, parseQueryString } from '../../util/qs';

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

class Lookup extends React.Component {
  constructor(props) {
    super(props);

    this.assertCorrectValueType();
    let lookupSelectedItems = [];
    if (props.value) {
      lookupSelectedItems = props.multiple ? [...props.value] : [props.value];
    }
    this.state = {
      isModalOpen: false,
      lookupSelectedItems,
      results: [],
      count: 0,
      error: null,
    };
    this.qsConfig = getQSConfig(props.qsNamespace, {
      page: 1,
      page_size: 5,
      order_by: props.sortedColumnKey,
    });
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.toggleSelected = this.toggleSelected.bind(this);
    this.saveModal = this.saveModal.bind(this);
    this.getData = this.getData.bind(this);
    this.clearQSParams = this.clearQSParams.bind(this);
  }

  componentDidMount() {
    this.getData();
  }

  componentDidUpdate(prevProps) {
    const { location, selectedCategory } = this.props;
    if (
      location !== prevProps.location ||
      prevProps.selectedCategory !== selectedCategory
    ) {
      this.getData();
    }
  }

  assertCorrectValueType() {
    const { multiple, value, selectCategoryOptions } = this.props;
    if (selectCategoryOptions) {
      return;
    }
    if (!multiple && Array.isArray(value)) {
      throw new Error(
        'Lookup value must not be an array unless `multiple` is set'
      );
    }
    if (multiple && !Array.isArray(value)) {
      throw new Error('Lookup value must be an array if `multiple` is set');
    }
  }

  async getData() {
    const {
      getItems,
      location: { search },
    } = this.props;
    const queryParams = parseQueryString(this.qsConfig, search);

    this.setState({ error: false });
    try {
      const { data } = await getItems(queryParams);
      const { results, count } = data;

      this.setState({
        results,
        count,
      });
    } catch (err) {
      this.setState({ error: true });
    }
  }

  toggleSelected(row) {
    const {
      name,
      onLookupSave,
      multiple,
      onToggleItem,
      selectCategoryOptions,
    } = this.props;
    const {
      lookupSelectedItems: updatedSelectedItems,
      isModalOpen,
    } = this.state;

    const selectedIndex = updatedSelectedItems.findIndex(
      selectedRow => selectedRow.id === row.id
    );
    if (multiple) {
      if (selectCategoryOptions) {
        onToggleItem(row, isModalOpen);
      }
      if (selectedIndex > -1) {
        updatedSelectedItems.splice(selectedIndex, 1);
        this.setState({ lookupSelectedItems: updatedSelectedItems });
      } else {
        this.setState(prevState => ({
          lookupSelectedItems: [...prevState.lookupSelectedItems, row],
        }));
      }
    } else {
      this.setState({ lookupSelectedItems: [row] });
    }

    // Updates the selected items from parent state
    // This handles the case where the user removes chips from the lookup input
    // while the modal is closed
    if (!isModalOpen) {
      onLookupSave(updatedSelectedItems, name);
    }
  }

  handleModalToggle() {
    const { isModalOpen } = this.state;
    const { value, multiple, selectCategory } = this.props;
    // Resets the selected items from parent state whenever modal is opened
    // This handles the case where the user closes/cancels the modal and
    // opens it again
    if (!isModalOpen) {
      let lookupSelectedItems = [];
      if (value) {
        lookupSelectedItems = multiple ? [...value] : [value];
      }
      this.setState({ lookupSelectedItems });
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

  saveModal() {
    const { onLookupSave, name, multiple } = this.props;
    const { lookupSelectedItems } = this.state;
    const value = multiple
      ? lookupSelectedItems
      : lookupSelectedItems[0] || null;

    this.handleModalToggle();
    onLookupSave(value, name);
  }

  clearQSParams() {
    const { history } = this.props;
    const parts = history.location.search.replace(/^\?/, '').split('&');
    const ns = this.qsConfig.namespace;
    const otherParts = parts.filter(param => !param.startsWith(`${ns}.`));
    history.push(`${history.location.pathname}?${otherParts.join('&')}`);
  }

  render() {
    const {
      isModalOpen,
      lookupSelectedItems,
      error,
      results,
      count,
    } = this.state;
    const {
      form,
      id,
      lookupHeader,
      value,
      columns,
      multiple,
      name,
      onBlur,
      selectCategory,
      required,
      i18n,
      selectCategoryOptions,
      selectedCategory,
    } = this.props;
    const header = lookupHeader || i18n._(t`Items`);
    const canDelete = !required || (multiple && value.length > 1);
    const chips = () => {
      return selectCategoryOptions && selectCategoryOptions.length > 0 ? (
        <ChipGroup>
          {(multiple ? value : [value]).map(chip => (
            <CredentialChip
              key={chip.id}
              onClick={() => this.toggleSelected(chip)}
              isReadOnly={!canDelete}
              credential={chip}
            />
          ))}
        </ChipGroup>
      ) : (
        <ChipGroup>
          {(multiple ? value : [value]).map(chip => (
            <Chip
              key={chip.id}
              onClick={() => this.toggleSelected(chip)}
              isReadOnly={!canDelete}
            >
              {chip.name}
            </Chip>
          ))}
        </ChipGroup>
      );
    };
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
            {value ? chips(value) : null}
          </ChipHolder>
        </InputGroup>
        <Modal
          className="awx-c-modal"
          title={i18n._(t`Select ${header}`)}
          isOpen={isModalOpen}
          onClose={this.handleModalToggle}
          actions={[
            <Button
              key="save"
              variant="primary"
              onClick={this.saveModal}
              style={results.length === 0 ? { display: 'none' } : {}}
            >
              {i18n._(t`Save`)}
            </Button>,
            <Button
              key="cancel"
              variant="secondary"
              onClick={this.handleModalToggle}
            >
              {results.length === 0 ? i18n._(t`Close`) : i18n._(t`Cancel`)}
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
                form={form}
              />
            </ToolbarItem>
          )}
          <PaginatedDataList
            items={results}
            itemCount={count}
            pluralizedItemName={lookupHeader}
            qsConfig={this.qsConfig}
            toolbarColumns={columns}
            renderItem={item => (
              <CheckboxListItem
                key={item.id}
                itemId={item.id}
                name={multiple ? item.name : name}
                label={item.name}
                isSelected={
                  selectCategoryOptions
                    ? value.some(i => i.id === item.id)
                    : lookupSelectedItems.some(i => i.id === item.id)
                }
                onSelect={() => this.toggleSelected(item)}
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
          {lookupSelectedItems.length > 0 && (
            <SelectedList
              label={i18n._(t`Selected`)}
              selected={selectCategoryOptions ? value : lookupSelectedItems}
              showOverflowAfter={5}
              onRemove={this.toggleSelected}
              isReadOnly={!canDelete}
              isCredentialList={
                selectCategoryOptions && selectCategoryOptions.length > 0
              }
            />
          )}
          {error ? <div>error</div> : ''}
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
  getItems: func.isRequired,
  lookupHeader: string,
  name: string,
  onLookupSave: func.isRequired,
  value: oneOfType([Item, arrayOf(Item)]),
  sortedColumnKey: string.isRequired,
  multiple: bool,
  required: bool,
  qsNamespace: string,
};

Lookup.defaultProps = {
  id: 'lookup-search',
  lookupHeader: null,
  name: null,
  value: null,
  multiple: false,
  required: false,
  qsNamespace: 'lookup',
};

export { Lookup as _Lookup };
export default withI18n()(withRouter(Lookup));
