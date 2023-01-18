import React from 'react';
import { within, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InstanceGroupsAPI } from 'api';
import RemoveInstanceButton from './RemoveInstanceButton';
import { I18nProvider } from '@lingui/react';
import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import english from '../../../../src/locales/en/messages';

jest.mock('api');

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
    node_type: 'control',
    node_state: 'ready',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: true,
    managed_by_policy: false,
  },
];
describe('<RemoveInstanceButtton />', () => {
  test('Should open modal and deprovision node', async () => {
    i18n.loadLocaleData({ en: { plurals: en } });
    i18n.load({ en: english });
    i18n.activate('en');
    InstanceGroupsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1 }], count: 1 },
    });
    const user = userEvent.setup();
    const onRemove = jest.fn();
    render(
      <I18nProvider i18n={i18n}>
        <RemoveInstanceButton
          isK8s={true}
          itemsToRemove={[instances[0]]}
          onRemove={onRemove}
        />
      </I18nProvider>
    );

    const button = screen.getByRole('button');
    await user.click(button);
    await waitFor(() => screen.getByRole('dialog'));
    const modal = screen.getByRole('dialog');
    const removeButton = within(modal).getByRole('button', {
      name: 'Confirm remove',
    });

    await user.click(removeButton);

    await waitFor(() => expect(onRemove).toBeCalled());
  });

  test('Should be disabled', async () => {
    const user = userEvent.setup();
    render(
      <RemoveInstanceButton
        isK8s={true}
        itemsToRemove={[instances[1]]}
        onRemove={jest.fn()}
      />
    );

    const button = screen.getByRole('button');
    await user.hover(button);
    await waitFor(() =>
      screen.getByText('You do not have permission to remove instances:')
    );
  });

  test('Should handle error when fetching warning message details.', async () => {
    InstanceGroupsAPI.read.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/instance_groups',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    const user = userEvent.setup();
    const onRemove = jest.fn();
    render(
      <RemoveInstanceButton
        isK8s={true}
        itemsToRemove={[instances[0]]}
        onRemove={onRemove}
      />
    );

    const button = screen.getByRole('button');
    await user.click(button);
    await waitFor(() => screen.getByRole('dialog'));
    screen.getByText('Error!');
  });
});
