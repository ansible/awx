import yaml from 'js-yaml';

export default function mergeExtraVars(extraVars = '', survey = {}) {
  let vars = {};
  if (typeof extraVars === 'string') {
    vars = yaml.load(extraVars);
  } else if (typeof extraVars === 'object') {
    vars = extraVars;
  }
  return {
    ...vars,
    ...survey,
  };
}

export function maskPasswords(vars, passwordKeys) {
  const updated = { ...vars };
  passwordKeys.forEach((key) => {
    if (typeof updated[key] !== 'undefined') {
      updated[key] = '········';
    }
  });
  return updated;
}
