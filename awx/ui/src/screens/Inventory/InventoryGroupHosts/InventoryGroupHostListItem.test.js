import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryGroupHostListItem from './InventoryGroupHostListItem';
import mockHosts from '../shared/data.hosts.json';

jest.mock('../../../api');

describe('<InventoryGroupHostListItem />', () => {
  let wrapper;
  const mockHost = mockHosts.results[0];

  beforeEach(() => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryGroupHostListItem
            detailUrl="/host/1"
            editUrl="/host/1"
            host={mockHost}
            isSelected={false}
            onSelect={() => {}}
            rowIndex={0}
          />
        </tbody>
      </table>
    );
  });

  test('should display expected details', () => {
    expect(wrapper.find('InventoryGroupHostListItem').length).toBe(1);
    expect(
      wrapper.find('Td[dataLabel="host-name-2"]').find('Link').prop('to')
    ).toBe('/host/1');
    expect(wrapper.find('Td[dataLabel="host-description-2"]').text()).toBe(
      'Bar'
    );
  });

  test('should display expected row item content', () => {
    expect(wrapper.find('b').text()).toContain(
      '.host-000001.group-00000.dummy'
    );
    expect(wrapper.find('Sparkline').length).toBe(1);
    expect(wrapper.find('HostToggle').length).toBe(1);
  });

  test('edit button shown to users with edit capabilities', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    const copyMockHost = { ...mockHost };
    copyMockHost.summary_fields.user_capabilities.edit = false;
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <InventoryGroupHostListItem
            detailUrl="/host/1"
            editUrl="/host/1"
            host={mockHost}
            isSelected={false}
            onSelect={() => {}}
            rowIndex={0}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
