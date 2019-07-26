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
  Modal as PFModal,
} from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';

import PaginatedDataList from '../PaginatedDataList';
import DataListToolbar from '../DataListToolbar';
import CheckboxListItem from '../CheckboxListItem';
import SelectedList from '../SelectedList';
import { ChipGroup, Chip } from '../Chip';
import { getQSConfig, parseNamespacedQueryString } from '../../util/qs';

const InputGroup = styled(PFInputGroup)`
  ${props =>
    props.multiple &&
    `
    --pf-c-form-control--Height: 90px;
    overflow-y: auto;
  `}
`;

const Modal = styled(PFModal)`
  --pf-c-modal-box--body--MinHeight: 460px;
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
    this.qsConfig = getQSConfig('lookup', {
      page: 1,
      page_size: 5,
      order_by: props.sortedColumnKey,
    });
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.toggleSelected = this.toggleSelected.bind(this);
    this.saveModal = this.saveModal.bind(this);
    this.getData = this.getData.bind(this);
  }

  componentDidMount() {
    this.getData();
  }

  componentDidUpdate(prevProps) {
    const { location } = this.props;
    if (location !== prevProps.location) {
      this.getData();
    }
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

  async getData() {
    const {
      getItems,
      location: { search },
    } = this.props;
    const queryParams = parseNamespacedQueryString(this.qsConfig, search);

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
    const { name, onLookupSave, multiple } = this.props;
    const {
      lookupSelectedItems: updatedSelectedItems,
      isModalOpen,
    } = this.state;

    const selectedIndex = updatedSelectedItems.findIndex(
      selectedRow => selectedRow.id === row.id
    );

    if (multiple) {
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
    const { value, multiple } = this.props;
    // Resets the selected items from parent state whenever modal is opened
    // This handles the case where the user closes/cancels the modal and
    // opens it again
    if (!isModalOpen) {
      let lookupSelectedItems = [];
      if (value) {
        lookupSelectedItems = multiple ? [...value] : [value];
      }
      this.setState({ lookupSelectedItems });
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
    onLookupSave(value, name);
    this.handleModalToggle();
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
      id,
      lookupHeader,
      value,
      columns,
      multiple,
      name,
      required,
      i18n,
    } = this.props;

    const header = lookupHeader || i18n._(t`items`);
    const canDelete = !required || (multiple && value.length > 1);

    const chips = value ? (
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
    ) : null;

    return (
      <Fragment>
        <InputGroup>
          <Button
            aria-label="Search"
            id={id}
            onClick={this.handleModalToggle}
            variant={ButtonVariant.tertiary}
          >
            <SearchIcon />
          </Button>
          <div className="pf-c-form-control">{chips}</div>
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
          <PaginatedDataList
            items={results}
            itemCount={count}
            itemName={lookupHeader}
            qsConfig={this.qsConfig}
            toolbarColumns={columns}
            renderItem={item => (
              <CheckboxListItem
                key={item.id}
                itemId={item.id}
                name={multiple ? item.name : name}
                label={item.name}
                isSelected={lookupSelectedItems.some(i => i.id === item.id)}
                onSelect={() => this.toggleSelected(item)}
                isRadio={!multiple}
              />
            )}
            renderToolbar={props => <DataListToolbar {...props} fillWidth />}
            showPageSizeOptions={false}
          />
          {lookupSelectedItems.length > 0 && (
            <SelectedList
              label={i18n._(t`Selected`)}
              selected={lookupSelectedItems}
              showOverflowAfter={5}
              onRemove={this.toggleSelected}
              isReadOnly={!canDelete}
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
