import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ConstructedInventoryHosts from './ConstructedInventoryHosts';

describe('<ConstructedInventoryHosts />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<ConstructedInventoryHosts />);
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('ConstructedInventoryHosts').length).toBe(1);
  });
});
