import { yamlToJson, jsonToYaml, parseVariableField } from './yaml';

describe('yamlToJson', () => {
  test('should convert to json', () => {
    const yaml = `
---
one: 1
two: two
`;
    expect(yamlToJson(yaml)).toEqual(`{
  "one": 1,
  "two": "two"
}`);
  });

  test('should remove comments', () => {
    const yaml = `
---
one: 1
# comment
two: two
# comment two
`;
    expect(yamlToJson(yaml)).toEqual(`{
  "one": 1,
  "two": "two"
}`);
  });

  test('should convert empty string to {}', () => {
    expect(yamlToJson('')).toEqual('{}');
  });

  test('should convert null to {}', () => {
    expect(yamlToJson(null)).toEqual('{}');
  });

  test('should convert empty yaml to {}', () => {
    expect(yamlToJson('---')).toEqual('{}');
  });

  test('should throw if invalid yaml given', () => {
    expect(() => yamlToJson('foo')).toThrow();
  });
});

describe('jsonToYaml', () => {
  test('should convert to yaml', () => {
    const json = `{
  "one": 1,
  "two": "two"
}
`;
    expect(jsonToYaml(json)).toEqual(`one: 1
two: two
`);
  });

  test('should convert empty object to empty yaml doc', () => {
    expect(jsonToYaml('{}')).toEqual('---\n');
  });

  test('should convert empty string to empty yaml doc', () => {
    expect(jsonToYaml('')).toEqual('---\n');
  });

  test('should throw if invalid json given', () => {
    expect(() => jsonToYaml('bad data')).toThrow();
  });
});

describe('parseVariableField', () => {
  const injector = `
  extra_vars:
    password: '{{ password }}'
    username: '{{ username }}'
`;

  const input = `{
  "fields": [
    {
      "id": "username",
      "type": "string",
      "label": "Username"
    },
    {
      "id": "password",
      "type": "string",
      "label": "Password",
      "secret": true
    }
  ]
}`;
  test('should convert empty yaml to an object', () => {
    expect(parseVariableField('---')).toEqual({});
  });

  test('should convert empty json to an object', () => {
    expect(parseVariableField('{}')).toEqual({});
  });

  test('should convert yaml string to json object', () => {
    expect(parseVariableField(injector)).toEqual(
      JSON.parse(yamlToJson(injector))
    );
  });

  test('should convert json string to json object', () => {
    expect(parseVariableField(input)).toEqual(JSON.parse(input));
  });
});
