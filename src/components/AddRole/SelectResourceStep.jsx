import React, { Fragment } from 'react';
import PropTypes from 'prop-types';

import { i18nMark } from '@lingui/react';

import {
  EmptyState,
  EmptyStateBody,
  EmptyStateIcon,
  Title,
} from '@patternfly/react-core';

import { CubesIcon } from '@patternfly/react-icons';

import CheckboxListItem from '../ListItem';
import DataListToolbar from '../DataListToolbar';
import Pagination from '../Pagination';
import SelectedList from '../SelectedList';

const paginationStyling = {
  paddingLeft: '0',
  justifyContent: 'flex-end',
  borderRight: '1px solid #ebebeb',
  borderBottom: '1px solid #ebebeb',
  borderTop: '0'
};

class SelectResourceStep extends React.Component {
  constructor (props) {
    super(props);

    const { sortedColumnKey } = this.props;

    this.state = {
      count: null,
      error: false,
      page: 1,
      page_size: 5,
      resources: [],
      sortOrder: 'ascending',
      sortedColumnKey
    };

    this.handleSetPage = this.handleSetPage.bind(this);
    this.handleSort = this.handleSort.bind(this);
    this.readResourceList = this.readResourceList.bind(this);
  }

  componentDidMount () {
    const { page_size, page, sortedColumnKey } = this.state;

    this.readResourceList({ page_size, page, order_by: sortedColumnKey });
  }

  handleSetPage (pageNumber) {
    const { page_size, sortedColumnKey, sortOrder } = this.state;
    const page = parseInt(pageNumber, 10);

    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    this.readResourceList({ page_size, page, order_by });
  }

  handleSort (sortedColumnKey, sortOrder) {
    const { page_size } = this.state;

    let order_by = sortedColumnKey;

    if (sortOrder === 'descending') {
      order_by = `-${order_by}`;
    }

    this.readResourceList({ page: 1, page_size, order_by });
  }

  async readResourceList (queryParams) {
    const { onSearch } = this.props;
    const { page, order_by } = queryParams;

    let sortOrder = 'ascending';
    let sortedColumnKey = order_by;

    if (order_by.startsWith('-')) {
      sortOrder = 'descending';
      sortedColumnKey = order_by.substring(1);
    }

    this.setState({ error: false });

    try {
      const { data } = await onSearch(queryParams);
      const { count, results } = data;

      const stateToUpdate = {
        count,
        page,
        resources: results,
        sortOrder,
        sortedColumnKey
      };

      this.setState(stateToUpdate);
    } catch (err) {
      this.setState({ error: true });
    }
  }

  render () {
    const {
      count,
      error,
      page,
      page_size,
      resources,
      sortOrder,
      sortedColumnKey
    } = this.state;

    const {
      columns,
      displayKey,
      emptyListBody,
      emptyListTitle,
      onRowClick,
      selectedLabel,
      selectedResourceRows
    } = this.props;

    return (
      <Fragment>
        <Fragment>
          {(resources.length === 0) ? (
            <EmptyState>
              <EmptyStateIcon icon={CubesIcon} />
              <Title size="lg">
                {emptyListTitle}
              </Title>
              <EmptyStateBody>
                {emptyListBody}
              </EmptyStateBody>
            </EmptyState>
          ) : (
            <Fragment>
              {selectedResourceRows.length > 0 && (
                <SelectedList
                  displayKey={displayKey}
                  label={selectedLabel}
                  onRemove={onRowClick}
                  selected={selectedResourceRows}
                  showOverflowAfter={5}
                />
              )}
              <DataListToolbar
                columns={columns}
                noLeftMargin
                onSearch={this.onSearch}
                handleSort={this.handleSort}
                sortOrder={sortOrder}
                sortedColumnKey={sortedColumnKey}
              />
              <ul className="pf-c-data-list awx-c-list">
                {resources.map(i => (
                  <CheckboxListItem
                    isSelected={selectedResourceRows.some(item => item.id === i.id)}
                    itemId={i.id}
                    key={i.id}
                    name={i[displayKey]}
                    onSelect={() => onRowClick(i)}
                  />
                ))}
              </ul>
              <Pagination
                count={count}
                onSetPage={this.handleSetPage}
                page={page}
                pageCount={Math.ceil(count / page_size)}
                pageSizeOptions={null}
                page_size={page_size}
                showPageSizeOptions={false}
                style={paginationStyling}
              />
            </Fragment>
          )}
        </Fragment>
        { error ? <div>error</div> : '' }
      </Fragment>
    );
  }
}

SelectResourceStep.propTypes = {
  columns: PropTypes.arrayOf(PropTypes.object).isRequired,
  displayKey: PropTypes.string,
  emptyListBody: PropTypes.string,
  emptyListTitle: PropTypes.string,
  onRowClick: PropTypes.func,
  onSearch: PropTypes.func.isRequired,
  selectedLabel: PropTypes.string,
  selectedResourceRows: PropTypes.arrayOf(PropTypes.object),
  sortedColumnKey: PropTypes.string
};

SelectResourceStep.defaultProps = {
  displayKey: 'name',
  emptyListBody: i18nMark('Please add items to populate this list'),
  emptyListTitle: i18nMark('No Items Found'),
  onRowClick: () => {},
  selectedLabel: i18nMark('Selected Items'),
  selectedResourceRows: [],
  sortedColumnKey: 'name'
};

export default SelectResourceStep;
