def generate_survey_spec(variables=None, default_type='integer', required=True):
    '''
    Returns a valid survey spec for a job template, based on the input
    argument specifying variable name(s)
    '''
    if isinstance(variables, list):
        name = "%s survey" % variables[0]
        description = "A survey that starts with %s." % variables[0]
        vars_list = variables
    else:
        name = "%s survey" % variables
        description = "A survey about %s." % variables
        vars_list = [variables]

    spec = []
    index = 0
    for var in vars_list:
        spec_item = {}
        spec_item['index'] = index
        index += 1
        spec_item['required'] = required
        spec_item['choices'] = ''
        spec_item['type'] = default_type
        if isinstance(var, dict):
            spec_item.update(var)
            var_name = spec_item.get('variable', 'variable')
        else:
            var_name = var
        spec_item.setdefault('variable', var_name)
        spec_item.setdefault('question_name', "Enter a value for %s." % var_name)
        spec_item.setdefault('question_description', "A question about %s." % var_name)
        if spec_item['type'] == 'integer':
            spec_item.setdefault('default', 0)
            spec_item.setdefault('max', spec_item['default'] + 100)
            spec_item.setdefault('min', spec_item['default'] - 100)
        else:
            spec_item.setdefault('default', '')
        spec.append(spec_item)

    survey_spec = {}
    survey_spec['spec'] = spec
    survey_spec['name'] = name
    survey_spec['description'] = description
    return survey_spec
