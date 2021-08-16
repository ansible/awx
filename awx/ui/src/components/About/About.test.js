import React from 'react';
import { shallow } from 'enzyme';
import About from './About';

jest.mock('../../hooks/useBrandName', () => ({
  __esModule: true,
  default: () => ({
    current: 'AWX',
  }),
}));

describe('<About />', () => {
  test('should render AboutModal', () => {
    const onClose = jest.fn();
    const wrapper = shallow(<About isOpen onClose={onClose} />);

    const modal = wrapper.find('AboutModal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('onClose')).toEqual(onClose);
    expect(modal.prop('productName')).toEqual({ current: 'AWX' });
    expect(modal.prop('isOpen')).toEqual(true);
  });
});
