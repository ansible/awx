import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Wizard } from '@patternfly/react-core';
import SelectResourceStep from './SelectResourceStep';
import SelectRoleStep from './SelectRoleStep';
import SelectableCard from './SelectableCard';
import { TeamsAPI, UsersAPI } from '../../api';

const readUsers = async queryParams =>
  UsersAPI.read(Object.assign(queryParams, { is_superuser: false }));

const readTeams = async queryParams => TeamsAPI.read(queryParams);

class AddResourceRole extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      selectedResource: null,
      selectedResourceRows: [],
      selectedRoleRows: [],
      currentStepId: 1,
      maxEnabledStep: 1,
    };

    this.handleResourceCheckboxClick = this.handleResourceCheckboxClick.bind(
      this
    );
    this.handleResourceSelect = this.handleResourceSelect.bind(this);
    this.handleRoleCheckboxClick = this.handleRoleCheckboxClick.bind(this);
    this.handleWizardNext = this.handleWizardNext.bind(this);
    this.handleWizardSave = this.handleWizardSave.bind(this);
    this.handleWizardGoToStep = this.handleWizardGoToStep.bind(this);
  }

  handleResourceCheckboxClick(user) {
    const { selectedResourceRows, currentStepId } = this.state;

    const selectedIndex = selectedResourceRows.findIndex(
      selectedRow => selectedRow.id === user.id
    );

    if (selectedIndex > -1) {
      selectedResourceRows.splice(selectedIndex, 1);
      const stateToUpdate = { selectedResourceRows };
      if (selectedResourceRows.length === 0) {
        stateToUpdate.maxEnabledStep = currentStepId;
      }
      this.setState(stateToUpdate);
    } else {
      this.setState(prevState => ({
        selectedResourceRows: [...prevState.selectedResourceRows, user],
      }));
    }
  }

  handleRoleCheckboxClick(role) {
    const { selectedRoleRows } = this.state;

    const selectedIndex = selectedRoleRows.findIndex(
      selectedRow => selectedRow.id === role.id
    );

    if (selectedIndex > -1) {
      selectedRoleRows.splice(selectedIndex, 1);
      this.setState({ selectedRoleRows });
    } else {
      this.setState(prevState => ({
        selectedRoleRows: [...prevState.selectedRoleRows, role],
      }));
    }
  }

  handleResourceSelect(resourceType) {
    this.setState({
      selectedResource: resourceType,
      selectedResourceRows: [],
      selectedRoleRows: [],
    });
  }

  handleWizardNext(step) {
    this.setState({
      currentStepId: step.id,
      maxEnabledStep: step.id,
    });
  }

  handleWizardGoToStep(step) {
    this.setState({
      currentStepId: step.id,
    });
  }

  async handleWizardSave() {
    const { onSave } = this.props;
    const {
      selectedResourceRows,
      selectedRoleRows,
      selectedResource,
    } = this.state;

    try {
      const roleRequests = [];

      for (let i = 0; i < selectedResourceRows.length; i++) {
        for (let j = 0; j < selectedRoleRows.length; j++) {
          if (selectedResource === 'users') {
            roleRequests.push(
              UsersAPI.associateRole(
                selectedResourceRows[i].id,
                selectedRoleRows[j].id
              )
            );
          } else if (selectedResource === 'teams') {
            roleRequests.push(
              TeamsAPI.associateRole(
                selectedResourceRows[i].id,
                selectedRoleRows[j].id
              )
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

  render() {
    const {
      selectedResource,
      selectedResourceRows,
      selectedRoleRows,
      currentStepId,
      maxEnabledStep,
    } = this.state;
    const { onClose, roles, i18n } = this.props;

    const userColumns = [
      {
        name: i18n._(t`Username`),
        key: 'username',
        isSortable: true,
        isSearchable: true,
      },
    ];

    const teamColumns = [
      {
        name: i18n._(t`Name`),
        key: 'name',
        isSortable: true,
        isSearchable: true,
      },
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
        name: i18n._(t`Select a Resource Type`),
        component: (
          <div style={{ display: 'flex', flexWrap: 'wrap' }}>
            <div style={{ width: '100%', marginBottom: '10px' }}>
              {i18n._(
                t`Choose the type of resource that will be receiving new roles.  For example, if you'd like to add new roles to a set of users please choose Users and click Next.  You'll be able to select the specific resources in the next step.`
              )}
            </div>
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
        enableNext: selectedResource !== null,
      },
      {
        id: 2,
        name: i18n._(t`Select Items from List`),
        component: (
          <Fragment>
            {selectedResource === 'users' && (
              <SelectResourceStep
                columns={userColumns}
                displayKey="username"
                onRowClick={this.handleResourceCheckboxClick}
                onSearch={readUsers}
                selectedLabel={i18n._(t`Selected`)}
                selectedResourceRows={selectedResourceRows}
                sortedColumnKey="username"
              />
            )}
            {selectedResource === 'teams' && (
              <SelectResourceStep
                columns={teamColumns}
                onRowClick={this.handleResourceCheckboxClick}
                onSearch={readTeams}
                selectedLabel={i18n._(t`Selected`)}
                selectedResourceRows={selectedResourceRows}
              />
            )}
          </Fragment>
        ),
        enableNext: selectedResourceRows.length > 0,
        canJumpTo: maxEnabledStep >= 2,
      },
      {
        id: 3,
        name: i18n._(t`Select Roles to Apply`),
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
        enableNext: selectedRoleRows.length > 0,
        canJumpTo: maxEnabledStep >= 3,
      },
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
        onGoToStep={this.handleWizardGoToStep}
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
  roles: PropTypes.shape(),
};

AddResourceRole.defaultProps = {
  roles: {},
};

export { AddResourceRole as _AddResourceRole };
export default withI18n()(AddResourceRole);
