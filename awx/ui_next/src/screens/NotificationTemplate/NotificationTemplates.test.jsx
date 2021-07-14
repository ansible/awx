import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import NotificationTemplates from './NotificationTemplates';

jest.mock('./NotificationTemplateList', () => {
  const NotificationTemplateList = () => <div />;
  return {
    __esModule: true,
    default: NotificationTemplateList,
  };
});

describe('<NotificationTemplates />', () => {
  test('initially renders without crashing', () => {
    const wrapper = mountWithContexts(<NotificationTemplates />);

    const pageSections = wrapper.find('PageSection');
    expect(pageSections).toHaveLength(1);
    expect(pageSections.first().props().variant).toBe('light');
    expect(wrapper.find('NotificationTemplateList')).toHaveLength(1);
  });
});
