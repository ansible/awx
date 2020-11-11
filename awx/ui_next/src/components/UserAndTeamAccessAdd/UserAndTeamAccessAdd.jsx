import React, { useState, useCallback, useEffect, useContext } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useParams } from 'react-router-dom';
import styled from 'styled-components';
import { Button, DropdownItem } from '@patternfly/react-core';
import { KebabifiedContext } from '../../contexts/Kebabified';
import useRequest, { useDismissableError } from '../../util/useRequest';
import SelectableCard from '../SelectableCard';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import Wizard from '../Wizard/Wizard';
import useSelected from '../../util/useSelected';
import SelectResourceStep from '../AddRole/SelectResourceStep';
import SelectRoleStep from '../AddRole/SelectRoleStep';
import getResourceAccessConfig from './getResourceAccessConfig';

const Grid = styled.div`
  display: grid;
  grid-gap: 20px;
  grid-template-columns: 33% 33% 33%;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
`;

function UserAndTeamAccessAdd({ i18n, title, onFetchData, apiModel }) {
  const [selectedResourceType, setSelectedResourceType] = useState(null);
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [stepIdReached, setStepIdReached] = useState(1);
  const { id: userId } = useParams();
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);
  const {
    selected: resourcesSelected,
    handleSelect: handleResourceSelect,
  } = useSelected([]);
  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isWizardOpen);
    }
  }, [isKebabified, isWizardOpen, onKebabModalChange]);

  const {
    selected: rolesSelected,
    handleSelect: handleRoleSelect,
  } = useSelected([]);

  const { request: handleWizardSave, error: saveError } = useRequest(
    useCallback(async () => {
      const roleRequests = [];
      const resourceRolesTypes = resourcesSelected.flatMap(resource =>
        Object.values(resource.summary_fields.object_roles)
      );

      rolesSelected.map(role =>
        resourceRolesTypes.forEach(rolename => {
          if (rolename.name === role.name) {
            roleRequests.push(apiModel.associateRole(userId, rolename.id));
          }
        })
      );

      await Promise.all(roleRequests);
      onFetchData();
      setIsWizardOpen(false);
    }, [onFetchData, rolesSelected, apiModel, userId, resourcesSelected]),
    {}
  );

  const { error, dismissError } = useDismissableError(saveError);

  const steps = [
    {
      id: 1,
      name: i18n._(t`Add resource type`),
      component: (
        <Grid>
          {getResourceAccessConfig(i18n).map(resource => (
            <SelectableCard
              key={resource.selectedResource}
              isSelected={
                resource.selectedResource ===
                selectedResourceType?.selectedResource
              }
              label={resource.label}
              dataCy={`add-role-${resource.selectedResource}`}
              onClick={() => setSelectedResourceType(resource)}
            />
          ))}
        </Grid>
      ),
      enableNext: selectedResourceType !== null,
    },
    {
      id: 2,
      name: i18n._(t`Select items from list`),
      component: selectedResourceType && (
        <SelectResourceStep
          searchColumns={selectedResourceType.searchColumns}
          sortColumns={selectedResourceType.sortColumns}
          displayKey="name"
          onRowClick={handleResourceSelect}
          fetchItems={selectedResourceType.fetchItems}
          fetchOptions={selectedResourceType.fetchOptions}
          selectedLabel={i18n._(t`Selected`)}
          selectedResourceRows={resourcesSelected}
          sortedColumnKey="username"
        />
      ),
      enableNext: resourcesSelected.length > 0,
      canJumpTo: stepIdReached >= 2,
    },
    {
      id: 3,
      name: i18n._(t`Select roles to apply`),
      component: resourcesSelected?.length > 0 && (
        <SelectRoleStep
          onRolesClick={handleRoleSelect}
          roles={resourcesSelected[0].summary_fields.object_roles}
          selectedListKey={
            selectedResourceType === 'users' ? 'username' : 'name'
          }
          selectedListLabel={i18n._(t`Selected`)}
          selectedResourceRows={resourcesSelected}
          selectedRoleRows={rolesSelected}
        />
      ),
      nextButtonText: i18n._(t`Save`),
      canJumpTo: stepIdReached >= 3,
    },
  ];

  if (error) {
    return (
      <AlertModal
        aria-label={i18n._(t`Associate role error`)}
        isOpen={error}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={dismissError}
      >
        {i18n._(t`Failed to associate role`)}
        <ErrorDetail error={error} />
      </AlertModal>
    );
  }

  return (
    <>
      {isKebabified ? (
        <DropdownItem
          key="add"
          component="button"
          aria-label={i18n._(t`Add`)}
          onClick={() => setIsWizardOpen(true)}
        >
          {i18n._(t`Add`)}
        </DropdownItem>
      ) : (
        <Button
          variant="primary"
          aria-label={i18n._(t`Add`)}
          onClick={() => setIsWizardOpen(true)}
          key="add"
        >
          {i18n._(t`Add`)}
        </Button>
      )}
      {isWizardOpen && (
        <Wizard
          isOpen={isWizardOpen}
          title={title}
          steps={steps}
          onClose={() => setIsWizardOpen(false)}
          onNext={({ id }) =>
            setStepIdReached(stepIdReached < id ? id : stepIdReached)
          }
          onSave={handleWizardSave}
        />
      )}
    </>
  );
}

export default withI18n()(UserAndTeamAccessAdd);
