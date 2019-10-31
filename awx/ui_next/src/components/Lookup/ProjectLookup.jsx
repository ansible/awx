import React from 'react';
import { string, func, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import { ProjectsAPI } from '@api';
import { Project } from '@types';
import Lookup from '@components/Lookup';
import { FieldTooltip } from '@components/FormField';

class ProjectLookup extends React.Component {
  render() {
    const {
      helperTextInvalid,
      i18n,
      isValid,
      onChange,
      required,
      tooltip,
      value,
      onBlur,
    } = this.props;

    const loadProjects = async params => {
      const response = await ProjectsAPI.read(params);
      const { results, count } = response.data;
      if (count === 1) {
        onChange(results[0], 'project');
      }
      return response;
    };

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
          lookupHeader={i18n._(t`Project`)}
          name="project"
          value={value}
          onBlur={onBlur}
          onLookupSave={onChange}
          getItems={loadProjects}
          required={required}
          sortedColumnKey="name"
          qsNamespace="project"
        />
      </FormGroup>
    );
  }
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

export default withI18n()(ProjectLookup);
