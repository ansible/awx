import React, { useCallback, useEffect } from 'react';
import { string, func, bool, oneOfType, number } from 'prop-types';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';

import { ExecutionEnvironmentsAPI, ProjectsAPI } from '../../api';
import { ExecutionEnvironment } from '../../types';
import { getQSConfig, parseQueryString, mergeParams } from '../../util/qs';
import Popover from '../Popover';
import OptionsList from '../OptionsList';
import useRequest from '../../util/useRequest';

import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('execution_environments', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function ExecutionEnvironmentLookup({
  globallyAvailable,
  i18n,
  isDefaultEnvironment,
  isGlobalDefaultEnvironment,
  isDisabled,
  onBlur,
  onChange,
  organizationId,
  popoverContent,
  projectId,
  tooltip,
  value,
}) {
  const location = useLocation();

  const {
    request: fetchProject,
    error: fetchProjectError,
    isLoading: fetchProjectLoading,
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
      const params = parseQueryString(QS_CONFIG, location.search);
      const globallyAvailableParams = globallyAvailable
        ? { or__organization__isnull: 'True' }
        : {};
      const organizationIdParams =
        organizationId || project?.organization
          ? { or__organization__id: organizationId }
          : {};
      const [{ data }, actionsResponse] = await Promise.all([
        ExecutionEnvironmentsAPI.read(
          mergeParams(params, {
            ...globallyAvailableParams,
            ...organizationIdParams,
          })
        ),
        ExecutionEnvironmentsAPI.readOptions(),
      ]);
      return {
        executionEnvironments: data.results,
        count: data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [location, globallyAvailable, organizationId, project]),
    {
      executionEnvironments: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchExecutionEnvironments();
  }, [fetchExecutionEnvironments]);

  const renderLookup = () => (
    <>
      <Lookup
        id="execution-environments"
        header={i18n._(t`Execution Environments`)}
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        qsConfig={QS_CONFIG}
        isLoading={isLoading || fetchProjectLoading}
        isDisabled={isDisabled}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            options={executionEnvironments}
            optionCount={count}
            searchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name__icontains',
                isDefault: true,
              },
            ]}
            sortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
            ]}
            searchableKeys={searchableKeys}
            relatedSearchableKeys={relatedSearchableKeys}
            multiple={state.multiple}
            header={i18n._(t`Execution Environment`)}
            name="executionEnvironments"
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
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
      return i18n._(t`Global Default Execution Environment`);
    }
    if (defaultExecutionEnvironment) {
      return i18n._(t`Default Execution Environment`);
    }
    return i18n._(t`Execution Environment`);
  };

  return (
    <FormGroup
      fieldId="execution-environment-lookup"
      label={renderLabel(isGlobalDefaultEnvironment, isDefaultEnvironment)}
      labelIcon={popoverContent && <Popover content={popoverContent} />}
    >
      {tooltip ? (
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
};

ExecutionEnvironmentLookup.defaultProps = {
  popoverContent: '',
  isDefaultEnvironment: false,
  isGlobalDefaultEnvironment: false,
  value: null,
  projectId: null,
  organizationId: null,
};

export default withI18n()(ExecutionEnvironmentLookup);
