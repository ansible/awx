import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card } from '@patternfly/react-core';

import { OrganizationsAPI } from '../../../api';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest from '../../../util/useRequest';
import PaginatedDataList from '../../../components/PaginatedDataList';
import DatalistToolbar from '../../../components/DataListToolbar';

import OrganizationExecEnvListItem from './OrganizationExecEnvListItem';

const QS_CONFIG = getQSConfig('organizations', {
  page: 1,
  page_size: 20,
  order_by: 'image',
});

function OrganizationExecEnvList({ i18n, organization }) {
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
        OrganizationsAPI.readExecutionEnvironmentsOptions(id, params),
      ]);

      return {
        executionEnvironments: response.data.results,
        executionEnvironmentsCount: response.data.count,
        actions: responseActions.data.actions,
        relatedSearchableKeys: (
          responseActions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          responseActions.data.actions?.GET || {}
        ).filter(key => responseActions.data.actions?.GET[key].filterable),
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
    <>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={isLoading}
          items={executionEnvironments}
          itemCount={executionEnvironmentsCount}
          pluralizedItemName={i18n._(t`Execution Environments`)}
          qsConfig={QS_CONFIG}
          toolbarSearchableKeys={searchableKeys}
          toolbarRelatedSearchableKeys={relatedSearchableKeys}
          toolbarSearchColumns={[
            {
              name: i18n._(t`Image`),
              key: 'image__icontains',
              isDefault: true,
            },
            {
              name: i18n._(t`Created By (Username)`),
              key: 'created_by__username__icontains',
            },
            {
              name: i18n._(t`Modified By (Username)`),
              key: 'modified_by__username__icontains',
            },
          ]}
          toolbarSortColumns={[
            {
              name: i18n._(t`Image`),
              key: 'image',
            },
            {
              name: i18n._(t`Created`),
              key: 'created',
            },
            {
              name: i18n._(t`Modified`),
              key: 'modified',
            },
          ]}
          renderToolbar={props => (
            <DatalistToolbar {...props} qsConfig={QS_CONFIG} />
          )}
          renderItem={executionEnvironment => (
            <OrganizationExecEnvListItem
              key={executionEnvironment.id}
              executionEnvironment={executionEnvironment}
              detailUrl={`/execution_environments/${executionEnvironment.id}`}
            />
          )}
        />
      </Card>
    </>
  );
}

export default withI18n()(OrganizationExecEnvList);
