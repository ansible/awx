import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Wizard } from '@patternfly/react-core';
import SelectResourceStep from './SelectResourceStep';
import SelectRoleStep from './SelectRoleStep';
import SelectableCard from './SelectableCard';

class AddResourceRole extends React.Component {
  constructor (props) {
    super(props);

    this.state = {
      selectedResource: null,
      selectedResourceRows: [],
      selectedRoleRows: [],
      currentStepId: 1,
    };

    this.handleResourceCheckboxClick = this.handleResourceCheckboxClick.bind(this);
    this.handleResourceSelect = this.handleResourceSelect.bind(this);
    this.handleRoleCheckboxClick = this.handleRoleCheckboxClick.bind(this);
    this.handleWizardNext = this.handleWizardNext.bind(this);
    this.handleWizardSave = this.handleWizardSave.bind(this);
    this.readTeams = this.readTeams.bind(this);
    this.readUsers = this.readUsers.bind(this);
  }

  handleResourceCheckboxClick (user) {
    const { selectedResourceRows } = this.state;

    const selectedIndex = selectedResourceRows
      .findIndex(selectedRow => selectedRow.id === user.id);

    if (selectedIndex > -1) {
      selectedResourceRows.splice(selectedIndex, 1);
      this.setState({ selectedResourceRows });
    } else {
      this.setState(prevState => ({
        selectedResourceRows: [...prevState.selectedResourceRows, user]
      }));
    }
  }

  handleRoleCheckboxClick (role) {
    const { selectedRoleRows } = this.state;

    const selectedIndex = selectedRoleRows
      .findIndex(selectedRow => selectedRow.id === role.id);

    if (selectedIndex > -1) {
      selectedRoleRows.splice(selectedIndex, 1);
      this.setState({ selectedRoleRows });
    } else {
      this.setState(prevState => ({
        selectedRoleRows: [...prevState.selectedRoleRows, role]
      }));
    }
  }

  handleResourceSelect (resourceType) {
    this.setState({
      selectedResource: resourceType,
      selectedResourceRows: [],
      selectedRoleRows: []
    });
  }

  handleWizardNext (step) {
    this.setState({
      currentStepId: step.id,
    });
  }

  async handleWizardSave () {
    const {
      onSave,
      api
    } = this.props;
    const {
      selectedResourceRows,
      selectedRoleRows,
      selectedResource
    } = this.state;

    try {
      const roleRequests = [];

      for (let i = 0; i < selectedResourceRows.length; i++) {
        for (let j = 0; j < selectedRoleRows.length; j++) {
          if (selectedResource === 'users') {
            roleRequests.push(
              api.createUserRole(selectedResourceRows[i].id, selectedRoleRows[j].id)
            );
          } else if (selectedResource === 'teams') {
            roleRequests.push(
              api.createTeamRole(selectedResourceRows[i].id, selectedRoleRows[j].id)
            );
          }
        }
      }

      await Promise.all(roleRequests);
      onSave();
    } catch (err) {
      // TODO: handle this error
    }
  }

  async readUsers (queryParams) {
    const { api } = this.props;
    return api.readUsers(Object.assign(queryParams, { is_superuser: false }));
  }

  async readTeams (queryParams) {
    const { api } = this.props;
    return api.readTeams(queryParams);
  }

  render () {
    const {
      selectedResource,
      selectedResourceRows,
      selectedRoleRows,
      currentStepId,
    } = this.state;
    const {
      onClose,
      roles,
      i18n
    } = this.props;

    const userColumns = [
      { name: i18n._(t`Username`), key: 'username', isSortable: true }
    ];

    const teamColumns = [
      { name: i18n._(t`Name`), key: 'name', isSortable: true }
    ];

    let wizardTitle = '';

    switch (selectedResource) {
      case 'users':
        wizardTitle = i18n._(t`Add User Roles`);
        break;
      case 'teams':
        wizardTitle = i18n._(t`Add Team Roles`);
        break;
      default:
        wizardTitle = i18n._(t`Add Roles`);
    }

    const steps = [
      {
        id: 1,
        name: i18n._(t`Select Users Or Teams`),
        component: (
          <div style={{ display: 'flex' }}>
            <SelectableCard
              isSelected={selectedResource === 'users'}
              label={i18n._(t`Users`)}
              onClick={() => this.handleResourceSelect('users')}
            />
            <SelectableCard
              isSelected={selectedResource === 'teams'}
              label={i18n._(t`Teams`)}
              onClick={() => this.handleResourceSelect('teams')}
            />
          </div>
        ),
        enableNext: selectedResource !== null
      },
      {
        id: 2,
        name: i18n._(t`Select items from list`),
        component: (
          <Fragment>
            {selectedResource === 'users' && (
              <SelectResourceStep
                columns={userColumns}
                displayKey="username"
                onRowClick={this.handleResourceCheckboxClick}
                onSearch={this.readUsers}
                selectedLabel={i18n._(t`Selected`)}
                selectedResourceRows={selectedResourceRows}
                sortedColumnKey="username"
                itemName="user"
              />
            )}
            {selectedResource === 'teams' && (
              <SelectResourceStep
                columns={teamColumns}
                onRowClick={this.handleResourceCheckboxClick}
                onSearch={this.readTeams}
                selectedLabel={i18n._(t`Selected`)}
                selectedResourceRows={selectedResourceRows}
                itemName="team"
              />
            )}
          </Fragment>
        ),
        enableNext: selectedResourceRows.length > 0
      },
      {
        id: 3,
        name: i18n._(t`Apply roles`),
        component: (
          <SelectRoleStep
            onRolesClick={this.handleRoleCheckboxClick}
            roles={roles}
            selectedListKey={selectedResource === 'users' ? 'username' : 'name'}
            selectedListLabel={i18n._(t`Selected`)}
            selectedResourceRows={selectedResourceRows}
            selectedRoleRows={selectedRoleRows}
          />
        ),
        nextButtonText: i18n._(t`Save`),
        enableNext: selectedRoleRows.length > 0
      }
    ];

    const currentStep = steps.find(step => step.id === currentStepId);

    // TODO: somehow internationalize steps and currentStep.nextButtonText
    return (
      <Wizard
        style={{ overflow: 'scroll' }}
        isOpen
        onNext={this.handleWizardNext}
        onClose={onClose}
        onSave={this.handleWizardSave}
        steps={steps}
        title={wizardTitle}
        nextButtonText={currentStep.nextButtonText || undefined}
      />
    );
  }
}

AddResourceRole.propTypes = {
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  roles: PropTypes.shape()
};

AddResourceRole.defaultProps = {
  roles: {}
};

export default withI18n()(AddResourceRole);
