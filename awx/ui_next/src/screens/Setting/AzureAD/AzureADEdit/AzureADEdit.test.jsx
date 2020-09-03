import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import AzureADEdit from './AzureADEdit';

describe('<AzureADEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<AzureADEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('AzureADEdit').length).toBe(1);
  });
});
