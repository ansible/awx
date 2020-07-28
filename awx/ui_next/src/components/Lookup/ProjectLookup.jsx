import React, { useCallback, useEffect } from 'react';
import { node, string, func, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { ProjectsAPI } from '../../api';
import { Project } from '../../types';
import { FieldTooltip } from '../FormField';
import OptionsList from '../OptionsList';
import useRequest from '../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../util/qs';
import Lookup from './Lookup';
import LookupErrorMessage from './shared/LookupErrorMessage';

const QS_CONFIG = getQSConfig('project', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function ProjectLookup({
  helperTextInvalid,
  autocomplete,
  i18n,
  isValid,
  onChange,
  required,
  tooltip,
  value,
  onBlur,
  history,
}) {
  const {
    result: { projects, count, actions, relatedSearchFields },
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
      if (data.count === 1 && autocomplete) {
        autocomplete(data.results[0]);
      }
      return {
        count: data.count,
        projects: data.results,
        actions: actionsResponse.data.actions,
        relatedSearchFields: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
      };
    }, [history.location.search, autocomplete]),
    {
      count: 0,
      projects: [],
      actions: {},
      relatedSearchFields: [],
    }
  );

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const relatedSearchableKeys = relatedSearchFields || [];
  const searchableKeys = Object.keys(actions?.GET || {}).filter(
    key => actions.GET[key].filterable
  );

  return (
    <FormGroup
      fieldId="project"
      helperTextInvalid={helperTextInvalid}
      isRequired={required}
      validated={isValid ? 'default' : 'error'}
      label={i18n._(t`Project`)}
      labelIcon={tooltip && <FieldTooltip content={tooltip} />}
    >
      <Lookup
        id="project"
        header={i18n._(t`Project`)}
        name="project"
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        required={required}
        isLoading={isLoading}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            searchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name__icontains',
                isDefault: true,
              },
              {
                name: i18n._(t`Type`),
                key: 'or__scm_type',
                options: [
                  [``, i18n._(t`Manual`)],
                  [`git`, i18n._(t`Git`)],
                  [`hg`, i18n._(t`Mercurial`)],
                  [`svn`, i18n._(t`Subversion`)],
                  [`insights`, i18n._(t`Red Hat Insights`)],
                ],
              },
              {
                name: i18n._(t`Source Control URL`),
                key: 'scm_url__icontains',
              },
              {
                name: i18n._(t`Modified By (Username)`),
                key: 'modified_by__username__icontains',
              },
              {
                name: i18n._(t`Created By (Username)`),
                key: 'created_by__username__icontains',
              },
            ]}
            sortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
            ]}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            options={projects}
            optionCount={count}
            multiple={state.multiple}
            header={i18n._(t`Project`)}
            name="project"
            qsConfig={QS_CONFIG}
            readOnly={!canDelete}
            selectItem={item => dispatch({ type: 'SELECT_ITEM', item })}
            deselectItem={item => dispatch({ type: 'DESELECT_ITEM', item })}
          />
        )}
      />
      <LookupErrorMessage error={error} />
    </FormGroup>
  );
}

ProjectLookup.propTypes = {
  autocomplete: func,
  helperTextInvalid: node,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  tooltip: string,
  value: Project,
};

ProjectLookup.defaultProps = {
  autocomplete: () => {},
  helperTextInvalid: '',
  isValid: true,
  onBlur: () => {},
  required: false,
  tooltip: '',
  value: null,
};

export { ProjectLookup as _ProjectLookup };
export default withI18n()(withRouter(ProjectLookup));
