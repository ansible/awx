import React, { useCallback, useEffect } from 'react';
import { node, string, func, bool, object, oneOfType } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { ProjectsAPI } from 'api';
import { Project } from 'types';
import useAutoPopulateLookup from 'hooks/useAutoPopulateLookup';
import useRequest from 'hooks/useRequest';
import { getSearchableKeys } from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import OptionsList from '../OptionsList';
import Popover from '../Popover';
import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('project', {
  page: 1,
  page_size: 5,
  order_by: 'name',
  role_level: 'use_role',
});

function ProjectLookup({
  helperTextInvalid,
  autoPopulate,
  isValid,
  onChange,
  required,
  tooltip,
  value,
  onBlur,
  history,
  isOverrideDisabled,
  validate,
  fieldName,
}) {
  const autoPopulateLookup = useAutoPopulateLookup(onChange);
  const {
    result: { projects, count, relatedSearchableKeys, searchableKeys, canEdit },
    request: fetchProjects,
    error,
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const [{ data }, actionsResponse] = await Promise.all([
        ProjectsAPI.read(params),
        ProjectsAPI.readOptions(),
      ]);
      if (autoPopulate) {
        autoPopulateLookup(data.results);
      }
      return {
        count: data.count,
        projects: data.results,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
        canEdit:
          Boolean(actionsResponse.data.actions.POST) || isOverrideDisabled,
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [autoPopulate, autoPopulateLookup, history.location.search]),
    {
      count: 0,
      projects: [],
      relatedSearchableKeys: [],
      searchableKeys: [],
      canEdit: false,
    }
  );

  const checkProjectName = useCallback(
    async (name) => {
      if (!name) {
        onChange(null);
        return;
      }

      try {
        const {
          data: { results: nameMatchResults, count: nameMatchCount },
        } = await ProjectsAPI.read({ name });
        onChange(nameMatchCount ? nameMatchResults[0] : null);
      } catch {
        onChange(null);
      }
    },
    [onChange]
  );

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <FormGroup
      fieldId="project"
      helperTextInvalid={helperTextInvalid}
      isRequired={required}
      validated={isValid ? 'default' : 'error'}
      label={t`Project`}
      labelIcon={tooltip && <Popover content={tooltip} />}
    >
      <Lookup
        id="project"
        header={t`Project`}
        name="project"
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        onDebounce={checkProjectName}
        fieldName={fieldName}
        validate={validate}
        required={required}
        isLoading={isLoading}
        isDisabled={!canEdit}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            searchColumns={[
              {
                name: t`Name`,
                key: 'name__icontains',
                isDefault: true,
              },
              {
                name: t`Type`,
                key: 'or__scm_type',
                options: [
                  [``, t`Manual`],
                  [`git`, t`Git`],
                  [`svn`, t`Subversion`],
                  [`archive`, t`Remote Archive`],
                  [`insights`, t`Red Hat Insights`],
                ],
              },
              {
                name: t`Source Control URL`,
                key: 'scm_url__icontains',
              },
              {
                name: t`Modified By (Username)`,
                key: 'modified_by__username__icontains',
              },
              {
                name: t`Created By (Username)`,
                key: 'created_by__username__icontains',
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
            options={projects}
            optionCount={count}
            multiple={state.multiple}
            header={t`Project`}
            name="project"
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={(item) => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={(item) => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </FormGroup>
  );
}

ProjectLookup.propTypes = {
  autoPopulate: bool,
  helperTextInvalid: node,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  tooltip: string,
  value: oneOfType([Project, object]),
  isOverrideDisabled: bool,
  validate: func,
  fieldName: string,
};

ProjectLookup.defaultProps = {
  autoPopulate: false,
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  tooltip: '',
  value: null,
  isOverrideDisabled: false,
  validate: () => undefined,
  fieldName: 'project',
};

export { ProjectLookup as _ProjectLookup };
export default withRouter(ProjectLookup);
