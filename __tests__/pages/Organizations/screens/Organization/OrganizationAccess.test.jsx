import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import OrganizationAccess from '../../../../../src/pages/Organizations/screens/Organization/OrganizationAccess';
import { sleep } from '../../../../testUtils';

describe('<OrganizationAccess />', () => {
  let network;
  const organization = {
    id: 1,
    name: 'Default',
    summary_fields: {
      object_roles: {},
      user_capabilities: {
        edit: true
      }
    }
  };

  const data = {
    count: 2,
    results: [{
      id: 1,
      username: 'joe',
      url: '/foo',
      first_name: 'joe',
      last_name: 'smith',
      summary_fields: {
        direct_access: [{
          role: {
            id: 1,
            name: 'Member',
            resource_name: 'Org',
            resource_type: 'organization',
            user_capabilities: { unattach: true },
          }
        }],
        indirect_access: [],
      }
    }, {
      id: 2,
      username: 'jane',
      url: '/bar',
      first_name: 'jane',
      last_name: 'brown',
      summary_fields: {
        direct_access: [{
          role: {
            id: 3,
            name: 'Member',
            resource_name: 'Org',
            resource_type: 'organization',
            team_id: 5,
            team_name: 'The Team',
            user_capabilities: { unattach: true },
          }
        }],
        indirect_access: [],
      }
    }]
  };

  beforeEach(() => {
    network = {
      api: {
        getOrganizationAccessList: jest.fn()
          .mockReturnValue(Promise.resolve({ data })),
        disassociateTeamRole: jest.fn(),
        disassociateUserRole: jest.fn(),
        toJSON: () => '/api/',
      },
    };
  });

  test('initially renders succesfully', () => {
    const wrapper = mountWithContexts(
      <OrganizationAccess organization={organization} />,
      { context: { network } }
    );
    expect(wrapper.find('OrganizationAccess')).toMatchSnapshot();
  });

  test('should fetch and display access records on mount', async () => {
    const wrapper = mountWithContexts(
      <OrganizationAccess organization={organization} />,
      { context: { network } }
    );
    await sleep(0);
    wrapper.update();
    expect(network.api.getOrganizationAccessList).toHaveBeenCalled();
    expect(wrapper.find('OrganizationAccess').state('isInitialized')).toBe(true);
    expect(wrapper.find('PaginatedDataList').prop('items')).toEqual(data.results);
    expect(wrapper.find('OrganizationAccessItem')).toHaveLength(2);
  });

  test('should open confirmation dialog when deleting role', async () => {
    const wrapper = mountWithContexts(
      <OrganizationAccess organization={organization} />,
      { context: { network } }
    );
    await sleep(0);
    wrapper.update();

    const button = wrapper.find('ChipButton').at(0);
    button.prop('onClick')();
    wrapper.update();

    const component = wrapper.find('OrganizationAccess');
    expect(component.state('roleToDelete'))
      .toEqual(data.results[0].summary_fields.direct_access[0].role);
    expect(component.state('roleToDeleteAccessRecord'))
      .toEqual(data.results[0]);
    expect(component.find('DeleteRoleConfirmationModal')).toHaveLength(1);
  });

  it('should close dialog when cancel button clicked', async () => {
    const wrapper = mountWithContexts(
      <OrganizationAccess organization={organization} />,
      { context: { network } }
    );
    await sleep(0);
    wrapper.update();
    const button = wrapper.find('ChipButton').at(0);
    button.prop('onClick')();
    wrapper.update();

    wrapper.find('DeleteRoleConfirmationModal').prop('onCancel')();
    const component = wrapper.find('OrganizationAccess');
    expect(component.state('roleToDelete')).toBeNull();
    expect(component.state('roleToDeleteAccessRecord')).toBeNull();
    expect(network.api.disassociateTeamRole).not.toHaveBeenCalled();
    expect(network.api.disassociateUserRole).not.toHaveBeenCalled();
  });

  it('should delete user role', async () => {
    const wrapper = mountWithContexts(
      <OrganizationAccess organization={organization} />,
      { context: { network } }
    );
    await sleep(0);
    wrapper.update();
    const button = wrapper.find('ChipButton').at(0);
    button.prop('onClick')();
    wrapper.update();

    wrapper.find('DeleteRoleConfirmationModal').prop('onConfirm')();
    await sleep(0);
    wrapper.update();

    const component = wrapper.find('OrganizationAccess');
    expect(component.state('roleToDelete')).toBeNull();
    expect(component.state('roleToDeleteAccessRecord')).toBeNull();
    expect(network.api.disassociateTeamRole).not.toHaveBeenCalled();
    expect(network.api.disassociateUserRole).toHaveBeenCalledWith(1, 1);
    expect(network.api.getOrganizationAccessList).toHaveBeenCalledTimes(2);
  });

  it('should delete team role', async () => {
    const wrapper = mountWithContexts(
      <OrganizationAccess organization={organization} />,
      { context: { network } }
    );
    await sleep(0);
    wrapper.update();
    const button = wrapper.find('ChipButton').at(1);
    button.prop('onClick')();
    wrapper.update();

    wrapper.find('DeleteRoleConfirmationModal').prop('onConfirm')();
    await sleep(0);
    wrapper.update();

    const component = wrapper.find('OrganizationAccess');
    expect(component.state('roleToDelete')).toBeNull();
    expect(component.state('roleToDeleteAccessRecord')).toBeNull();
    expect(network.api.disassociateTeamRole).toHaveBeenCalledWith(5, 3);
    expect(network.api.disassociateUserRole).not.toHaveBeenCalled();
    expect(network.api.getOrganizationAccessList).toHaveBeenCalledTimes(2);
  });
});
