import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Card } from '@patternfly/react-core';

import { OrganizationsAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest from 'hooks/useRequest';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  getSearchableKeys,
} from 'components/PaginatedTable';
import DatalistToolbar from 'components/DataListToolbar';

import OrganizationExecEnvListItem from './OrganizationExecEnvListItem';

const QS_CONFIG = getQSConfig('organizations', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function OrganizationExecEnvList({ organization }) {
  const { id } = organization;
  const location = useLocation();

  const {
    error: contentError,
    isLoading,
    request: fetchExecutionEnvironments,
    result: {
      executionEnvironments,
      executionEnvironmentsCount,
      relatedSearchableKeys,
      searchableKeys,
    },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const [response, responseActions] = await Promise.all([
        OrganizationsAPI.readExecutionEnvironments(id, params),
        OrganizationsAPI.readExecutionEnvironmentsOptions(id),
      ]);

      return {
        executionEnvironments: response.data.results,
        executionEnvironmentsCount: response.data.count,
        actions: responseActions.data.actions,
        relatedSearchableKeys: (
          responseActions?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(responseActions.data.actions?.GET),
      };
    }, [location, id]),
    {
      executionEnvironments: [],
      executionEnvironmentsCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchExecutionEnvironments();
  }, [fetchExecutionEnvironments]);

  return (
    <Card>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading}
        items={executionEnvironments}
        itemCount={executionEnvironmentsCount}
        pluralizedItemName={t`Execution Environments`}
        qsConfig={QS_CONFIG}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        toolbarSearchColumns={[
          {
            name: t`Name`,
            key: 'name__icontains',
            isDefault: true,
          },
          {
            name: t`Image`,
            key: 'image__icontains',
            isDefault: false,
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
        renderToolbar={(props) => (
          <DatalistToolbar {...props} qsConfig={QS_CONFIG} />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG} isSelectable={false}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell sortKey="image">{t`Image`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(executionEnvironment, index) => (
          <OrganizationExecEnvListItem
            key={executionEnvironment.id}
            executionEnvironment={executionEnvironment}
            detailUrl={`/execution_environments/${executionEnvironment.id}`}
            rowIndex={index}
          />
        )}
      />
    </Card>
  );
}

export default OrganizationExecEnvList;
