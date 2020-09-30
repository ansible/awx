export function assertDetail(wrapper, label, value) {
  expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
  expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
}

export function assertVariableDetail(wrapper, label, value) {
  expect(
    wrapper.find(`VariablesDetail[label="${label}"] .pf-c-form__label`).text()
  ).toBe(label);
  expect(
    wrapper
      .find(`VariablesDetail[label="${label}"] CodeMirrorInput`)
      .prop('value')
  ).toBe(value);
}
