import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventorySourceListItem from './InventorySourceListItem';

const source = {
  id: 1,
  name: 'Foo',
  source: 'Source Bar',
  summary_fields: {
    user_capabilities: { start: true, edit: true },
    last_job: {
      canceled_on: '2020-04-30T18:56:46.054087Z',
      description: '',
      failed: true,
      finished: '2020-04-30T18:56:46.054031Z',
      id: 664,
      license_error: false,
      name: ' Inventory 1 Org 0 - source 4',
      status: 'canceled',
    },
  },
};
describe('<InventorySourceListItem />', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });
  test('should mount properly', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <InventorySourceListItem
        source={source}
        isSelected={false}
        onSelect={onSelect}
        label="Source Bar"
      />
    );
    expect(wrapper.find('InventorySourceListItem').length).toBe(1);
  });

  test('all buttons and text fields should render properly', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <InventorySourceListItem
        source={source}
        isSelected={false}
        onSelect={onSelect}
        label="Source Bar"
      />
    );
    expect(wrapper.find('StatusIcon').length).toBe(1);
    expect(
      wrapper
        .find('Link')
        .at(0)
        .prop('to')
    ).toBe('/jobs/inventory/664');
    expect(wrapper.find('DataListCheck').length).toBe(1);
    expect();
    expect(
      wrapper
        .find('DataListCell')
        .at(1)
        .text()
    ).toBe('Foo');
    expect(
      wrapper
        .find('DataListCell')
        .at(2)
        .text()
    ).toBe('Source Bar');
    expect(wrapper.find('InventorySourceSyncButton').length).toBe(1);
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
  });

  test('item should be checked', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <InventorySourceListItem
        source={source}
        isSelected
        onSelect={onSelect}
        label="Source Bar"
      />
    );
    expect(wrapper.find('DataListCheck').length).toBe(1);
    expect(wrapper.find('DataListCheck').prop('checked')).toBe(true);
  });

  test('should not render status icon', () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <InventorySourceListItem
        source={{
          ...source,
          summary_fields: {
            user_capabilities: { start: true, edit: true },
            last_job: null,
          },
        }}
        isSelected={false}
        onSelect={onSelect}
        label="Source Bar"
      />
    );
    expect(wrapper.find('StatusIcon').length).toBe(0);
  });

  test('should not render sync buttons', async () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <InventorySourceListItem
        source={{
          ...source,
          summary_fields: { user_capabilities: { start: false, edit: true } },
        }}
        isSelected={false}
        onSelect={onSelect}
      />
    );
    expect(wrapper.find('InventorySourceSyncButton').length).toBe(0);
    expect(wrapper.find('Button[aria-label="Edit Source"]').length).toBe(1);
  });

  test('should not render edit buttons', async () => {
    const onSelect = jest.fn();
    wrapper = mountWithContexts(
      <InventorySourceListItem
        source={{
          ...source,
          summary_fields: { user_capabilities: { start: true, edit: false } },
        }}
        isSelected={false}
        onSelect={onSelect}
        label="Source Bar"
      />
    );
    expect(wrapper.find('Button[aria-label="Edit Source"]').length).toBe(0);
    expect(wrapper.find('InventorySourceSyncButton').length).toBe(1);
  });
});
