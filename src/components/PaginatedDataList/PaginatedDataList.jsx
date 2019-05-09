import React, { Fragment } from 'react';
import PropTypes, { arrayOf, shape, string, bool } from 'prop-types';
import { DataList } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';

import ContentEmpty from '../ContentEmpty';
import ContentError from '../ContentError';
import ContentLoading from '../ContentLoading';
import Pagination from '../Pagination';
import DataListToolbar from '../DataListToolbar';
import PaginatedDataListItem from './PaginatedDataListItem';
import {
  parseNamespacedQueryString,
  updateNamespacedQueryString,
} from '../../util/qs';
import { pluralize, ucFirst } from '../../util/strings';
import { QSConfig } from '../../types';

const EmptyStateControlsWrapper = styled.div`
  display: flex;
  margin-top: 20px;
  margin-right: 20px;
  margin-bottom: 20px;
  justify-content: flex-end;

  & > :not(:first-child)  {
    margin-left: 20px;
  }
`;
class PaginatedDataList extends React.Component {
  constructor (props) {
    super(props);
    this.handleSetPage = this.handleSetPage.bind(this);
    this.handleSetPageSize = this.handleSetPageSize.bind(this);
    this.handleSort = this.handleSort.bind(this);
  }

  getSortOrder () {
    const { qsConfig, location } = this.props;
    const queryParams = parseNamespacedQueryString(qsConfig, location.search);
    if (queryParams.order_by && queryParams.order_by.startsWith('-')) {
      return [queryParams.order_by.substr(1), 'descending'];
    }
    return [queryParams.order_by, 'ascending'];
  }

  handleSetPage (event, pageNumber) {
    this.pushHistoryState({ page: pageNumber });
  }

  handleSetPageSize (event, pageSize) {
    this.pushHistoryState({ page_size: pageSize });
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

  render () {
    const [orderBy, sortOrder] = this.getSortOrder();
    const {
      contentError,
      contentLoading,
      emptyStateControls,
      items,
      itemCount,
      qsConfig,
      renderItem,
      toolbarColumns,
      itemName,
      itemNamePlural,
      showPageSizeOptions,
      location,
      i18n,
      renderToolbar,
    } = this.props;
    const columns = toolbarColumns.length ? toolbarColumns : [{ name: i18n._(t`Name`), key: 'name', isSortable: true }];
    const queryParams = parseNamespacedQueryString(qsConfig, location.search);

    const itemDisplayName = ucFirst(pluralize(itemName));
    const itemDisplayNamePlural = ucFirst(itemNamePlural || pluralize(itemName));

    const dataListLabel = i18n._(t`${itemDisplayName} List`);
    const emptyContentMessage = i18n._(t`Please add ${itemDisplayNamePlural} to populate this list `);
    const emptyContentTitle = i18n._(t`No ${itemDisplayNamePlural} Found `);

    let Content;
    if (contentLoading && items.length <= 0) {
      Content = (<ContentLoading />);
    } else if (contentError) {
      Content = (<ContentError />);
    } else if (items.length <= 0) {
      Content = (<ContentEmpty title={emptyContentTitle} message={emptyContentMessage} />);
    } else {
      Content = (<DataList aria-label={dataListLabel}>{items.map(renderItem)}</DataList>);
    }

    if (items.length <= 0) {
      return (
        <Fragment>
          {emptyStateControls && (
            <EmptyStateControlsWrapper>
              {emptyStateControls}
            </EmptyStateControlsWrapper>
          )}
          {emptyStateControls && (
            <div css="border-bottom: 1px solid #d2d2d2" />
          )}
          {Content}
        </Fragment>
      );
    }

    return (
      <Fragment>
        {renderToolbar({
          sortedColumnKey: orderBy,
          sortOrder,
          columns,
          onSearch: () => { },
          onSort: this.handleSort,
        })}
        {Content}
        <Pagination
          variant="bottom"
          itemCount={itemCount}
          page={queryParams.page || 1}
          perPage={queryParams.page_size}
          perPageOptions={showPageSizeOptions ? [
            { title: '5', value: 5 },
            { title: '10', value: 10 },
            { title: '20', value: 20 },
            { title: '50', value: 50 }
          ] : []}
          onSetPage={this.handleSetPage}
          onPerPageSelect={this.handleSetPageSize}
        />
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
  showPageSizeOptions: PropTypes.bool,
  renderToolbar: PropTypes.func,
  contentLoading: PropTypes.bool,
  contentError: PropTypes.bool,
};

PaginatedDataList.defaultProps = {
  contentLoading: false,
  contentError: false,
  toolbarColumns: [],
  itemName: 'item',
  itemNamePlural: '',
  showPageSizeOptions: true,
  renderItem: (item) => (<PaginatedDataListItem key={item.id} item={item} />),
  renderToolbar: (props) => (<DataListToolbar {...props} />),
};

export { PaginatedDataList as _PaginatedDataList };
export default withI18n()(withRouter(PaginatedDataList));
