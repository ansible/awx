import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import JobsEdit from './JobsEdit';

describe('<JobsEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<JobsEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('JobsEdit').length).toBe(1);
  });
});
