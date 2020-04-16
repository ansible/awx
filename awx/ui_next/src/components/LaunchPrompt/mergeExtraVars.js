import yaml from 'js-yaml';

export default function mergeExtraVars(extraVars, survey = {}) {
  const vars = yaml.safeLoad(extraVars) || {};
  return {
    ...vars,
    ...survey,
  };
}

// TODO: "safe" version that obscures passwords for preview step
