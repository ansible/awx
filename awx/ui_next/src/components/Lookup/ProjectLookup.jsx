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
    result: { count, projects },
    error,
    request: fetchProjects,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      const { data } = await ProjectsAPI.read(params);
      if (data.count === 1) {
        onChange(data.results[0]);
      }
      return {
        count: data.count,
        projects: data.results,
      };
    }, [onChange, history.location.search]),
    {
      count: 0,
      projects: [],
    }
  );

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <FormGroup
      fieldId="project"
      helperTextInvalid={helperTextInvalid}
      isRequired={required}
      isValid={isValid}
      label={i18n._(t`Project`)}
    >
      {tooltip && <FieldTooltip content={tooltip} />}
      <Lookup
        id="project"
        header={i18n._(t`Project`)}
        name="project"
        value={value}
        onBlur={onBlur}
        onChange={onChange}
        required={required}
        qsConfig={QS_CONFIG}
        renderOptionsList={({ state, dispatch, canDelete }) => (
          <OptionsList
            value={state.selectedItems}
            searchColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isDefault: true,
              },
              {
                name: i18n._(t`Type`),
                key: 'scm_type',
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
                key: 'scm_url',
              },
              {
                name: i18n._(t`Modified By (Username)`),
                key: 'modified_by__username',
              },
              {
                name: i18n._(t`Created By (Username)`),
                key: 'created_by__username',
              },
            ]}
            sortColumns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
              },
            ]}
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
  value: Project,
  helperTextInvalid: node,
  isValid: bool,
  onBlur: func,
  onChange: func.isRequired,
  required: bool,
  tooltip: string,
};

ProjectLookup.defaultProps = {
  helperTextInvalid: '',
  isValid: true,
  required: false,
  tooltip: '',
  value: null,
  onBlur: () => {},
};

export { ProjectLookup as _ProjectLookup };
export default withI18n()(withRouter(ProjectLookup));
