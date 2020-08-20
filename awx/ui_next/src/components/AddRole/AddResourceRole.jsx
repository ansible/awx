import React, { Fragment } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import SelectableCard from '../SelectableCard';
import Wizard from '../Wizard';
import SelectResourceStep from './SelectResourceStep';
import SelectRoleStep from './SelectRoleStep';
import { TeamsAPI, UsersAPI } from '../../api';

const readUsers = async queryParams =>
  UsersAPI.read(Object.assign(queryParams, { is_superuser: false }));

const readUsersOptions = async () => UsersAPI.readOptions();

const readTeams = async queryParams => TeamsAPI.read(queryParams);

const readTeamsOptions = async () => TeamsAPI.readOptions();

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

    // Object roles can be user only, so we remove them when
    // showing role choices for team access
    const selectableRoles = { ...roles };
    if (selectedResource === 'teams') {
      Object.keys(roles).forEach(key => {
        if (selectableRoles[key].user_only) {
          delete selectableRoles[key];
        }
      });
    }

    const userSearchColumns = [
      {
        name: i18n._(t`Username`),
        key: 'username__icontains',
        isDefault: true,
      },
      {
        name: i18n._(t`First Name`),
        key: 'first_name__icontains',
      },
      {
        name: i18n._(t`Last Name`),
        key: 'last_name__icontains',
      },
    ];

    const userSortColumns = [
      {
        name: i18n._(t`Username`),
        key: 'username',
      },
      {
        name: i18n._(t`First Name`),
        key: 'first_name',
      },
      {
        name: i18n._(t`Last Name`),
        key: 'last_name',
      },
    ];

    const teamSearchColumns = [
      {
        name: i18n._(t`Name`),
        key: 'name',
        isDefault: true,
      },
      {
        name: i18n._(t`Created By (Username)`),
        key: 'created_by__username',
      },
      {
        name: i18n._(t`Modified By (Username)`),
        key: 'modified_by__username',
      },
    ];

    const teamSortColumns = [
      {
        name: i18n._(t`Name`),
        key: 'name',
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
              dataCy="add-role-users"
              onClick={() => this.handleResourceSelect('users')}
            />
            <SelectableCard
              isSelected={selectedResource === 'teams'}
              label={i18n._(t`Teams`)}
              dataCy="add-role-teams"
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
                searchColumns={userSearchColumns}
                sortColumns={userSortColumns}
                displayKey="username"
                onRowClick={this.handleResourceCheckboxClick}
                fetchItems={readUsers}
                fetchOptions={readUsersOptions}
                selectedLabel={i18n._(t`Selected`)}
                selectedResourceRows={selectedResourceRows}
                sortedColumnKey="username"
              />
            )}
            {selectedResource === 'teams' && (
              <SelectResourceStep
                searchColumns={teamSearchColumns}
                sortColumns={teamSortColumns}
                onRowClick={this.handleResourceCheckboxClick}
                fetchItems={readTeams}
                fetchOptions={readTeamsOptions}
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
            roles={selectableRoles}
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
        backButtonText={i18n._(t`Back`)}
        cancelButtonText={i18n._(t`Cancel`)}
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
