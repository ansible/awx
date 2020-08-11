import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import AzureADDetail from './AzureADDetail';

describe('<AzureADDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<AzureADDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('AzureADDetail').length).toBe(1);
  });
});
