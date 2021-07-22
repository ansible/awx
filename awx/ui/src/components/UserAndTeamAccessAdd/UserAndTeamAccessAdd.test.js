import React from 'react';
import { act } from 'react-dom/test-utils';
import { UsersAPI, JobTemplatesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import UserAndTeamAccessAdd from './UserAndTeamAccessAdd';

jest.mock('../../api');

const onError = jest.fn();
const onClose = jest.fn();

describe('<UserAndTeamAccessAdd/>', () => {
  const resources = {
    data: {
      results: [
        {
          id: 1,
          name: 'Job Template Foo Bar',
          url: '/api/v2/job_template/1/',
          summary_fields: {
            object_roles: {
              admin_role: {
                description: 'Can manage all aspects of the job template',
                name: 'Admin',
                id: 164,
              },
              execute_role: {
                description: 'May run the job template',
                name: 'Execute',
                id: 165,
              },
              read_role: {
                description: 'May view settings for the job template',
                name: 'Read',
                id: 166,
              },
            },
          },
        },
      ],
      count: 1,
    },
  };
  const options = {
    data: {
      actions: {
        GET: {},
        POST: {},
      },
      related_search_fields: [],
    },
  };
  let wrapper;
  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserAndTeamAccessAdd
          apiModel={UsersAPI}
          onFetchData={() => {}}
          onClose={onClose}
          title="Add user permissions"
          onError={onError}
        />
      );
    });
    wrapper.update();
  });
  afterEach(() => {
    jest.resetAllMocks();
  });
  test('should mount properly', async () => {
    expect(wrapper.find('PFWizard').length).toBe(1);
  });
  test('should disable steps', async () => {
    expect(wrapper.find('Button[type="submit"]').prop('isDisabled')).toBe(true);
    expect(
      wrapper
        .find('WizardNavItem[content="Select items from list"]')
        .prop('isDisabled')
    ).toBe(true);
    expect(
      wrapper
        .find('WizardNavItem[content="Select roles to apply"]')
        .prop('isDisabled')
    ).toBe(true);
    await act(async () =>
      wrapper.find('SelectableCard[label="Job templates"]').prop('onClick')({
        fetchItems: JobTemplatesAPI.read,
        label: 'Job template',
        selectedResource: 'jobTemplate',
        searchColumns: [
          { name: 'Name', key: 'name__icontains', isDefault: true },
        ],
        sortColumns: [{ name: 'Name', key: 'name' }],
      })
    );
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();
    expect(
      wrapper
        .find('WizardNavItem[content="Add resource type"]')
        .prop('isDisabled')
    ).toBe(false);
    expect(
      wrapper
        .find('WizardNavItem[content="Select items from list"]')
        .prop('isDisabled')
    ).toBe(false);
    expect(
      wrapper
        .find('WizardNavItem[content="Select roles to apply"]')
        .prop('isDisabled')
    ).toBe(true);
  });

  test('should call api to associate role', async () => {
    JobTemplatesAPI.read.mockResolvedValue(resources);
    JobTemplatesAPI.readOptions.mockResolvedValue(options);
    UsersAPI.associateRole.mockResolvedValue({});
    await act(async () =>
      wrapper.find('SelectableCard[label="Job templates"]').prop('onClick')({
        fetchItems: JobTemplatesAPI.read,
        fetchOptions: JobTemplatesAPI.readOptions,
        label: 'Job template',
        selectedResource: 'jobTemplate',
        searchColumns: [
          { name: 'Name', key: 'name__icontains', isDefault: true },
        ],
        sortColumns: [{ name: 'Name', key: 'name' }],
      })
    );
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    expect(JobTemplatesAPI.read).toHaveBeenCalledWith({
      order_by: 'name',
      page: 1,
      page_size: 5,
    });

    await waitForElement(wrapper, 'SelectResourceStep', (el) => el.length > 0);
    expect(JobTemplatesAPI.read).toHaveBeenCalled();
    await act(async () =>
      wrapper
        .find('CheckboxListItem')
        .first()
        .find('input[type="checkbox"]')
        .simulate('click')
    );

    wrapper.update();

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    wrapper.update();

    expect(wrapper.find('RolesStep').length).toBe(1);

    await act(async () =>
      wrapper.find('CheckboxCard').first().prop('onSelect')()
    );

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    await expect(UsersAPI.associateRole).toHaveBeenCalled();
  });

  test('should close wizard on cancel', async () => {
    await act(async () =>
      wrapper.find('Button[children="Cancel"]').prop('onClick')()
    );
    wrapper.update();
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test('should throw error', async () => {
    expect(onError).toHaveBeenCalledTimes(0);
    JobTemplatesAPI.read.mockResolvedValue(resources);
    JobTemplatesAPI.readOptions.mockResolvedValue(options);
    UsersAPI.associateRole.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/users/a/roles',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );

    await act(async () =>
      wrapper.find('SelectableCard[label="Job templates"]').prop('onClick')({
        fetchItems: JobTemplatesAPI.read,
        fetchOptions: JobTemplatesAPI.readOptions,
        label: 'Job template',
        selectedResource: 'jobTemplate',
        searchColumns: [
          { name: 'Name', key: 'name__icontains', isDefault: true },
        ],
        sortColumns: [{ name: 'Name', key: 'name' }],
      })
    );
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    await waitForElement(wrapper, 'SelectResourceStep', (el) => el.length > 0);
    expect(JobTemplatesAPI.read).toHaveBeenCalled();
    await act(async () =>
      wrapper
        .find('CheckboxListItem')
        .first()
        .find('input[type="checkbox"]')
        .simulate('click')
    );

    wrapper.update();

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    wrapper.update();

    expect(wrapper.find('RolesStep').length).toBe(1);

    await act(async () =>
      wrapper.find('CheckboxCard').first().prop('onSelect')()
    );

    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );

    await expect(UsersAPI.associateRole).toHaveBeenCalled();
    wrapper.update();
    expect(onError).toHaveBeenCalled();
  });
});
