import yaml from 'js-yaml';

export function yamlToJson(yamlString) {
  const value = yaml.safeLoad(yamlString);
  if (!value) {
    return '{}';
  }
  if (typeof value !== 'object') {
    throw new Error('yaml is not in object format');
  }
  return JSON.stringify(value, null, 2);
}

export function jsonToYaml(jsonString) {
  if (jsonString.trim() === '') {
    return '---\n';
  }
  const value = JSON.parse(jsonString);
  if (Object.entries(value).length === 0) {
    return '---\n';
  }
  return yaml.safeDump(value);
}

export function isJson(jsonString) {
  if (typeof jsonString !== 'string') {
    return false;
  }
  let value;
  try {
    value = JSON.parse(jsonString);
  } catch (e) {
    return false;
  }

  return typeof value === 'object' && value !== null;
}
