import React, { Fragment } from 'react';
import PropTypes, { arrayOf, shape, string, bool } from 'prop-types';
import {
  DataList,
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';

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

    this.state = {
      error: null,
    };

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
    const {
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
    const { error } = this.state;
    const [orderBy, sortOrder] = this.getSortOrder();
    const queryParams = parseNamespacedQueryString(qsConfig, location.search);
    const columns = toolbarColumns.length ? toolbarColumns : [{ name: i18n._(t`Name`), key: 'name', isSortable: true }];
    return (
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
          <Fragment>
            <EmptyStateControlsWrapper>
              {emptyStateControls}
            </EmptyStateControlsWrapper>
            <div css="border-bottom: 1px solid #d2d2d2" />
            <EmptyState>
              <EmptyStateIcon icon={CubesIcon} />
              <Title size="lg">
                {i18n._(t`No ${ucFirst(itemNamePlural || pluralize(itemName))} Found `)}
              </Title>
              <EmptyStateBody>
                {i18n._(t`Please add ${ucFirst(itemNamePlural || pluralize(itemName))} to populate this list `)}
              </EmptyStateBody>
            </EmptyState>
          </Fragment>
        ) : (
          <Fragment>
            {renderToolbar({
              sortedColumnKey: orderBy,
              sortOrder,
              columns,
              onSearch: () => { },
              onSort: this.handleSort,
            })}
            <DataList aria-label={i18n._(t`${ucFirst(pluralize(itemName))} List`)}>
              {items.map(item => (renderItem ? renderItem(item) : (
                <PaginatedDataListItem key={item.id} item={item} />
              )))}
            </DataList>
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
  showPageSizeOptions: PropTypes.bool,
  renderToolbar: PropTypes.func,
};

PaginatedDataList.defaultProps = {
  renderItem: null,
  toolbarColumns: [],
  itemName: 'item',
  itemNamePlural: '',
  showPageSizeOptions: true,
  renderToolbar: (props) => (<DataListToolbar {...props} />),
};

export { PaginatedDataList as _PaginatedDataList };
export default withI18n()(withRouter(PaginatedDataList));
