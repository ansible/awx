import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import { WorkflowJobTemplatesAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import DataListToolbar from 'components/DataListToolbar';
import CheckboxListItem from 'components/CheckboxListItem';
import PaginatedTable, {
  HeaderCell,
  HeaderRow,
  getSearchableKeys,
} from 'components/PaginatedTable';

const QS_CONFIG = getQSConfig('workflow-job-templates', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function WorkflowJobTemplatesList({ nodeResource, onUpdateNodeResource }) {
  const location = useLocation();

  const {
    result: {
      workflowJobTemplates,
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
        WorkflowJobTemplatesAPI.read(params, {
          role_level: 'execute_role',
        }),
        WorkflowJobTemplatesAPI.readOptions(),
      ]);
      return {
        workflowJobTemplates: response.data.results,
        count: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [location]),
    {
      workflowJobTemplates: [],
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
      items={workflowJobTemplates}
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
        {
          name: t`Organization (Name)`,
          key: 'organization__name__icontains',
        },
        {
          name: t`Inventory (Name)`,
          key: 'inventory__name__icontains',
        },
        {
          name: t`Created By (Username)`,
          key: 'created_by__username__icontains',
        },
        {
          name: t`Modified By (Username)`,
          key: 'modified_by__username__icontains',
        },
      ]}
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
    />
  );
}

WorkflowJobTemplatesList.propTypes = {
  nodeResource: shape(),
  onUpdateNodeResource: func.isRequired,
};

WorkflowJobTemplatesList.defaultProps = {
  nodeResource: null,
};

export default WorkflowJobTemplatesList;
