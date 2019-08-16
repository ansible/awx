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
    const { value, tooltip, onChange, required, i18n } = this.props;

    return (
      <FormGroup
        fieldId="project-lookup"
        isRequired={required}
        label={i18n._(t`Project`)}
      >
        {tooltip && (
          <Tooltip position="right" content={tooltip}>
            <QuestionCircleIcon />
          </Tooltip>
        )}
        <Lookup
          id="project-lookup"
          lookupHeader={i18n._(t`Projects`)}
          name="project"
          value={value}
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
  tooltip: string,
  onChange: func.isRequired,
  required: bool,
};

ProjectLookup.defaultProps = {
  value: null,
  tooltip: '',
  required: false,
};

export default withI18n()(ProjectLookup);
