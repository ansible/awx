import React, { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card } from '@patternfly/react-core';

import { ExecutionEnvironmentsAPI } from '../../../api';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest from '../../../util/useRequest';
import DatalistToolbar from '../../../components/DataListToolbar';
import PaginatedDataList from '../../../components/PaginatedDataList';

import ExecutionEnvironmentTemplateListItem from './ExecutionEnvironmentTemplateListItem';

const QS_CONFIG = getQSConfig(
  'execution_environments',
  {
    page: 1,
    page_size: 20,
    order_by: 'name',
    type: 'job_template,workflow_job_template',
  },
  ['id', 'page', 'page_size']
);

function ExecutionEnvironmentTemplateList({ i18n, executionEnvironment }) {
  const { id } = executionEnvironment;
  const location = useLocation();

  const {
    error: contentError,
    isLoading,
    request: fetchTemplates,
    result: {
      templates,
      templatesCount,
      relatedSearchableKeys,
      searchableKeys,
    },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);

      const [response, responseActions] = await Promise.all([
        ExecutionEnvironmentsAPI.readUnifiedJobTemplates(id, params),
        ExecutionEnvironmentsAPI.readUnifiedJobTemplateOptions(id),
      ]);

      return {
        templates: response.data.results,
        templatesCount: response.data.count,
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
      templates: [],
      templatesCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  return (
    <>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={isLoading}
          items={templates}
          itemCount={templatesCount}
          pluralizedItemName={i18n._(t`Templates`)}
          qsConfig={QS_CONFIG}
          toolbarSearchableKeys={searchableKeys}
          toolbarRelatedSearchableKeys={relatedSearchableKeys}
          toolbarSearchColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name__icontains',
              isDefault: true,
            },
            {
              name: i18n._(t`Type`),
              key: 'or__type',
              options: [
                [`job_template`, i18n._(t`Job Template`)],
                [`workflow_job_template`, i18n._(t`Workflow Template`)],
              ],
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
              name: i18n._(t`Name`),
              key: 'name',
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
          renderItem={template => (
            <ExecutionEnvironmentTemplateListItem
              key={template.id}
              template={template}
              detailUrl={`/templates/${template.type}/${template.id}/details`}
            />
          )}
        />
      </Card>
    </>
  );
}

export default withI18n()(ExecutionEnvironmentTemplateList);
