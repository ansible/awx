import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SmartInventoryHostDetail from './SmartInventoryHostDetail';
import mockHost from '../shared/data.host.json';

jest.mock('../../../api');

describe('<SmartInventoryHostDetail />', () => {
  let wrapper;

  beforeAll(() => {
    wrapper = mountWithContexts(<SmartInventoryHostDetail host={mockHost} />);
  });

  afterAll(() => {
    wrapper.unmount();
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
    assertDetail('Created', '10/28/2019, 9:26:54 PM');
    assertDetail('Last modified', '10/29/2019, 8:18:41 PM');
    expect(wrapper.find('Detail[label="Activity"] Sparkline')).toHaveLength(1);
    expect(wrapper.find('VariablesDetail')).toHaveLength(1);
  });
});
