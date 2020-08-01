import yaml from 'js-yaml';

export default function mergeExtraVars(extraVars = '', survey = {}) {
  const vars = yaml.safeLoad(extraVars) || {};
  return {
    ...vars,
    ...survey,
  };
}

export function maskPasswords(vars, passwordKeys) {
  const updated = { ...vars };
  passwordKeys.forEach(key => {
    if (typeof updated[key] !== 'undefined') {
      updated[key] = '········';
    }
  });
  return updated;
}
