import React from 'react';
import { string, func, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import { ProjectsAPI } from '@api';
import { Project } from '@types';
import Lookup from '@components/Lookup';
import styled from 'styled-components';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

const loadProjects = async params => ProjectsAPI.read(params);

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

    return (
      <FormGroup
        fieldId="project"
        helperTextInvalid={helperTextInvalid}
        isRequired={required}
        isValid={isValid}
        label={i18n._(t`Project`)}
      >
        {tooltip && (
          <Tooltip position="right" content={tooltip}>
            <QuestionCircleIcon />
          </Tooltip>
        )}
        <Lookup
          id="project"
          lookupHeader={i18n._(t`Projects`)}
          name="project"
          value={value}
          onBlur={onBlur}
          onLookupSave={onChange}
          getItems={loadProjects}
          required={required}
          sortedColumnKey="name"
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
