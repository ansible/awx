import React, { useCallback, useEffect } from 'react';
import { string, func, bool, oneOfType, number } from 'prop-types';
import { useLocation } from 'react-router-dom';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { ExecutionEnvironmentsAPI, ProjectsAPI } from 'api';
import { ExecutionEnvironment } from 'types';
import { getQSConfig, parseQueryString, mergeParams } from 'util/qs';
import useRequest from 'hooks/useRequest';
import Popover from '../Popover';
import OptionsList from '../OptionsList';

import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('execution_environments', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function ExecutionEnvironmentLookup({
  globallyAvailable,
  helperTextInvalid,
  isDefaultEnvironment,
  isDisabled,
  isGlobalDefaultEnvironment,
  isValid,
  onBlur,
  onChange,
  organizationId,
  popoverContent,
  projectId,
  tooltip,
  validate,
  value,
  fieldName,
}) {
  const location = useLocation();

  const {
    request: fetchProject,
    error: fetchProjectError,
    isLoading: isProjectLoading,
    result: project,
  } = useRequest(
    useCallback(async () => {
      if (!projectId) {
        return {};
      }
      const { data } = await ProjectsAPI.readDetail(projectId);
      return data;
    }, [projectId]),
    {
      project: null,
      isLoading: true,
    }
  );

  useEffect(() => {
    fetchProject();
  }, [fetchProject]);

  const {
    result: {
      executionEnvironments,
      count,
      relatedSearchableKeys,
      searchableKeys,
    },
    request: fetchExecutionEnvironments,
    error,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      if (isProjectLoading) {
        return {
          executionEnvironments: [],
          count: 0,
        };
      }
      const params = parseQueryString(QS_CONFIG, location.search);
      const globallyAvailableParams = globallyAvailable
        ? { or__organization__isnull: 'True' }
        : {};
      const organizationIdParams = organizationId
        ? { or__organization__id: organizationId }
        : {};
      const projectIdParams =
        projectId && project?.organization
          ? {
              or__organization__id: project.organization,
            }
          : {};
      const [{ data }, actionsResponse] = await Promise.all([
        ExecutionEnvironmentsAPI.read(
          mergeParams(params, {
            ...globallyAvailableParams,
            ...organizationIdParams,
            ...projectIdParams,
          })
        ),
        ExecutionEnvironmentsAPI.readOptions(),
      ]);
      return {
        executionEnvironments: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter((key) => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [
      location,
      globallyAvailable,
      organizationId,
      projectId,
      project,
      isProjectLoading,
    ]),
    {
      executionEnvironments: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  const checkExecutionEnvironmentName = useCallback(
    async (name) => {
      if (!name) {
        onChange(null);
        return;
      }

      try {
        const {
          data: { results: nameMatchResults, count: nameMatchCount },
        } = await ExecutionEnvironmentsAPI.read({ name });
        onChange(nameMatchCount ? nameMatchResults[0] : null);
      } catch {
        onChange(null);
      }
    },
    [onChange]
  );

  useEffect(() => {
    fetchExecutionEnvironments();
  }, [fetchExecutionEnvironments]);

  const renderLookup = () => (
    <>
      <Lookup
        id="execution-environments"
        header={t`Execution Environment`}
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        onDebounce={checkExecutionEnvironmentName}
        fieldName={fieldName}
        validate={validate}
        qsConfig={QS_CONFIG}
        isLoading={isLoading || isProjectLoading}
        isDisabled={isDisabled}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={executionEnvironments}
            optionCount={count}
            searchColumns={[
              {
                name: t`Name`,
                key: 'name__icontains',
                isDefault: true,
              },
            ]}
            sortColumns={[
              {
                name: t`Name`,
                key: 'name',
              },
            ]}
            searchableKeys={searchableKeys}
            relatedSearchableKeys={relatedSearchableKeys}
            multiple={state.multiple}
            header={t`Execution Environment`}
            name="executionEnvironments"
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={(item) => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
    </>
  );

  const renderLabel = (
    globalDefaultEnvironment,
    defaultExecutionEnvironment
  ) => {
    if (globalDefaultEnvironment) {
      return t`Global Default Execution Environment`;
    }
    if (defaultExecutionEnvironment) {
      return t`Default Execution Environment`;
    }
    return t`Execution Environment`;
  };

  return (
    <FormGroup
      fieldId="execution-environment-lookup"
      label={renderLabel(isGlobalDefaultEnvironment, isDefaultEnvironment)}
      labelIcon={popoverContent && <Popover content={popoverContent} />}
      helperTextInvalid={helperTextInvalid}
      validated={isValid ? 'default' : 'error'}
    >
      {tooltip && isDisabled ? (
        <Tooltip content={tooltip}>{renderLookup()}</Tooltip>
      ) : (
        renderLookup()
      )}

      <LookupErrorMessage error={error || fetchProjectError} />
    </FormGroup>
  );
}

ExecutionEnvironmentLookup.propTypes = {
  value: ExecutionEnvironment,
  popoverContent: string,
  onChange: func.isRequired,
  isDefaultEnvironment: bool,
  isGlobalDefaultEnvironment: bool,
  projectId: oneOfType([number, string]),
  organizationId: oneOfType([number, string]),
  validate: func,
  fieldName: string,
};

ExecutionEnvironmentLookup.defaultProps = {
  popoverContent: '',
  isDefaultEnvironment: false,
  isGlobalDefaultEnvironment: false,
  value: null,
  projectId: null,
  organizationId: null,
  validate: () => undefined,
  fieldName: 'execution_environment',
};

export default ExecutionEnvironmentLookup;
