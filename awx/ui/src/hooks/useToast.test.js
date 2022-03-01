import React from 'react';
import { act } from 'react-dom/test-utils';
import { shallow, mount } from 'enzyme';
import useToast, { Toast, AlertVariant } from './useToast';

describe('useToast', () => {
  const Child = () => <div />;
  const Test = () => {
    const toastVals = useToast();
    return <Child {...toastVals} />;
  };

  test('should provide Toast component', () => {
    const wrapper = mount(<Test />);

    expect(wrapper.find('Child').prop('Toast')).toEqual(Toast);
  });

  test('should add toast', () => {
    const wrapper = mount(<Test />);

    expect(wrapper.find('Child').prop('toastProps').toasts).toEqual([]);
    act(() => {
      wrapper.find('Child').prop('addToast')({
        message: 'one',
        id: 1,
        variant: 'success',
      });
    });
    wrapper.update();

    expect(wrapper.find('Child').prop('toastProps').toasts).toEqual([
      {
        message: 'one',
        id: 1,
        variant: 'success',
      },
    ]);
  });

  test('should remove toast', () => {
    const wrapper = mount(<Test />);

    act(() => {
      wrapper.find('Child').prop('addToast')({
        message: 'one',
        id: 1,
        variant: 'success',
      });
    });
    wrapper.update();
    expect(wrapper.find('Child').prop('toastProps').toasts).toHaveLength(1);
    act(() => {
      wrapper.find('Child').prop('removeToast')(1);
    });
    wrapper.update();

    expect(wrapper.find('Child').prop('toastProps').toasts).toHaveLength(0);
  });
});

describe('Toast', () => {
  test('should render nothing with no toasts', () => {
    const wrapper = shallow(<Toast toasts={[]} removeToast={() => {}} />);
    expect(wrapper).toEqual({});
  });

  test('should render toast alert', () => {
    const toast = {
      title: 'Inventory saved',
      variant: AlertVariant.success,
      id: 1,
      message: 'the message',
    };
    const wrapper = shallow(<Toast toasts={[toast]} removeToast={() => {}} />);

    const alert = wrapper.find('Alert');
    expect(alert.prop('title')).toEqual('Inventory saved');
    expect(alert.prop('variant')).toEqual('success');
    expect(alert.prop('ouiaId')).toEqual('toast-message-1');
    expect(alert.prop('children')).toEqual('the message');
  });

  test('should call removeToast', () => {
    const removeToast = jest.fn();
    const toast = {
      title: 'Inventory saved',
      variant: AlertVariant.success,
      id: 1,
    };
    const wrapper = shallow(
      <Toast toasts={[toast]} removeToast={removeToast} />
    );

    const alert = wrapper.find('Alert');
    alert.prop('actionClose').props.onClose(1);
    expect(removeToast).toHaveBeenCalledTimes(1);
  });

  test('should render multiple alerts', () => {
    const toasts = [
      {
        title: 'Inventory saved',
        variant: AlertVariant.success,
        id: 1,
        message: 'the message',
      },
      {
        title: 'error saving',
        variant: AlertVariant.danger,
        id: 2,
      },
    ];
    const wrapper = shallow(<Toast toasts={toasts} removeToast={() => {}} />);

    const alert = wrapper.find('Alert');
    expect(alert).toHaveLength(2);

    expect(alert.at(0).prop('title')).toEqual('Inventory saved');
    expect(alert.at(0).prop('variant')).toEqual('success');
    expect(alert.at(1).prop('title')).toEqual('error saving');
    expect(alert.at(1).prop('variant')).toEqual('danger');
  });
});
