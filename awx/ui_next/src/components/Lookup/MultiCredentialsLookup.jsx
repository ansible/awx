import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup, Tooltip } from '@patternfly/react-core';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import { CredentialsAPI, CredentialTypesAPI } from '@api';
import Lookup from '@components/Lookup';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

class MultiCredentialsLookup extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      selectedCredentialType: { label: 'Machine', id: 1, kind: 'ssh' },
      credentialTypes: [],
    };
    this.loadCredentialTypes = this.loadCredentialTypes.bind(this);
    this.handleCredentialTypeSelect = this.handleCredentialTypeSelect.bind(
      this
    );
    this.loadCredentials = this.loadCredentials.bind(this);
    this.toggleCredentialSelection = this.toggleCredentialSelection.bind(this);
  }

  componentDidMount() {
    this.loadCredentialTypes();
  }

  async loadCredentialTypes() {
    const { onError } = this.props;
    try {
      const { data } = await CredentialTypesAPI.read();
      const acceptableTypes = ['machine', 'cloud', 'net', 'ssh', 'vault'];
      const credentialTypes = [];
      data.results.forEach(cred => {
        acceptableTypes.forEach(aT => {
          if (aT === cred.kind) {
            // This object has several repeated values as some of it's children
            // require different field values.
            cred = {
              id: cred.id,
              key: cred.id,
              kind: cred.kind,
              type: cred.namespace,
              value: cred.name,
              label: cred.name,
              isDisabled: false,
            };
            credentialTypes.push(cred);
          }
        });
      });
      this.setState({ credentialTypes });
    } catch (err) {
      onError(err);
    }
  }

  async loadCredentials(params) {
    const { selectedCredentialType } = this.state;
    params.credential_type = selectedCredentialType.id || 1;
    return CredentialsAPI.read(params);
  }

  toggleCredentialSelection(newCredential) {
    const { onChange, credentials: credentialsToUpdate } = this.props;

    let newCredentialsList;
    const isSelectedCredentialInState =
      credentialsToUpdate.filter(cred => cred.id === newCredential.id).length >
      0;

    if (isSelectedCredentialInState) {
      newCredentialsList = credentialsToUpdate.filter(
        cred => cred.id !== newCredential.id
      );
    } else {
      newCredentialsList = credentialsToUpdate.filter(
        credential =>
          credential.kind === 'vault' || credential.kind !== newCredential.kind
      );
      newCredentialsList = [...newCredentialsList, newCredential];
    }
    onChange(newCredentialsList);
  }

  handleCredentialTypeSelect(value, type) {
    const { credentialTypes } = this.state;
    const selectedType = credentialTypes.filter(item => item.label === type);
    this.setState({ selectedCredentialType: selectedType[0] });
  }

  render() {
    const { selectedCredentialType, credentialTypes } = this.state;
    const { tooltip, i18n, credentials } = this.props;
    return (
      <FormGroup label={i18n._(t`Credentials`)} fieldId="multiCredential">
        {tooltip && (
          <Tooltip position="right" content={tooltip}>
            <QuestionCircleIcon />
          </Tooltip>
        )}
        {credentialTypes && (
          <Lookup
            selectCategoryOptions={credentialTypes}
            selectCategory={this.handleCredentialTypeSelect}
            selectedCategory={selectedCredentialType}
            onToggleItem={this.toggleCredentialSelection}
            onloadCategories={this.loadCredentialTypes}
            id="multiCredential"
            lookupHeader={i18n._(t`Credentials`)}
            name="credentials"
            value={credentials}
            multiple
            onLookupSave={() => {}}
            getItems={this.loadCredentials}
            qsNamespace="credentials"
            columns={[
              {
                name: i18n._(t`Name`),
                key: 'name',
                isSortable: true,
                isSearchable: true,
              },
            ]}
            sortedColumnKey="name"
          />
        )}
      </FormGroup>
    );
  }
}

MultiCredentialsLookup.propTypes = {
  tooltip: PropTypes.string,
  credentials: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      name: PropTypes.string,
      description: PropTypes.string,
      kind: PropTypes.string,
      clound: PropTypes.bool,
    })
  ),
  onChange: PropTypes.func.isRequired,
  onError: PropTypes.func.isRequired,
};

MultiCredentialsLookup.defaultProps = {
  tooltip: '',
  credentials: [],
};
export { MultiCredentialsLookup as _MultiCredentialsLookup };

export default withI18n()(MultiCredentialsLookup);
