import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import { HostStatusBar } from '.';

describe('<HostStatusBar />', () => {
  let wrapper;
  const mockCounts = {
    ok: 5,
    skipped: 1,
  };

  beforeEach(() => {
    wrapper = mountWithContexts(<HostStatusBar counts={mockCounts} />);
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.length).toBe(1);
  });

  test('should render five bar segments', () => {
    expect(wrapper.find('BarSegment').length).toBe(5);
  });

  test('tooltips should display host status and count', () => {
    const tooltips = wrapper.find('TooltipContent');
    const expectedContent = [
      { label: 'OK', count: 5 },
      { label: 'Skipped', count: 1 },
      { label: 'Changed', count: 0 },
      { label: 'Failed', count: 0 },
      { label: 'Unreachable', count: 0 },
    ];

    tooltips.forEach((tooltip, index) => {
      expect(tooltip.text()).toEqual(
        `${expectedContent[index].label}${expectedContent[index].count}`
      );
    });
  });

  test('empty host counts should display tooltip and one bar segment', () => {
    wrapper = mountWithContexts(<HostStatusBar />);
    expect(wrapper.find('BarSegment').length).toBe(1);
    expect(wrapper.find('Tooltip').prop('content')).toEqual(
      'Host status information for this job is unavailable.'
    );
  });
});
