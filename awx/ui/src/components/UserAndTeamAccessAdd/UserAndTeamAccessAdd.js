import React, { useState, useCallback } from 'react';
import { t } from '@lingui/macro';
import { useParams, useRouteMatch } from 'react-router-dom';
import styled from 'styled-components';
import useRequest from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import SelectableCard from '../SelectableCard';
import Wizard from '../Wizard/Wizard';
import SelectResourceStep from '../AddRole/SelectResourceStep';
import SelectRoleStep from '../AddRole/SelectRoleStep';
import getResourceAccessConfig from './getResourceAccessConfig';

const Grid = styled.div`
  display: grid;
  grid-gap: 20px;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
`;

function UserAndTeamAccessAdd({
  title,
  onFetchData,
  apiModel,
  onClose,
  onError,
}) {
  const [selectedResourceType, setSelectedResourceType] = useState(null);
  const [stepIdReached, setStepIdReached] = useState(1);
  const { id: userId } = useParams();
  const teamsRouteMatch = useRouteMatch({
    path: '/teams/:id/roles',
    exact: true,
  });

  const { selected: resourcesSelected, handleSelect: handleResourceSelect } =
    useSelected([]);

  const { selected: rolesSelected, handleSelect: handleRoleSelect } =
    useSelected([]);

  const { request: handleWizardSave, error: saveError } = useRequest(
    useCallback(async () => {
      const roleRequests = [];
      const resourceRolesTypes = resourcesSelected.flatMap((resource) =>
        Object.values(resource.summary_fields.object_roles)
      );

      rolesSelected.map((role) =>
        resourceRolesTypes.forEach((rolename) => {
          if (rolename.name === role.name) {
            roleRequests.push(apiModel.associateRole(userId, rolename.id));
          }
        })
      );

      await Promise.all(roleRequests);
      onFetchData();
    }, [onFetchData, rolesSelected, apiModel, userId, resourcesSelected]),
    {}
  );

  // Object roles can be user only, so we remove them when
  // showing role choices for team access
  const selectableRoles = {
    ...resourcesSelected[0]?.summary_fields?.object_roles,
  };
  if (teamsRouteMatch && resourcesSelected[0]?.type === 'organization') {
    Object.keys(selectableRoles).forEach((key) => {
      if (selectableRoles[key].user_only) {
        delete selectableRoles[key];
      }
    });
  }

  const steps = [
    {
      id: 1,
      name: t`Add resource type`,
      component: (
        <Grid>
          {getResourceAccessConfig().map((resource) => (
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
      name: t`Select items from list`,
      component: selectedResourceType && (
        <SelectResourceStep
          searchColumns={selectedResourceType.searchColumns}
          sortColumns={selectedResourceType.sortColumns}
          displayKey="name"
          onRowClick={handleResourceSelect}
          fetchItems={selectedResourceType.fetchItems}
          fetchOptions={selectedResourceType.fetchOptions}
          selectedLabel={t`Selected`}
          selectedResourceRows={resourcesSelected}
          sortedColumnKey="username"
        />
      ),
      enableNext: resourcesSelected.length > 0,
      canJumpTo: stepIdReached >= 2,
    },
    {
      id: 3,
      name: t`Select roles to apply`,
      component: resourcesSelected?.length > 0 && (
        <SelectRoleStep
          onRolesClick={handleRoleSelect}
          roles={selectableRoles}
          selectedListKey={
            selectedResourceType === 'users' ? 'username' : 'name'
          }
          selectedListLabel={t`Selected`}
          selectedResourceRows={resourcesSelected}
          selectedRoleRows={rolesSelected}
        />
      ),
      nextButtonText: t`Save`,
      canJumpTo: stepIdReached >= 3,
    },
  ];

  if (saveError) {
    onError(saveError);
    onClose();
  }

  return (
    <Wizard
      isOpen
      title={title}
      steps={steps}
      onClose={onClose}
      onNext={({ id }) =>
        setStepIdReached(stepIdReached < id ? id : stepIdReached)
      }
      onSave={handleWizardSave}
    />
  );
}

export default UserAndTeamAccessAdd;
