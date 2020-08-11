import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import ActivityStreamEdit from './ActivityStreamEdit';

describe('<ActivityStreamEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<ActivityStreamEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('ActivityStreamEdit').length).toBe(1);
  });
});
