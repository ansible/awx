import React, { useEffect, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { Form, FormGroup } from '@patternfly/react-core';
import { ExecutionEnvironmentsAPI } from '../../api';
import Popover from '../Popover';

import { parseQueryString, getQSConfig } from '../../util/qs';
import useRequest from '../../util/useRequest';
import ContentError from '../ContentError';
import ContentLoading from '../ContentLoading';
import OptionsList from '../OptionsList';

const QS_CONFIG = getQSConfig('execution_environemts', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});
function AdHocExecutionEnvironmentStep() {
  const history = useHistory();
  const [executionEnvironmentField, , executionEnvironmentHelpers] = useField(
    'execution_environment'
  );
  const {
    error,
    isLoading,
    request: fetchExecutionEnvironments,
    result: { executionEnvironments, executionEnvironmentsCount },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);

      const {
        data: { results, count },
      } = await ExecutionEnvironmentsAPI.read(params);

      return {
        executionEnvironments: results,
        executionEnvironmentsCount: count,
      };
    }, [history.location.search]),
    { executionEnvironments: [], executionEnvironmentsCount: 0 }
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
    <Form>
      <FormGroup
        fieldId="execution_enviroment"
        label={t`Execution Environments`}
        aria-label={t`Execution Environments`}
        labelIcon={
          <Popover
            content={t`Select the Execution Environment you want this command to run inside`}
          />
        }
      >
        <OptionsList
          value={executionEnvironmentField.value || []}
          options={executionEnvironments}
          optionCount={executionEnvironmentsCount}
          header={t`Execution Environments`}
          qsConfig={QS_CONFIG}
          searchColumns={[
            {
              name: t`Name`,
              key: 'name',
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
          selectItem={value => {
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
