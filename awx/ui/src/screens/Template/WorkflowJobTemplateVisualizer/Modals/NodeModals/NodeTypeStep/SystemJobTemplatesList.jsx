import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { SystemJobTemplatesAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import DataListToolbar from 'components/DataListToolbar';
import CheckboxListItem from 'components/CheckboxListItem';
import PaginatedTable, {
  HeaderCell,
  HeaderRow,
  getSearchableKeys,
} from 'components/PaginatedTable';

const QS_CONFIG = getQSConfig('system-job-templates', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function SystemJobTemplatesList({ nodeResource, onUpdateNodeResource }) {
  const location = useLocation();

  const {
    result: {
      systemJobTemplates,
      count,
      relatedSearchableKeys,
      searchableKeys,
    },
    error,
    isLoading,
    request: fetchWorkflowJobTemplates,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        SystemJobTemplatesAPI.read(params, {
          role_level: 'execute_role',
        }),
        SystemJobTemplatesAPI.readOptions(),
      ]);
      return {
        systemJobTemplates: response.data.results,
        count: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [location]),
    {
      systemJobTemplates: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchWorkflowJobTemplates();
  }, [fetchWorkflowJobTemplates]);

  return (
    <PaginatedTable
      contentError={error}
      hasContentLoading={isLoading}
      itemCount={count}
      items={systemJobTemplates}
      qsConfig={QS_CONFIG}
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
      showPageSizeOptions={false}
      toolbarSearchColumns={[
        {
          name: t`Name`,
          key: 'name__icontains',
          isDefault: true,
        },
      ]}
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
    />
  );
}

SystemJobTemplatesList.propTypes = {
  nodeResource: shape(),
  onUpdateNodeResource: func.isRequired,
};

SystemJobTemplatesList.defaultProps = {
  nodeResource: null,
};

export default SystemJobTemplatesList;
