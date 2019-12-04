import React, { Fragment } from 'react';
import PropTypes, { arrayOf, shape, string, bool } from 'prop-types';
import { DataList } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { withRouter } from 'react-router-dom';

import ListHeader from '@components/ListHeader';
import ContentEmpty from '@components/ContentEmpty';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import Pagination from '@components/Pagination';
import DataListToolbar from '@components/DataListToolbar';

import {
  encodeNonDefaultQueryString,
  parseQueryString,
  replaceParams,
} from '@util/qs';

import { QSConfig } from '@types';

import PaginatedDataListItem from './PaginatedDataListItem';

class PaginatedDataList extends React.Component {
  constructor(props) {
    super(props);
    this.handleSetPage = this.handleSetPage.bind(this);
    this.handleSetPageSize = this.handleSetPageSize.bind(this);
  }

  handleSetPage(event, pageNumber) {
    const { history, qsConfig } = this.props;
    const { search } = history.location;
    const oldParams = parseQueryString(qsConfig, search);
    this.pushHistoryState(replaceParams(oldParams, { page: pageNumber }));
  }

  handleSetPageSize(event, pageSize) {
    const { history, qsConfig } = this.props;
    const { search } = history.location;
    const oldParams = parseQueryString(qsConfig, search);
    this.pushHistoryState(replaceParams(oldParams, { page_size: pageSize }));
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
      toolbarColumns,
      pluralizedItemName,
      showPageSizeOptions,
      location,
      i18n,
      renderToolbar,
    } = this.props;
    const columns = toolbarColumns.length
      ? toolbarColumns
      : [
          {
            name: i18n._(t`Name`),
            key: 'name',
            isSortable: true,
            isSearchable: true,
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
        <DataList aria-label={dataListLabel}>{items.map(renderItem)}</DataList>
      );
    }

    return (
      <Fragment>
        <ListHeader
          itemCount={itemCount}
          renderToolbar={renderToolbar}
          emptyStateControls={emptyStateControls}
          columns={columns}
          qsConfig={qsConfig}
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
  toolbarColumns: arrayOf(
    shape({
      name: string.isRequired,
      key: string.isRequired,
      isSortable: bool,
    })
  ),
  showPageSizeOptions: PropTypes.bool,
  renderToolbar: PropTypes.func,
  hasContentLoading: PropTypes.bool,
  contentError: PropTypes.shape(),
};

PaginatedDataList.defaultProps = {
  hasContentLoading: false,
  contentError: null,
  toolbarColumns: [],
  pluralizedItemName: 'Items',
  showPageSizeOptions: true,
  renderItem: item => <PaginatedDataListItem key={item.id} item={item} />,
  renderToolbar: props => <DataListToolbar {...props} />,
};

export { PaginatedDataList as _PaginatedDataList };
export default withI18n()(withRouter(PaginatedDataList));
