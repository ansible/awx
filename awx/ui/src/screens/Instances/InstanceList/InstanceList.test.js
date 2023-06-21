import React from 'react';
import { Route, Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import * as ConfigContext from 'contexts/Config';
import { within, render, waitFor, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import { InstanceGroupsAPI, InstancesAPI, SettingsAPI } from 'api';

import { I18nProvider } from '@lingui/react';
import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import english from '../../../../src/locales/en/messages';
import InstanceList from './InstanceList';

jest.mock('../../../api/models/InstanceGroups');
jest.mock('../../../api/models/Instances');
jest.mock('../../../api/models/Settings');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
  useLocation: () => ({
    search: '',
  }),
}));

const instances = [
  {
    id: 1,
    type: 'instance',
    url: '/api/v2/instances/1/',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    node_type: 'execution',
    node_state: 'ready',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: true,
    managed_by_policy: true,
    hostname: 'alex',
  },
  {
    id: 2,
    type: 'instance',
    url: '/api/v2/instances/2/',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    node_type: 'execution',
    node_state: 'ready',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: true,
    managed_by_policy: false,
    hostname: 'athena',
  },
  {
    id: 3,
    type: 'instance',
    url: '/api/v2/instances/3/',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    node_type: 'execution',
    node_state: 'ready',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: false,
    managed_by_policy: true,
    hostname: 'apollo',
  },
  {
    id: 4,
    type: 'instance',
    url: '/api/v2/instances/4/',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    node_type: 'hop',
    node_state: 'ready',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: false,
    managed_by_policy: true,
    hostname: 'Eno',
  },
];

describe('<InstanceList />, React testing library tests', () => {
  const user = userEvent.setup();
  const options = { data: { actions: { POST: true } } };

  const history = createMemoryHistory({
    initialEntries: ['/instances'],
  });

  i18n.loadLocaleData({ en: { plurals: en } });
  i18n.load({ en: english });
  i18n.activate('en');

  const customRender = (ui, isK8s = true) => {
    jest.spyOn(ConfigContext, 'useConfig').mockImplementation(() => ({
      me: { is_superuser: true },
    }));
    InstancesAPI.read.mockResolvedValue({
      data: {
        count: instances.length,
        results: instances,
      },
    });
    InstancesAPI.readOptions.mockResolvedValue(options);
    SettingsAPI.readCategory.mockResolvedValue({ data: { IS_K8S: isK8s } });

    InstanceGroupsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1 }], count: 1 },
    });

    return render(
      <I18nProvider i18n={i18n}>
        <Router history={history}>
          <Route path="/instances">{ui} </Route>
        </Router>
      </I18nProvider>
    );
  };

  test('Should show error modal on failure to deprovision instance', async () => {
    InstancesAPI.deprovisionInstance.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/instances',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );

    await waitFor(() => customRender(<InstanceList />));

    const selectedRowItem = screen.getByRole('checkbox', {
      name: 'Select row 2',
    });
    const button = screen.getByRole('button', { name: 'Remove' });

    await user.click(selectedRowItem);
    await user.click(button);

    await waitFor(() => screen.getByRole('dialog'));
    const deprovisionModal = screen.getByRole('dialog');
    const removeButton = within(deprovisionModal).getByRole('button', {
      name: 'Confirm remove',
    });

    await user.click(removeButton);
    await waitFor(() =>
      expect(InstancesAPI.deprovisionInstance).toBeCalledWith(3)
    );
    screen.getByText('Error!');
  });

  test('Should fetch instances from the api and render them in the list', async () => {
    await waitFor(() => customRender(<InstanceList />));
    expect(InstancesAPI.read).toHaveBeenCalled();
    expect(InstancesAPI.readOptions).toHaveBeenCalled();
    expect(screen.getAllByTestId('instances list item')).toHaveLength(4);
  });

  test('Should run health check, and inform user to reload the page', async () => {
    await waitFor(() => customRender(<InstanceList />));
    const selectedRowItem = screen.getByRole('checkbox', {
      name: 'Select row 2',
    });
    const button = screen.getByRole('button', { name: 'Run health check' });

    await user.click(selectedRowItem);
    await user.click(button);

    await waitFor(() =>
      screen.getByText(
        'Health check request(s) submitted. Please wait and reload the page.'
      )
    );
  });

  test('Should render health check error', async () => {
    InstancesAPI.healthCheck.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'create',
            url: '/api/v2/instances',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );

    await waitFor(() => customRender(<InstanceList />));
    const selectedRowItem = screen.getByRole('checkbox', {
      name: 'Select row 2',
    });
    const button = screen.getByRole('button', { name: 'Run health check' });

    await user.click(selectedRowItem);
    await user.click(button);

    expect(screen.getByText('Error!')).toBeInTheDocument();
  });
  test('Should show Add button', async () => {
    await waitFor(() => customRender(<InstanceList />));
    expect(screen.getByRole('link', { name: 'Add' })).toBeInTheDocument();
  });

  test('Should not show Add button', async () => {
    await waitFor(() => customRender(<InstanceList />, false));
    const add = screen.queryByText('Add');
    expect(add).toBeNull();
  });
});
