import React, { Fragment } from 'react';
import PropTypes, { arrayOf, shape, string, bool, node } from 'prop-types';
import {
  DataList,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCell,
  Text,
  TextContent,
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withRouter, Link } from 'react-router-dom';

import Pagination from '../Pagination';
import DataListToolbar from '../DataListToolbar';
import {
  parseNamespacedQueryString,
  updateNamespacedQueryString,
} from '../../util/qs';
import { pluralize, getArticle, ucFirst } from '../../util/strings';
import { QSConfig } from '../../types';

const detailWrapperStyle = {
  display: 'grid',
  gridTemplateColumns: 'minmax(70px, max-content) minmax(60px, max-content)',
};

const detailLabelStyle = {
  fontWeight: '700',
  lineHeight: '24px',
  marginRight: '20px',
};

class PaginatedDataList extends React.Component {
  constructor (props) {
    super(props);

    this.state = {
      error: null,
    };

    this.handleSetPage = this.handleSetPage.bind(this);
    this.handleSort = this.handleSort.bind(this);
  }

  getPageCount () {
    const { itemCount, qsConfig, location } = this.props;
    const queryParams = parseNamespacedQueryString(qsConfig, location.search);
    return Math.ceil(itemCount / queryParams.page_size);
  }

  getSortOrder () {
    const { qsConfig, location } = this.props;
    const queryParams = parseNamespacedQueryString(qsConfig, location.search);
    if (queryParams.order_by && queryParams.order_by.startsWith('-')) {
      return [queryParams.order_by.substr(1), 'descending'];
    }
    return [queryParams.order_by, 'ascending'];
  }

  handleSetPage (pageNumber, pageSize) {
    this.pushHistoryState({
      page: pageNumber,
      page_size: pageSize,
    });
  }

  handleSort (sortedColumnKey, sortOrder) {
    this.pushHistoryState({
      order_by: sortOrder === 'ascending' ? sortedColumnKey : `-${sortedColumnKey}`,
      page: null,
    });
  }

  pushHistoryState (newParams) {
    const { history, qsConfig } = this.props;
    const { pathname, search } = history.location;
    const qs = updateNamespacedQueryString(qsConfig, search, newParams);
    history.push(`${pathname}?${qs}`);
  }

  getPluralItemName () {
    const { itemName, itemNamePlural } = this.props;
    return itemNamePlural || `${itemName}s`;
  }

