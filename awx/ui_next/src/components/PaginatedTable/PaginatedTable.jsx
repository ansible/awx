import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { TableComposable, Tbody } from '@patternfly/react-table';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useHistory } from 'react-router-dom';

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
import { QSConfig, SearchColumns } from '../../types';

function PaginatedTable({
  contentError,
  hasContentLoading,
  emptyStateControls,
  items,
  itemCount,
  qsConfig,
  headerRow,
  renderRow,
  toolbarSearchColumns,
  toolbarSearchableKeys,
  toolbarRelatedSearchableKeys,
  pluralizedItemName,
  showPageSizeOptions,
  i18n,
  renderToolbar,
}) {
  const history = useHistory();

  const pushHistoryState = params => {
    const { pathname } = history.location;
    const encodedParams = encodeNonDefaultQueryString(qsConfig, params);
    history.push(encodedParams ? `${pathname}?${encodedParams}` : pathname);
  };

  const handleSetPage = (event, pageNumber) => {
    const oldParams = parseQueryString(qsConfig, history.location.search);
    pushHistoryState(replaceParams(oldParams, { page: pageNumber }));
  };

  const handleSetPageSize = (event, pageSize, page) => {
    const oldParams = parseQueryString(qsConfig, history.location.search);
    pushHistoryState(replaceParams(oldParams, { page_size: pageSize, page }));
  };

  const searchColumns = toolbarSearchColumns.length
    ? toolbarSearchColumns
    : [
        {
          name: i18n._(t`Name`),
          key: 'name',
          isDefault: true,
        },
      ];
  const queryParams = parseQueryString(qsConfig, history.location.search);

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
      <TableComposable aria-label={dataListLabel}>
        {headerRow}
        <Tbody>{items.map(renderRow)}</Tbody>
      </TableComposable>
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
      onSetPage={handleSetPage}
      onPerPageSelect={handleSetPageSize}
    />
  );

  return (
    <Fragment>
      <ListHeader
        itemCount={itemCount}
        renderToolbar={renderToolbar}
        emptyStateControls={emptyStateControls}
        searchColumns={searchColumns}
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
          onSetPage={handleSetPage}
          onPerPageSelect={handleSetPageSize}
        />
      ) : null}
    </Fragment>
  );
}

const Item = PropTypes.shape({
  id: PropTypes.number.isRequired,
  url: PropTypes.string.isRequired,
  name: PropTypes.string,
});

PaginatedTable.propTypes = {
  items: PropTypes.arrayOf(Item).isRequired,
  itemCount: PropTypes.number.isRequired,
  pluralizedItemName: PropTypes.string,
  qsConfig: QSConfig.isRequired,
  renderRow: PropTypes.func.isRequired,
  toolbarSearchColumns: SearchColumns,
  toolbarSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  toolbarRelatedSearchableKeys: PropTypes.arrayOf(PropTypes.string),
  showPageSizeOptions: PropTypes.bool,
  renderToolbar: PropTypes.func,
  hasContentLoading: PropTypes.bool,
  contentError: PropTypes.shape(),
};

PaginatedTable.defaultProps = {
  hasContentLoading: false,
  contentError: null,
  toolbarSearchColumns: [],
  toolbarSearchableKeys: [],
  toolbarRelatedSearchableKeys: [],
  pluralizedItemName: 'Items',
  showPageSizeOptions: true,
  renderToolbar: props => <DataListToolbar {...props} />,
};

export { PaginatedTable as _PaginatedTable };
export default withI18n()(PaginatedTable);
