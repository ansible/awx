import getChipsByKey from './getChipsByKey';

describe('getChipsByKey', () => {
  const qsConfig = {
    namespace: 'job',
    defaultParams: {
      order_by: '-finished',
      page: 1,
      page_size: 20,
    },
    integerFields: ['id', 'page', 'page_size'],
    dateFields: ['modified', 'created'],
  };
  const columns = [
    { name: 'Name', key: 'name__icontains', isDefault: true },
    { name: 'ID', key: 'id' },
    {
      name: 'Job Type',
      key: 'or__type',
      options: [
        ['project_update', 'Source Control Update'],
        ['inventory_update', 'Inventory Sync'],
        ['job', 'Playbook Run'],
        ['ad_hoc_command', 'Command'],
        ['system_job', 'Management Job'],
        ['workflow_job', 'Workflow Job'],
      ],
    },
    { name: 'Limit', key: 'job__limit' },
  ];
  const defaultQueryParams = {
    page: 1,
    page_size: 20,
    order_by: '-finished',
  };

  test('should get initial chips', () => {
    expect(getChipsByKey(defaultQueryParams, columns, qsConfig)).toEqual({
      id: {
        key: 'id',
        label: 'ID (id)',
        chips: [],
      },
      job__limit: {
        key: 'job__limit',
        label: 'Limit (job__limit)',
        chips: [],
      },
      name__icontains: {
        key: 'name__icontains',
        label: 'Name (name__icontains)',
        chips: [],
      },
      or__type: {
        key: 'or__type',
        label: 'Job Type (or__type)',
        chips: [],
      },
    });
  });

  test('should get chips from query string', () => {
    const queryParams = {
      page: 1,
      page_size: 20,
      order_by: '-finished',
      name__icontains: 'job',
    };

    expect(getChipsByKey(queryParams, columns, qsConfig)).toEqual({
      id: {
        key: 'id',
        label: 'ID (id)',
        chips: [],
      },
      job__limit: {
        key: 'job__limit',
        label: 'Limit (job__limit)',
        chips: [],
      },
      name__icontains: {
        key: 'name__icontains',
        label: 'Name (name__icontains)',
        chips: [
          {
            key: 'name__icontains:job',
            node: 'job',
          },
        ],
      },
      or__type: {
        key: 'or__type',
        label: 'Job Type (or__type)',
        chips: [],
      },
    });
  });
});
