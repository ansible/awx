import React, { Fragment, useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import { withRouter, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import useRequest from '../../util/useRequest';

import { SearchColumns, SortColumns } from '../../types';
import PaginatedDataList from '../PaginatedDataList';
import DataListToolbar from '../DataListToolbar';
import CheckboxListItem from '../CheckboxListItem';
import SelectedList from '../SelectedList';
import { getQSConfig, parseQueryString } from '../../util/qs';

const QS_Config = sortColumns => {
  return getQSConfig('resource', {
    page: 1,
    page_size: 5,
    order_by: `${
      sortColumns.filter(col => col.key === 'name').length ? 'name' : 'username'
    }`,
  });
};
function SelectResourceStep({
  searchColumns,
  sortColumns,
  displayKey,
  onRowClick,
  selectedLabel,
  selectedResourceRows,
  fetchItems,
  i18n,
}) {
  const location = useLocation();

  const {
    isLoading,
    error,
    request: readResourceList,
    result: { resources, itemCount },
  } = useRequest(
    useCallback(async () => {
      const queryParams = parseQueryString(
        QS_Config(sortColumns),
        location.search
      );

      const {
        data: { count, results },
      } = await fetchItems(queryParams);
      return { resources: results, itemCount: count };
    }, [location, fetchItems, sortColumns]),
    {
      resources: [],
      itemCount: 0,
    }
  );

  useEffect(() => {
    readResourceList();
  }, [readResourceList]);

  return (
    <Fragment>
      <div>
        {i18n._(
          t`Choose the resources that will be receiving new roles.  You'll be able to select the roles to apply in the next step.  Note that the resources chosen here will receive all roles chosen in the next step.`
        )}
      </div>
      {selectedResourceRows.length > 0 && (
        <SelectedList
          displayKey={displayKey}
          label={selectedLabel}
          onRemove={onRowClick}
          selected={selectedResourceRows}
        />
      )}
      <PaginatedDataList
        hasContentLoading={isLoading}
        contentError={error}
        items={resources}
        itemCount={itemCount}
        qsConfig={QS_Config(sortColumns)}
        onRowClick={onRowClick}
        toolbarSearchColumns={searchColumns}
        toolbarSortColumns={sortColumns}
        renderItem={item => (
          <CheckboxListItem
            isSelected={selectedResourceRows.some(i => i.id === item.id)}
            itemId={item.id}
            key={item.id}
            name={item[displayKey]}
            label={item[displayKey]}
            onSelect={() => onRowClick(item)}
            onDeselect={() => onRowClick(item)}
          />
        )}
        renderToolbar={props => <DataListToolbar {...props} fillWidth />}
        showPageSizeOptions={false}
      />
    </Fragment>
  );
}

SelectResourceStep.propTypes = {
  searchColumns: SearchColumns,
  sortColumns: SortColumns,
  displayKey: PropTypes.string,
  onRowClick: PropTypes.func,
  fetchItems: PropTypes.func.isRequired,
  selectedLabel: PropTypes.string,
  selectedResourceRows: PropTypes.arrayOf(PropTypes.object),
};

SelectResourceStep.defaultProps = {
  searchColumns: null,
  sortColumns: null,
  displayKey: 'name',
  onRowClick: () => {},
  selectedLabel: null,
  selectedResourceRows: [],
};

export { SelectResourceStep as _SelectResourceStep };
export default withI18n()(withRouter(SelectResourceStep));
