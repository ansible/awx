import React, { useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { Form, FormGroup } from '@patternfly/react-core';
import { ExecutionEnvironmentsAPI } from 'api';

import { parseQueryString, getQSConfig, mergeParams } from 'util/qs';
import { getSearchableKeys } from 'components/PaginatedTable';
import useRequest from 'hooks/useRequest';
import Popover from '../Popover';
import ContentError from '../ContentError';
import ContentLoading from '../ContentLoading';
import OptionsList from '../OptionsList';

const QS_CONFIG = getQSConfig('execution_environments', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});
function AdHocExecutionEnvironmentStep({ organizationId }) {
  const history = useHistory();
  const [executionEnvironmentField, , executionEnvironmentHelpers] = useField(
    'execution_environment'
  );
  const {
    error,
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
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const globallyAvailableParams = { or__organization__isnull: 'True' };
      const organizationIdParams = organizationId
        ? { or__organization__id: organizationId }
        : {};

      const [
        {
          data: { results, count },
        },
        actionsResponse,
      ] = await Promise.all([
        ExecutionEnvironmentsAPI.read(
          mergeParams(params, {
            ...globallyAvailableParams,
            ...organizationIdParams,
          })
        ),
        ExecutionEnvironmentsAPI.readOptions(),
      ]);
      return {
        executionEnvironments: results,
        executionEnvironmentsCount: count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [history.location.search, organizationId]),
    {
      executionEnvironments: [],
      executionEnvironmentsCount: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchExecutionEnvironments();
  }, [fetchExecutionEnvironments]);

  if (error) {
    return <ContentError error={error} />;
  }
  if (isLoading) {
    return <ContentLoading />;
  }

  return (
    <Form autoComplete="off">
      <FormGroup
        fieldId="execution_enviroment"
        label={t`Execution Environment`}
        aria-label={t`Execution Environment`}
        labelIcon={
          <Popover
            content={t`Select the Execution Environment you want this command to run inside.`}
          />
        }
      >
        <OptionsList
          isLoading={isLoading}
          value={executionEnvironmentField.value || []}
          options={executionEnvironments}
          optionCount={executionEnvironmentsCount}
          header={t`Execution Environments`}
          qsConfig={QS_CONFIG}
          searchColumns={[
            {
              name: t`Name`,
              key: 'name__icontains',
              isDefault: true,
            },
            {
              name: t`Created By (Username)`,
              key: 'created_by__username',
            },
            {
              name: t`Modified By (Username)`,
              key: 'modified_by__username',
            },
          ]}
          sortColumns={[
            {
              name: t`Name`,
              key: 'name',
            },
          ]}
          name="execution_environment"
          searchableKeys={searchableKeys}
          relatedSearchableKeys={relatedSearchableKeys}
          selectItem={(value) => {
            executionEnvironmentHelpers.setValue([value]);
          }}
          deselectItem={() => {
            executionEnvironmentHelpers.setValue([]);
          }}
        />
      </FormGroup>
    </Form>
  );
}
export default AdHocExecutionEnvironmentStep;
