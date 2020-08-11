import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { DataList } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withRouter } from 'react-router-dom';

import ListHeader from '../ListHeader';
import ContentEmpty from '../ContentEmpty';
import ContentError from '../ContentError';
import ContentLoading from '../ContentLoading';
import Pagination from '../Pagination';
import DataListToolbar from '../DataListToolbar';

import {
  encodeNonDefaultQueryString,
  parseQueryString,
  replaceParams,
} from '../../util/qs';

import { QSConfig, SearchColumns, SortColumns } from '../../types';

import PaginatedDataListItem from './PaginatedDataListItem';

class PaginatedDataList extends React.Component {
  constructor(props) {
    super(props);
    this.handleSetPage = this.handleSetPage.bind(this);
    this.handleSetPageSize = this.handleSetPageSize.bind(this);
    this.handleListItemSelect = this.handleListItemSelect.bind(this);
  }

  handleListItemSelect = (id = 0) => {
    const { items, onRowClick } = this.props;
    const match = items.find(item => item.id === Number(id));
    onRowClick(match);
  };

  handleSetPage(event, pageNumber) {
    const { history, qsConfig } = this.props;
    const { search } = history.location;
    const oldParams = parseQueryString(qsConfig, search);
    this.pushHistoryState(replaceParams(oldParams, { page: pageNumber }));
  }

  handleSetPageSize(event, pageSize, page) {
    const { history, qsConfig } = this.props;
    const { search } = history.location;
    const oldParams = parseQueryString(qsConfig, search);
    this.pushHistoryState(
      replaceParams(oldParams, { page_size: pageSize, page })
    );
  }

  pushHistoryState(params) {
    const { history, qsConfig } = this.props;
    const { pathname } = history.location;
    const encodedParams = encodeNonDefaultQueryString(qsConfig, params);
    history.push(encodedParams ? `${pathname}?${encodedParams}` : pathname);
  }

  render() {
    const {
      contentError,
      hasContentLoading,
      emptyStateControls,
      items,
      itemCount,
      qsConfig,
      renderItem,
      toolbarSearchColumns,
      toolbarSearchableKeys,
      toolbarRelatedSearchableKeys,
      toolbarSortColumns,
      pluralizedItemName,
      showPageSizeOptions,
      location,
      i18n,
      renderToolbar,
    } = this.props;
    const searchColumns = toolbarSearchColumns.length
      ? toolbarSearchColumns
      : [
          {
            name: i18n._(t`Name`),
            key: 'name',
            isDefault: true,
          },
        ];
    const sortColumns = toolbarSortColumns.length
      ? toolbarSortColumns
      : [
          {
            name: i18n._(t`Name`),
            key: 'name',
          },
        ];
    const queryParams = parseQueryString(qsConfig, location.search);

    const dataListLabel = i18n._(t`${pluralizedItemName} List`);
    const emptyContentMessage = i18n._(
      t`Please add ${pluralizedItemName} to populate this list `
    );
    const emptyContentTitle = i18n._(t`No ${pluralizedItemName} Found `);

    let Content;
    if (hasContentLoading && items.length <= 0) {
      Content = <ContentLoading />;
    } else if (contentError) {
      Content = <ContentError error={contentError} />;
    } else if (items.length <= 0) {
      Content = (
        <ContentEmpty title={emptyContentTitle} message={emptyContentMessage} />
      );
    } else {
      Content = (
        <DataList
          aria-label={dataListLabel}
          onSelectDataListItem={id => this.handleListItemSelect(id)}
        >
          {items.map(renderItem)}
        </DataList>
      );
    }

    const ToolbarPagination = (
      <Pagination
        isCompact
        dropDirection="down"
        itemCount={itemCount}
        page={queryParams.page || 1}
        perPage={queryParams.page_size}
        perPageOptions={
          showPageSizeOptions
            ? [
                { title: '5', value: 5 },
                { title: '10', value: 10 },
                { title: '20', value: 20 },
                { title: '50', value: 50 },
              ]
            : []
        }
        onSetPage={this.handleSetPage}
        onPerPageSelect={this.handleSetPageSize}
      />
    );

    return (
      <Fragment>
        <ListHeader
          itemCount={itemCount}
          renderToolbar={renderToolbar}
          emptyStateControls={emptyStateControls}
          searchColumns={searchColumns}
          sortColumns={sortColumns}
          searchableKeys={toolbarSearchableKeys}
          relatedSearchableKeys={toolbarRelatedSearchableKeys}
          qsConfig={qsConfig}
          pagination={ToolbarPagination}
        />
        {Content}
        {items.length ? (
          <Pagination
            variant="bottom"
            itemCount={itemCount}
            page={queryParams.page || 1}
            perPage={queryParams.page_size}
            perPageOptions={
              showPageSizeOptions
                ? [
                    { title: '5', value: 5 },
                    { title: '10', value: 10 },
                    { title: '20', value: 20 },
                    { title: '50', value: 50 },
                  ]
                : []
            }
            onSetPage={this.handleSetPage}
            onPerPageSelect={this.handleSetPageSize}
          />
        ) : null}
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
  pluralizedItemName: PropTypes.string,
  qsConfig: QSConfig.isRequired,
  renderItem: PropTypes.func,
  toolbarSearchColumns: SearchColumns,
  toolbarSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  toolbarRelatedSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  toolbarSortColumns: SortColumns,
  showPageSizeOptions: PropTypes.bool,
  renderToolbar: PropTypes.func,
  hasContentLoading: PropTypes.bool,
  contentError: PropTypes.shape(),
  onRowClick: PropTypes.func,
};

PaginatedDataList.defaultProps = {
  hasContentLoading: false,
  contentError: null,
  toolbarSearchColumns: [],
  toolbarSearchableKeys: [],
  toolbarRelatedSearchableKeys: [],
  toolbarSortColumns: [],
  pluralizedItemName: 'Items',
  showPageSizeOptions: true,
  renderItem: item => <PaginatedDataListItem key={item.id} item={item} />,
  renderToolbar: props => <DataListToolbar {...props} />,
  onRowClick: () => null,
};

export { PaginatedDataList as _PaginatedDataList };
export default withI18n()(withRouter(PaginatedDataList));
