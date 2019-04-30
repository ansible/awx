import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import Organization from '../../../../../src/pages/Organizations/screens/Organization/Organization';

describe.only('<Organization />', () => {
  const me = {
    is_super_user: true,
    is_system_auditor: false
  };

  test('initially renders succesfully', () => {
    mountWithContexts(<Organization me={me} />);
  });

  test('notifications tab shown/hidden based on permissions', () => {
    const wrapper = mountWithContexts(<Organization me={me} />);
    expect(wrapper.find('.pf-c-tabs__item').length).toBe(3);
    expect(wrapper.find('.pf-c-tabs__button[children="Notifications"]').length).toBe(0);
    wrapper.find('Organization').setState({
      isNotifAdmin: true
    });
    expect(wrapper.find('.pf-c-tabs__item').length).toBe(4);
    expect(wrapper.find('button.pf-c-tabs__button[children="Notifications"]').length).toBe(1);
  });
});
