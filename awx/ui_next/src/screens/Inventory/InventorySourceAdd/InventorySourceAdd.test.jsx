import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventorySourceAdd from './InventorySourceAdd';
import { InventorySourcesAPI, ProjectsAPI } from '../../../api';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 111,
  }),
}));

describe('<InventorySourceAdd />', () => {
  let wrapper;
  const invSourceData = {
    credential: { id: 222 },
    description: 'bar',
    inventory: 111,
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

  ProjectsAPI.readInventories.mockResolvedValue({
    data: [],
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('new form displays primary form fields', async () => {
    const config = {
      custom_virtualenvs: ['venv/foo', 'venv/bar'],
    };
    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceAdd />, {
        context: { config },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('FormGroup[label="Name"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Description"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Source"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Ansible Environment"]')).toHaveLength(
      1
    );
  });

  test('should navigate to inventory sources list when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceAdd />, {
        context: { router: { history } },
      });
    });
    await act(async () => {
      wrapper.find('InventorySourceForm').invoke('onCancel')();
    });
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/111/sources'
    );
  });

  test('should post to the api when submit is clicked', async () => {
    InventorySourcesAPI.create.mockResolvedValueOnce({ data: {} });
    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceAdd />);
    });
    await act(async () => {
      wrapper.find('InventorySourceForm').invoke('onSubmit')(invSourceData);
    });
    expect(InventorySourcesAPI.create).toHaveBeenCalledTimes(1);
    expect(InventorySourcesAPI.create).toHaveBeenCalledWith({
      ...invSourceData,
      credential: 222,
      source_project: 999,
      source_script: null,
    });
  });

  test('successful form submission should trigger redirect', async () => {
    const history = createMemoryHistory({});
    InventorySourcesAPI.create.mockResolvedValueOnce({
      data: { id: 123, inventory: 111 },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceAdd />, {
        context: { router: { history } },
      });
    });
    await act(async () => {
      wrapper.find('InventorySourceForm').invoke('onSubmit')(invSourceData);
    });
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/111/sources/123/details'
    );
  });

  test('unsuccessful form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    InventorySourcesAPI.create.mockImplementation(() => Promise.reject(error));
    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceAdd />);
    });
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    await act(async () => {
      wrapper.find('InventorySourceForm').invoke('onSubmit')({});
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
