
import requests

import util
import json

{%for model in models%}{%if model.api%}
def list_{{model.name.lower()}}(**kwargs):
    response = util.unpaginate(util.get_url(), '{{model.v2_end_point}}', util.get_verify(), util.get_auth(), kwargs)
    return response

def get_{{model.name.lower()}}({%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}):
    response = requests.get(util.get_url() + "{{model.v2_end_point}}" + str({%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}), verify=util.get_verify(), auth=util.get_auth())
    return response.json()

def create_{{model.name.lower()}}({%for field in model.fields%}{%if not field.pk and field.default is not defined%}{{field.name}},{%endif%}{%endfor%}{%for field in model.fields%}{%if not field.pk and field.default is defined%}{{field.name}}={{field.default}},{%endif%}{%endfor%}):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "{{model.v2_end_point}}", data=json.dumps(dict({%for field in model.fields%}{%if not field.pk%}{{field.name}}={{field.name}},
                                                                                   {%endif%}{%endfor%})),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()

def update_{{model.name.lower()}}({%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}, {%for field in model.fields%}{%if not field.pk%}{{field.name}}=None,{%endif%}{%endfor%}):
    headers = {'content-type': 'application/json'}
    data=dict({%for field in model.fields%}{%if not field.pk%}{{field.name}}={{field.name}},
              {%endif%}{%endfor%})
    data={x:y for x,y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "{{model.v2_end_point}}" + str({%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_{{model.name.lower()}}({%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}):
    response = requests.delete(util.get_url() + "{{model.v2_end_point}}" + str({%for field in model.fields%}{%if field.pk%}{{field.name}}{%endif%}{%endfor%}), verify=util.get_verify(), auth=util.get_auth())
    return response

{%endif%}{%endfor%}
