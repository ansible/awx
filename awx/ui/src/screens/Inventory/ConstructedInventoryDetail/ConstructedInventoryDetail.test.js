import React from 'react';
import { Router } from 'react-router-dom';
import { InventoriesAPI, ConstructedInventoriesAPI } from 'api';
import {
  render,
  screen,
  waitForElementToBeRemoved,
} from '@testing-library/react';
import '@testing-library/jest-dom';
import { createMemoryHistory } from 'history';
import { I18nProvider } from '@lingui/react';
import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import english from '../../../locales/en/messages';
import ConstructedInventoryDetail from './ConstructedInventoryDetail';

jest.mock('../../../api');

const mockInventory = {
  id: 1,
  type: 'inventory',
  summary_fields: {
    organization: {
      id: 1,
      name: 'The Organization',
      description: '',
    },
    created_by: {
      username: 'the_creator',
      id: 2,
    },
    modified_by: {
      username: 'the_modifier',
      id: 3,
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
      adhoc: true,
    },
    labels: {
      count: 1,
      results: [
        {
          id: 17,
          name: 'seventeen',
        },
      ],
    },
  },
  created: '2019-10-04T16:56:48.025455Z',
  modified: '2019-10-04T16:56:48.025468Z',
  name: 'Constructed Inv',
  description: '',
  organization: 1,
  kind: 'constructed',
  has_active_failures: false,
  total_hosts: 0,
  hosts_with_active_failures: 0,
  total_groups: 0,
  groups_with_active_failures: 0,
  has_inventory_sources: false,
  total_inventory_sources: 0,
  inventory_sources_with_failures: 0,
  pending_deletion: false,
  prevent_instance_group_fallback: true,
  update_cache_timeout: 0,
  limit: '',
  verbosity: 1,
  source_vars:
    '{\n    "plugin": "constructed",\n    "strict": true,\n    "groups": {\n        "shutdown": "resolved_state == \\"shutdown\\"",\n        "shutdown_in_product_dev": "resolved_state == \\"shutdown\\" and account_alias == \\"product_dev\\""\n    },\n    "compose": {\n        "resolved_state": "state | default(\\"running\\")"\n    }\n}',
};

describe('<ConstructedInventoryDetail />', () => {
  const history = createMemoryHistory({
    initialEntries: ['/inventories/constructed_inventory/1/details'],
  });

  const Component = (props) => (
    <I18nProvider i18n={i18n}>
      <Router history={history}>
        <ConstructedInventoryDetail inventory={mockInventory} {...props} />
      </Router>
    </I18nProvider>
  );

  beforeEach(() => {
    i18n.loadLocaleData({ en: { plurals: en } });
    i18n.load({ en: english });
    i18n.activate('en');

    InventoriesAPI.readInstanceGroups.mockResolvedValue({
      data: { results: [] },
    });
    InventoriesAPI.readInputInventories.mockResolvedValue({
      data: {
        results: [
          {
            id: 123,
            name: 'input_inventory_123',
          },
          {
            id: 456,
            name: 'input_inventory_456',
          },
        ],
      },
    });
    InventoriesAPI.readSources.mockResolvedValue({
      data: {
        results: [
          {
            id: 999,
            type: 'inventory_source',
            summary_fields: {
              last_job: {
                id: 101,
                name: 'Auto-created source for: Constructed Inv',
                status: 'successful',
                finished: '2023-02-02T22:22:22.222220Z',
              },
              user_capabilities: {
                start: true,
              },
            },
          },
        ],
      },
    });
    ConstructedInventoriesAPI.readOptions.mockResolvedValue({
      data: {
        related: {},
        actions: {
          GET: {
            limit: {
              label: 'Limit',
              help_text: '',
            },
            total_groups: {
              label: 'Total Groups',
              help_text: '',
            },
            total_hosts: {
              label: 'Total Hosts',
              help_text: '',
            },
            total_inventory_sources: {
              label: 'Total inventory sources',
              help_text: '',
            },
            update_cache_timeout: {
              label: 'Update cache timeout',
              help_text: '',
            },
            inventory_sources_with_failures: {
              label: 'Inventory sources with failures',
              help_text: '',
            },
            source_vars: {
              label: 'Source vars',
              help_text: '',
            },
            verbosity: {
              label: 'Verbosity',
              help_text: '',
            },
            created: {
              label: 'Created by',
              help_text: '',
            },
            modified: {
              label: 'Modified by',
              help_text: '',
            },
          },
        },
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render details', async () => {
    render(<Component />);
    await waitForElementToBeRemoved(() => screen.getByRole('progressbar'));
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Constructed Inv')).toBeInTheDocument();
    expect(screen.getByText('Last Job Status')).toBeInTheDocument();
    expect(screen.getByText('Successful')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Constructed Inventory')).toBeInTheDocument();
  });

  test('should render action buttons', async () => {
    render(<Component />);
    await waitForElementToBeRemoved(() => screen.getByRole('progressbar'));
    expect(screen.getByRole('link', { name: 'Edit' })).toHaveAttribute(
      'href',
      '/inventories/constructed_inventory/1/edit'
    );
    expect(
      screen.getByRole('button', { name: 'Start inventory source sync' })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
  });

  test('should show cancel sync button during an inventory source sync running job', async () => {
    InventoriesAPI.readSources.mockResolvedValue({
      data: {
        results: [
          {
            id: 999,
            type: 'inventory_source',
            summary_fields: {
              current_job: {
                id: 111,
                name: 'Auto-created source for: Constructed Inv',
                status: 'running',
              },
              user_capabilities: {
                start: true,
              },
            },
          },
        ],
      },
    });
    render(<Component />);
    await waitForElementToBeRemoved(() => screen.getByRole('progressbar'));
    expect(
      screen.getByRole('button', {
        name: 'Cancel Constructed Inventory Source Sync',
      })
    ).toBeInTheDocument();
  });

  test('should show error when the api throws while fetching details', async () => {
    InventoriesAPI.readInputInventories.mockRejectedValueOnce(new Error());
    render(<Component />);
    await waitForElementToBeRemoved(() => screen.getByRole('progressbar'));
    expect(
      screen.getByText(
        'There was an error loading this content. Please reload the page.'
      )
    ).toBeInTheDocument();
  });
});
