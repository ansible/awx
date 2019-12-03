import React, { useState, useEffect } from 'react';
import { string, func, bool } from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { ProjectsAPI } from '@api';
import { Project } from '@types';
import { FieldTooltip } from '@components/FormField';
import { getQSConfig, parseQueryString } from '@util/qs';
import Lookup from './Lookup';
import OptionsList from './shared/OptionsList';
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
  const [projects, setProjects] = useState([]);
  const [count, setCount] = useState(0);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      const params = parseQueryString(QS_CONFIG, history.location.search);
      try {
        const { data } = await ProjectsAPI.read(params);
        setProjects(data.results);
        setCount(data.count);
        if (data.count === 1) {
          onChange(data.results[0]);
        }
      } catch (err) {
        setError(err);
      }
    })();
  }, [history.location]);

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
  helperTextInvalid: string,
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
