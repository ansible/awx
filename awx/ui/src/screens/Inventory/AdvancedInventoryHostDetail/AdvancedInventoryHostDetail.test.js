import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import AdvancedInventoryHostDetail from './AdvancedInventoryHostDetail';
import mockHost from '../shared/data.host.json';

jest.mock('../../../api');

describe('<AdvancedInventoryHostDetail />', () => {
  let wrapper;

  beforeAll(() => {
    wrapper = mountWithContexts(
      <AdvancedInventoryHostDetail host={mockHost} />
    );
  });

  test('should render Details', () => {
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    assertDetail('Name', 'localhost');
    assertDetail('Description', 'localhost description');
    assertDetail('Inventory', 'Mikes Inventory');
    assertDetail('Enabled', 'On');
    assertDetail('Created', '2019-10-28, 21:26:54');
    assertDetail('Last modified', '2019-10-29, 20:18:41');
    expect(wrapper.find('Detail[label="Activity"] Sparkline')).toHaveLength(1);
    expect(wrapper.find('VariablesDetail')).toHaveLength(1);
  });

  test('should not load Activity', () => {
    wrapper = mountWithContexts(
      <AdvancedInventoryHostDetail
        host={{
          ...mockHost,
          summary_fields: {
            recent_jobs: [],
            inventory: { kind: 'constructed', id: 2 },
          },
        }}
      />
    );
    const activity_detail = wrapper.find(`Detail[label="Activity"]`).at(0);
    expect(activity_detail.prop('isEmpty')).toEqual(true);
  });
});
