import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import SAMLDetail from './SAMLDetail';

describe('<SAMLDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<SAMLDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('SAMLDetail').length).toBe(1);
  });
});