  render () {
    const {
      items,
      itemCount,
      qsConfig,
      renderItem,
      toolbarColumns,
      additionalControls,
      itemName,
      itemNamePlural,
      showSelectAll,
      isAllSelected,
      onSelectAll,
      alignToolbarLeft,
      showPageSizeOptions,
      paginationStyling,
      location,
      i18n
    } = this.props;
    const { error } = this.state;
    const [orderBy, sortOrder] = this.getSortOrder();
    const queryParams = parseNamespacedQueryString(qsConfig, location.search);
    const columns = toolbarColumns || [{ name: i18n._(t`Name`), key: 'name', isSortable: true }];
    return (
      <Fragment>
        {error && (
          <Fragment>
            {error && (
              <Fragment>
                <div>{error.message}</div>
                {error.response && (
                  <div>{error.response.data.detail}</div>
                )}
              </Fragment> // TODO: replace with proper error handling
            )}
            {items.length === 0 ? (
              <EmptyState>
                <EmptyStateIcon icon={CubesIcon} />
                <Title size="lg">
                  {i18n._(t`No ${ucFirst(itemNamePlural || pluralize(itemName))} Found`)}
                </Title>
                <EmptyStateBody>
                  {i18n._(t`Please add ${getArticle(itemName)} ${itemName} to populate this list`)}
                </EmptyStateBody>
              </EmptyState>
            ) : (
              <Fragment>
                <DataListToolbar
                  sortedColumnKey={orderBy}
                  sortOrder={sortOrder}
                  columns={toolbarColumns}
                  onSearch={() => { }}
                  onSort={this.handleSort}
                  showSelectAll={showSelectAll}
                  isAllSelected={isAllSelected}
                  onSelectAll={onSelectAll}
                  additionalControls={additionalControls}
                  noLeftMargin={alignToolbarLeft}
                />
                <DataList aria-label={i18n._(t`${ucFirst(pluralize(itemName))} List`)}>
                  {items.map(item => (renderItem ? renderItem(item) : (
                    <DataListItem
                      aria-labelledby={`items-list-item-${item.id}`}
                      key={item.id}
                    >
                      <DataListItemRow>
                        <DataListItemCells dataListCells={[
                          <DataListCell key="team-name">
                            <TextContent style={detailWrapperStyle}>
                              <Link to={{ pathname: item.url }}>
                                <Text
                                  id={`items-list-item-${item.id}`}
                                  style={detailLabelStyle}
                                >
                                  {item.name}
                                </Text>
                              </Link>
                            </TextContent>
                          </DataListCell>
                        ]}
                        />
                      </DataListItemRow>
                    </DataListItem>
                  )))}
                </DataList>
                <Pagination
                  count={itemCount}
                  page={queryParams.page || 1}
                  pageCount={this.getPageCount()}
                  page_size={queryParams.page_size}
                  onSetPage={this.handleSetPage}
                  showPageSizeOptions={showPageSizeOptions}
                  style={paginationStyling}
                />
              </Fragment>
            )}
          </Fragment> // TODO: replace with proper error handling
        )}
        {items.length === 0 ? (
          <EmptyState>
            <EmptyStateIcon icon={CubesIcon} />
            <Title size="lg">
              {i18n._(t`No ${ucFirst(itemNamePlural || pluralize(itemName))} Found`)}
            </Title>
            <EmptyStateBody>
              {i18n._(t`Please add ${getArticle(itemName)} ${itemName} to populate this list`)}
            </EmptyStateBody>
          </EmptyState>
        ) : (
          <Fragment>
            <DataListToolbar
              sortedColumnKey={orderBy}
              sortOrder={sortOrder}
              columns={columns}
              onSearch={() => { }}
              onSort={this.handleSort}
              showSelectAll={showSelectAll}
              isAllSelected={isAllSelected}
              onSelectAll={onSelectAll}
              additionalControls={additionalControls}
            />
            <DataList aria-label={i18n._(t`${ucFirst(pluralize(itemName))} List`)}>
              {items.map(item => (renderItem ? renderItem(item) : (
                <DataListItem
                  aria-labelledby={`items-list-item-${item.id}`}
                  key={item.id}
                >
                  <DataListItemRow>
                    <DataListItemCells dataListCells={[
                      <DataListCell key="team-name">
                        <TextContent style={detailWrapperStyle}>
                          <Link to={{ pathname: item.url }}>
                            <Text
                              id={`items-list-item-${item.id}`}
                              style={detailLabelStyle}
                            >
                              {item.name}
                            </Text>
                          </Link>
                        </TextContent>
                      </DataListCell>
                    ]}
                    />
                  </DataListItemRow>
                </DataListItem>
              )))}
            </DataList>
            <Pagination
              count={itemCount}
              page={queryParams.page}
              pageCount={this.getPageCount()}
              page_size={queryParams.page_size}
              onSetPage={this.handleSetPage}
            />
          </Fragment>
        )}
      </Fragment>
    );
  }
}

const Item = PropTypes.shape({
  id: PropTypes.number.isRequired,
  url: PropTypes.string.isRequired,
  name: PropTypes.string,
});

PaginatedDataList.propTypes = {
  items: PropTypes.arrayOf(Item).isRequired,
  itemCount: PropTypes.number.isRequired,
  itemName: PropTypes.string,
  itemNamePlural: PropTypes.string,
  qsConfig: QSConfig.isRequired,
  renderItem: PropTypes.func,
  toolbarColumns: arrayOf(shape({
    name: string.isRequired,
    key: string.isRequired,
    isSortable: bool,
  })),
  additionalControls: arrayOf(node),
  showSelectAll: PropTypes.bool,
  isAllSelected: PropTypes.bool,
  onSelectAll: PropTypes.func,
  alignToolbarLeft: PropTypes.bool,
  showPageSizeOptions: PropTypes.bool,
  paginationStyling: PropTypes.shape(),
};

PaginatedDataList.defaultProps = {
  renderItem: null,
  toolbarColumns: [],
  additionalControls: [],
  itemName: 'item',
  itemNamePlural: '',
  showSelectAll: false,
  isAllSelected: false,
  onSelectAll: null,
  alignToolbarLeft: false,
  showPageSizeOptions: true,
  paginationStyling: null,
};

export { PaginatedDataList as _PaginatedDataList };
export default withI18n()(withRouter(PaginatedDataList));
