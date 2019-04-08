import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { SearchIcon, CubesIcon } from '@patternfly/react-icons';
import {
  Button,
  ButtonVariant,
  Chip,
  EmptyState,
  EmptyStateBody,
  EmptyStateIcon,
  InputGroup,
  Modal,
  Title
} from '@patternfly/react-core';
import { I18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import CheckboxListItem from '../ListItem';
import DataListToolbar from '../DataListToolbar';
import SelectedList from '../SelectedList';
import Pagination from '../Pagination';

const paginationStyling = {
  paddingLeft: '0',
  justifyContent: 'flex-end',
  borderRight: '1px solid #ebebeb',
  borderBottom: '1px solid #ebebeb',
  borderTop: '0'
};

class Lookup extends React.Component {
  constructor (props) {
    super(props);

    this.state = {
      isModalOpen: false,
      lookupSelectedItems: [...props.value] || [],
      results: [],
      count: 0,
      page: 1,
      page_size: 5,
      error: null,
      sortOrder: 'ascending',
      sortedColumnKey: props.sortedColumnKey
    };
    this.onSetPage = this.onSetPage.bind(this);
    this.handleModalToggle = this.handleModalToggle.bind(this);
    this.toggleSelected = this.toggleSelected.bind(this);
    this.saveModal = this.saveModal.bind(this);
    this.getData = this.getData.bind(this);
    this.onSearch = this.onSearch.bind(this);
    this.onSort = this.onSort.bind(this);
  }

  componentDidMount () {
    const { page_size, page } = this.state;
    this.getData({ page_size, page });
  }

  onSearch () {
    const { sortedColumnKey, sortOrder } = this.state;
    this.onSort(sortedColumnKey, sortOrder);
  }

  onSort (sortedColumnKey, sortOrder) {
    this.setState({ page: 1, sortedColumnKey, sortOrder }, this.getData);
  }

  async getData () {
    const { getItems } = this.props;
    const { page, page_size, sortedColumnKey, sortOrder } = this.state;

    this.setState({ error: false });

    const queryParams = {
      page,
      page_size
    };

    if (sortedColumnKey) {
      queryParams.order_by = sortOrder === 'descending' ? `-${sortedColumnKey}` : sortedColumnKey;
    }

    try {
      const { data } = await getItems(queryParams);
      const { results, count } = data;

      const stateToUpdate = {
        results,
        count
      };

      this.setState(stateToUpdate);
    } catch (err) {
      this.setState({ error: true });
    }
  }

  onSetPage = async (pageNumber, pageSize) => {
    const page = parseInt(pageNumber, 10);
    const page_size = parseInt(pageSize, 10);
    this.setState({ page, page_size }, this.getData);
  };

  toggleSelected (row) {
    const { name, onLookupSave } = this.props;
    const { lookupSelectedItems: updatedSelectedItems, isModalOpen } = this.state;

    const selectedIndex = updatedSelectedItems
      .findIndex(selectedRow => selectedRow.id === row.id);

    if (selectedIndex > -1) {
      updatedSelectedItems.splice(selectedIndex, 1);
      this.setState({ lookupSelectedItems: updatedSelectedItems });
    } else {
      this.setState(prevState => ({
        lookupSelectedItems: [...prevState.lookupSelectedItems, row]
      }));
    }

    // Updates the selected items from parent state
    // This handles the case where the user removes chips from the lookup input
    // while the modal is closed
    if (!isModalOpen) {
      onLookupSave(updatedSelectedItems, name);
    }
  }

  handleModalToggle () {
    const { isModalOpen } = this.state;
    const { value } = this.props;
    // Resets the selected items from parent state whenever modal is opened
    // This handles the case where the user closes/cancels the modal and
    // opens it again
    if (!isModalOpen) {
      this.setState({ lookupSelectedItems: [...value] });
    }
    this.setState((prevState) => ({
      isModalOpen: !prevState.isModalOpen,
    }));
  }

  saveModal () {
    const { onLookupSave, name } = this.props;
    const { lookupSelectedItems } = this.state;
    onLookupSave(lookupSelectedItems, name);
    this.handleModalToggle();
  }

  render () {
    const {
      isModalOpen,
      lookupSelectedItems,
      error,
      results,
      count,
      page,
      page_size,
      sortedColumnKey,
      sortOrder
    } = this.state;
    const { id, lookupHeader = 'items', value, columns } = this.props;

    const chips = value ? (
      <div className="pf-c-chip-group">
        {value.map(chip => (
          <Chip key={chip.id} onClick={() => this.toggleSelected(chip)}>
            {chip.name}
          </Chip>
        ))}
      </div>
    ) : null;

    return (
      <I18n>
        {({ i18n }) => (
          <Fragment>
            <InputGroup className="awx-lookup">
              <Button
                aria-label="Search"
                id={id}
                onClick={this.handleModalToggle}
                variant={ButtonVariant.tertiary}
              >
                <SearchIcon />
              </Button>
              <div className="pf-c-form-control">
                {chips}
              </div>
            </InputGroup>
            <Modal
              className="awx-c-modal"
              title={`Select ${lookupHeader}`}
              isOpen={isModalOpen}
              onClose={this.handleModalToggle}
              actions={[
                <Button key="save" variant="primary" onClick={this.saveModal} style={(results.length === 0) ? { display: 'none' } : {}}>{i18n._(t`Save`)}</Button>,
                <Button key="cancel" variant="secondary" onClick={this.handleModalToggle}>{(results.length === 0) ? i18n._(t`Close`) : i18n._(t`Cancel`)}</Button>
              ]}
            >
              {(results.length === 0) ? (
                <EmptyState>
                  <EmptyStateIcon icon={CubesIcon} />
                  <Title size="lg">
                    <Trans>{`No ${lookupHeader} Found`}</Trans>
                  </Title>
                  <EmptyStateBody>
                    <Trans>{`Please add ${lookupHeader.toLowerCase()} to populate this list`}</Trans>
                  </EmptyStateBody>
                </EmptyState>
              ) : (
                <Fragment>
                  <DataListToolbar
                    sortedColumnKey={sortedColumnKey}
                    sortOrder={sortOrder}
                    columns={columns}
                    onSearch={this.onSearch}
                    onSort={this.onSort}
                    isLookup
                  />
                  <ul className="pf-c-data-list awx-c-list">
                    {results.map(i => (
                      <CheckboxListItem
                        key={i.id}
                        itemId={i.id}
                        name={i.name}
                        isSelected={lookupSelectedItems.some(item => item.id === i.id)}
                        onSelect={() => this.toggleSelected(i)}
                      />
                    ))}
                  </ul>
                  <Pagination
                    count={count}
                    page={page}
                    pageCount={Math.ceil(count / page_size)}
                    page_size={page_size}
                    onSetPage={this.onSetPage}
                    pageSizeOptions={null}
                    showPageSizeOptions={false}
                    style={paginationStyling}
                  />
                </Fragment>
              )}
              {lookupSelectedItems.length > 0 && (
                <SelectedList
                  label={i18n._(t`Selected`)}
                  selected={lookupSelectedItems}
                  showOverflowAfter={5}
                  onRemove={this.toggleSelected}
                />
              )}
              { error ? <div>error</div> : '' }
            </Modal>
          </Fragment>
        )}
      </I18n>
    );
  }
}

Lookup.propTypes = {
  id: PropTypes.string,
  getItems: PropTypes.func.isRequired,
  lookupHeader: PropTypes.string,
  name: PropTypes.string,
  onLookupSave: PropTypes.func.isRequired,
  value: PropTypes.arrayOf(PropTypes.object).isRequired,
};

Lookup.defaultProps = {
  id: 'lookup-search',
  lookupHeader: 'items',
  name: null,
};

export default Lookup;
