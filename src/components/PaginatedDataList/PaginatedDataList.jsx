import React, { Fragment } from 'react';
import PropTypes, { arrayOf, shape, string, bool } from 'prop-types';
import {
  DataList,
  DataListItem,
  DataListCell,
  Text,
  TextContent,
  TextVariants,
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';
import { I18n, i18nMark } from '@lingui/react';
import { Trans, t } from '@lingui/macro';
import { withRouter, Link } from 'react-router-dom';

import Pagination from '../Pagination';
import DataListToolbar from '../DataListToolbar';
import { encodeQueryString, parseQueryString } from '../../util/qs';
import { pluralize, getArticle, ucFirst } from '../../util/strings';

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
    const { itemCount, queryParams: { page_size } } = this.props;
    return Math.ceil(itemCount / page_size);
  }

  getSortOrder () {
    const { queryParams } = this.props;
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
    const { history } = this.props;
    const { pathname, search } = history.location;
    const currentParams = parseQueryString(search);
    const qs = encodeQueryString({
      ...currentParams,
      ...newParams
    });
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
      queryParams,
      renderItem,
      toolbarColumns,
      additionalControls,
      itemName,
      itemNamePlural,
    } = this.props;
    const { error } = this.state;
    const [orderBy, sortOrder] = this.getSortOrder();
    return (
      <I18n>
        {({ i18n }) => (
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
                  <Trans>
                    No
                    {' '}
                    {ucFirst(itemNamePlural || pluralize(itemName))}
                    {' '}
                    Found
                  </Trans>
                </Title>
                <EmptyStateBody>
                  <Trans>
                    Please add
                    {' '}
                    {getArticle(itemName)}
                    {' '}
                    {itemName}
                    {' '}
                    to populate this list
                  </Trans>
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
                  showAdd={!!additionalControls}
                  add={additionalControls}
                />
                <DataList aria-label={i18n._(t`${ucFirst(pluralize(itemName))} List`)}>
                  {items.map(item => (renderItem ? renderItem(item) : (
                    <DataListItem
                      aria-labelledby={`items-list-item-${item.id}`}
                      key={item.id}
                    >
                      <DataListCell>
                        <TextContent style={detailWrapperStyle}>
                          <Link to={{ pathname: item.url }}>
                            <Text
                              id="items-list-item"
                              component={TextVariants.h6}
                              style={detailLabelStyle}
                            >
                              <span id={`items-list-item-${item.id}`}>
                                {item.name}
                              </span>
                            </Text>
                          </Link>
                        </TextContent>
                      </DataListCell>
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
        )}
      </I18n>
    );
  }
}

const Item = PropTypes.shape({
  id: PropTypes.number.isRequired,
  url: PropTypes.string.isRequired,
  name: PropTypes.string,
});

const QueryParams = PropTypes.shape({
  page: PropTypes.number,
  page_size: PropTypes.number,
  order_by: PropTypes.string,
});

PaginatedDataList.propTypes = {
  items: PropTypes.arrayOf(Item).isRequired,
  itemCount: PropTypes.number.isRequired,
  itemName: PropTypes.string,
  itemNamePlural: PropTypes.string,
  // TODO: determine this internally but pass in defaults?
  queryParams: QueryParams.isRequired,
  renderItem: PropTypes.func,
  toolbarColumns: arrayOf(shape({
    name: string.isRequired,
    key: string.isRequired,
    isSortable: bool,
  })),
  additionalControls: PropTypes.node,
};

PaginatedDataList.defaultProps = {
  renderItem: null,
  toolbarColumns: [
    { name: i18nMark('Name'), key: 'name', isSortable: true },
  ],
  additionalControls: null,
  itemName: 'item',
  itemNamePlural: '',
};

export { PaginatedDataList as _PaginatedDataList };
export default withRouter(PaginatedDataList);
