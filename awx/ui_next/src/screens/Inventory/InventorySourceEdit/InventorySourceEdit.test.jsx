import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventorySourceEdit from './InventorySourceEdit';
import { CredentialsAPI, InventorySourcesAPI, ProjectsAPI } from '../../../api';

jest.mock('../../../api/models/Projects');
jest.mock('../../../api/models/Credentials');
jest.mock('../../../api/models/InventorySources');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));

describe('<InventorySourceAdd />', () => {
  let wrapper;
  let history;
  const mockInvSrc = {
    id: 23,
    description: 'bar',
    inventory: 1,
    name: 'foo',
    overwrite: false,
    overwrite_vars: false,
    source: 'scm',
    source_path: 'mock/file.sh',
    source_project: { id: 999 },
    source_vars: '---↵',
    update_cache_timeout: 0,
    update_on_launch: false,
    update_on_project_update: false,
    verbosity: 1,
  };
  InventorySourcesAPI.readOptions.mockResolvedValue({
    data: {
      actions: {
        GET: {
          source: {
            choices: [
              ['file', 'File, Directory or Script'],
              ['scm', 'Sourced from a Project'],
              ['ec2', 'Amazon EC2'],
              ['gce', 'Google Compute Engine'],
              ['azure_rm', 'Microsoft Azure Resource Manager'],
              ['vmware', 'VMware vCenter'],
              ['satellite6', 'Red Hat Satellite 6'],
              ['openstack', 'OpenStack'],
              ['rhv', 'Red Hat Virtualization'],
              ['tower', 'Ansible Tower'],
            ],
          },
        },
      },
    },
  });
  InventorySourcesAPI.replace.mockResolvedValue({
    data: {
      ...mockInvSrc,
    },
  });
  ProjectsAPI.readInventories.mockResolvedValue({
    data: [],
  });
  CredentialsAPI.read.mockResolvedValue({
    data: { count: 0, results: [] },
  });
  ProjectsAPI.read.mockResolvedValue({
    data: {
      count: 2,
      results: [
        {
          id: 1,
          name: 'mock proj one',
        },
        {
          id: 2,
          name: 'mock proj two',
        },
      ],
    },
  });

  beforeAll(async () => {
    history = createMemoryHistory();
    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceEdit source={mockInvSrc} />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterAll(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('handleSubmit should call api update', async () => {
    expect(InventorySourcesAPI.replace).toHaveBeenCalledTimes(0);
    await act(async () => {
      wrapper.find('InventorySourceForm').invoke('onSubmit')(mockInvSrc);
    });
    expect(InventorySourcesAPI.replace).toHaveBeenCalledTimes(1);
  });

  test('should navigate to inventory source detail after successful submission', () => {
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/1/sources/23/details'
    );
  });

  test('should navigate to inventory source detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/1/sources/23/details'
    );
  });

  test('unsuccessful form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    InventorySourcesAPI.replace.mockImplementation(() => Promise.reject(error));
    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceEdit source={mockInvSrc} />);
    });
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    await act(async () => {
      wrapper.find('InventorySourceForm').invoke('onSubmit')({});
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
