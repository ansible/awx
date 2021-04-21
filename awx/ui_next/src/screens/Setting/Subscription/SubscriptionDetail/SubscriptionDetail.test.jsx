import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import SubscriptionDetail from './SubscriptionDetail';

const config = {
  me: {
    is_superuser: false,
  },
  version: '1.2.3',
  license_info: {
    compliant: true,
    current_instances: 1,
    date_expired: false,
    date_warning: true,
    free_instances: 1000,
    grace_period_remaining: 2904229,
    instance_count: 1001,
    license_date: '1614401999',
    license_type: 'enterprise',
    pool_id: '123',
    product_name: 'Red Hat Ansible Automation, Standard (5000 Managed Nodes)',
    satellite: false,
    sku: 'ABC',
    subscription_name:
      'Red Hat Ansible Automation, Standard (1001 Managed Nodes)',
    support_level: null,
    time_remaining: 312229,
    trial: false,
    valid_key: true,
  },
};

describe('<SubscriptionDetail />', () => {
  let wrapper;

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(<SubscriptionDetail />, {
        context: { config },
      });
    });
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('SubscriptionDetail').length).toBe(1);
  });

  test('should render expected details', () => {
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }
    assertDetail('Status', 'Compliant');
    assertDetail('Version', '1.2.3');
    assertDetail('Subscription type', 'enterprise');
    assertDetail(
      'Subscription',
      'Red Hat Ansible Automation, Standard (1001 Managed Nodes)'
    );
    assertDetail('Trial', 'False');
    assertDetail('Expires on', '2/27/2021, 4:59:59 AM');
    assertDetail('Days remaining', '3');
    assertDetail('Hosts used', '1');
    assertDetail('Hosts remaining', '1000');

    expect(wrapper.find('Button[aria-label="edit"]').length).toBe(1);
  });
});
