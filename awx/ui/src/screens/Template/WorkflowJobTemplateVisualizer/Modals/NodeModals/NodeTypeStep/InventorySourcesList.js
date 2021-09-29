import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { InventorySourcesAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import DataListToolbar from 'components/DataListToolbar';
import CheckboxListItem from 'components/CheckboxListItem';
import PaginatedTable, {
  HeaderCell,
  HeaderRow,
  getSearchableKeys,
} from 'components/PaginatedTable';

const QS_CONFIG = getQSConfig('inventory-sources', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function InventorySourcesList({ nodeResource, onUpdateNodeResource }) {
  const location = useLocation();

  const {
    result: { inventorySources, count, relatedSearchableKeys, searchableKeys },
    error,
    isLoading,
    request: fetchInventorySources,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        InventorySourcesAPI.read(params),
        InventorySourcesAPI.readOptions(),
      ]);
      return {
        inventorySources: response.data.results,
        count: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [location]),
    {
      inventorySources: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchInventorySources();
  }, [fetchInventorySources]);

  return (
    <PaginatedTable
      contentError={error}
      hasContentLoading={isLoading}
      itemCount={count}
      items={inventorySources}
      qsConfig={QS_CONFIG}
      showPageSizeOptions={false}
      headerRow={
        <HeaderRow isExpandable={false} qsConfig={QS_CONFIG}>
          <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
        </HeaderRow>
      }
      renderRow={(item, index) => (
        <CheckboxListItem
          rowIndex={index}
          isSelected={!!(nodeResource && nodeResource.id === item.id)}
          itemId={item.id}
          key={item.id}
          name={item.name}
          label={item.name}
          onSelect={() => onUpdateNodeResource(item)}
          onDeselect={() => onUpdateNodeResource(null)}
          isRadio
        />
      )}
      renderToolbar={(props) => <DataListToolbar {...props} fillWidth />}
      toolbarSearchColumns={[
        {
          name: t`Name`,
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: t`Source`,
          key: 'or__source',
          options: [
            [`file`, t`File, directory or script`],
            [`scm`, t`Sourced from a project`],
            [`ec2`, t`Amazon EC2`],
            [`gce`, t`Google Compute Engine`],
            [`azure_rm`, t`Microsoft Azure Resource Manager`],
            [`vmware`, t`VMware vCenter`],
            [`satellite6`, t`Red Hat Satellite 6`],
            [`openstack`, t`OpenStack`],
            [`rhv`, t`Red Hat Virtualization`],
            [`controller`, t`Red Hat Ansible Automation Platform`],
          ],
        },
      ]}
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
    />
  );
}

InventorySourcesList.propTypes = {
  nodeResource: shape(),
  onUpdateNodeResource: func.isRequired,
};

InventorySourcesList.defaultProps = {
  nodeResource: null,
};

export default InventorySourcesList;
