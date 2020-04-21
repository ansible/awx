import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import InventorySourceListItem from './InventorySourceListItem';

const source = {
  id: 1,
  name: 'Foo',
  source: 'Source Bar',
  summary_fields: { user_capabilities: { start: true, edit: true } },
};
describe('<InventorySourceListItem />', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });
  test('should mount properly', async () => {
    let wrapper;
    const onSelect = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceListItem
          source={source}
          isSelected={false}
          onSelect={onSelect}
        />
      );
    });
    expect(wrapper.find('InventorySourceListItem').length).toBe(1);
  });
  test('all buttons and text fields should render properly', async () => {
    let wrapper;
    const onSelect = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceListItem
          source={source}
          isSelected={false}
          onSelect={onSelect}
        />
      );
    });
    expect(wrapper.find('DataListCheck').length).toBe(1);
    expect(
      wrapper
        .find('DataListCell')
        .at(0)
        .text()
    ).toBe('Foo');
    expect(
      wrapper
        .find('DataListCell')
        .at(1)
        .text()
    ).toBe('Source Bar');
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
  });

  test('item should be checked', async () => {
    let wrapper;
    const onSelect = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceListItem
          source={source}
          isSelected
          onSelect={onSelect}
        />
      );
    });
    expect(wrapper.find('DataListCheck').length).toBe(1);
    expect(wrapper.find('DataListCheck').prop('checked')).toBe(true);
  });

  test(' should render edit buttons', async () => {
    let wrapper;
    const onSelect = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceListItem
          source={{
            ...source,
            summary_fields: { user_capabilities: { edit: false, start: true } },
          }}
          isSelected={false}
          onSelect={onSelect}
        />
      );
    });
    expect(wrapper.find('Button[aria-label="Edit Source"]').length).toBe(0);
  });
});
