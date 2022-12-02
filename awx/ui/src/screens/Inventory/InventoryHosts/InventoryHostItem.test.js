import React from 'react';
import { Router } from 'react-router-dom';
import {
  render,
  fireEvent,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import '@testing-library/jest-dom';
import { HostsAPI } from 'api';
import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import InventoryHostItem from './InventoryHostItem';
import { createMemoryHistory } from 'history';
import english from '../../../locales/en/messages';

jest.mock('api');

const mockHost = {
  id: 1,
  name: 'Host 1',
  url: '/api/v2/hosts/1',
  description: 'Bar',
  inventory: 1,
  summary_fields: {
    inventory: {
      id: 1,
      name: 'Inv 1',
    },
    user_capabilities: {
      edit: true,
    },
    recent_jobs: [
      {
        id: 123,
        name: 'Demo Job Template',
        status: 'failed',
        finished: '2020-02-26T22:38:41.037991Z',
      },
    ],
    groups: {
      count: 1,
      results: [
        {
          id: 11,
          name: 'group_11',
        },
      ],
    },
  },
};

describe('<InventoryHostItem />', () => {
  const history = createMemoryHistory({
    initialEntries: ['/inventories/inventory/1/hosts'],
  });

  const getChips = (currentScreen) => {
    const list = currentScreen.getByRole('list', {
      name: 'Related Groups',
    });
    const { getAllByRole } = within(list);
    const items = getAllByRole('listitem');
    return items.map((item) => item.textContent);
  };

  const Component = (props) => (
    <Router history={history}>
      <table>
        <tbody>
          <InventoryHostItem
            detailUrl="/host/1"
            editUrl={`/inventories/inventory/1/hosts/1/edit`}
            host={mockHost}
            isSelected={false}
            onSelect={() => {}}
            {...props}
          />
        </tbody>
      </table>
    </Router>
  );

  beforeEach(() => {
    i18n.loadLocaleData({ en: { plurals: en } });
    i18n.load({ en: english });
    i18n.activate('en');
  });

  test('should display expected details', () => {
    render(<Component />);

    expect(screen.getByRole('cell', { name: 'Bar' })).toBeInTheDocument();
    expect(
      screen.getByRole('checkbox', { name: 'Toggle host' })
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Host 1' })).toHaveAttribute(
      'href',
      '/host/1'
    );
    expect(screen.getByRole('link', { name: 'Edit host' })).toHaveAttribute(
      'href',
      '/inventories/inventory/1/hosts/1/edit'
    );

    const relatedGroupChips = getChips(screen);
    expect(relatedGroupChips).toEqual(['group_11']);
  });

  test('edit button hidden from users without edit capabilities', () => {
    const copyMockHost = { ...mockHost };
    copyMockHost.summary_fields.user_capabilities.edit = false;

    render(<Component host={copyMockHost} />);
    expect(screen.queryByText('Edit host')).toBeNull();
  });

  test('should show and hide related groups on overflow button click', async () => {
    const copyMockHost = { ...mockHost };
    const mockGroups = [
      {
        id: 1,
        name: 'group_1',
      },
      {
        id: 2,
        name: 'group_2',
      },
      {
        id: 3,
        name: 'group_3',
      },
      {
        id: 4,
        name: 'group_4',
      },
      {
        id: 5,
        name: 'group_5',
      },
      {
        id: 6,
        name: 'group_6',
      },
    ];
    copyMockHost.summary_fields.groups = {
      count: 6,
      results: mockGroups.slice(0, 5),
    };
    HostsAPI.readGroups.mockReturnValue({
      data: {
        results: mockGroups,
      },
    });

    render(<Component host={copyMockHost} />);

    const initialRelatedGroupChips = getChips(screen);
    expect(initialRelatedGroupChips).toEqual([
      'group_1',
      'group_2',
      'group_3',
      'group_4',
      '2 more',
    ]);

    const overflowGroupsButton = screen.queryByText('2 more');
    fireEvent.click(overflowGroupsButton);

    await waitFor(() => expect(HostsAPI.readGroups).toHaveBeenCalledWith(1));

    const expandedRelatedGroupChips = getChips(screen);
    expect(expandedRelatedGroupChips).toEqual([
      'group_1',
      'group_2',
      'group_3',
      'group_4',
      'group_5',
      'group_6',
      'Show less',
    ]);

    const collapseGroupsButton = await screen.findByText('Show less');
    fireEvent.click(collapseGroupsButton);

    const collapsedRelatedGroupChips = getChips(screen);
    expect(collapsedRelatedGroupChips).toEqual(initialRelatedGroupChips);
  });

  test('should show error modal when related groups api request fails', async () => {
    const copyMockHost = { ...mockHost };
    const mockGroups = [
      {
        id: 1,
        name: 'group_1',
      },
      {
        id: 2,
        name: 'group_2',
      },
      {
        id: 3,
        name: 'group_3',
      },
      {
        id: 4,
        name: 'group_4',
      },
      {
        id: 5,
        name: 'group_5',
      },
      {
        id: 6,
        name: 'group_6',
      },
    ];
    copyMockHost.summary_fields.groups = {
      count: 6,
      results: mockGroups.slice(0, 5),
    };
    HostsAPI.readGroups.mockRejectedValueOnce(new Error());

    render(<Component host={copyMockHost} />);
    await waitFor(() => {
      const overflowGroupsButton = screen.queryByText('2 more');
      fireEvent.click(overflowGroupsButton);
    });
    expect(screen.getByRole('dialog', { name: 'Alert modal Error!' }));
  });
});
