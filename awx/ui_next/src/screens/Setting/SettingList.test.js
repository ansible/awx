import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import SettingList from './SettingList';

describe('<SettingList />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<SettingList />);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.length).toBe(1);
  });
});
