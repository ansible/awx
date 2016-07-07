POST requests to this resource should include the full specification for a Job Template Survey

Here is an example survey specification:

    {
        "name": "Simple Surveny",
        "description": "Description of the simple survey",
        "spec": [
            {
        	"type": "text",
        	"question_name": "example question",
        	"question_description": "What is your favorite color?",
        	"variable": "favorite_color",
        	"required": false,
        	"default": "blue"
            }
        ]
    }

`name` and `description` are required elements at the beginning of the survey specification. `spec` must be a
list of survey items.

Within each survey item `type` must be one of:

* text: For survey questions expecting a textual answer
* integer: For survey questions expecting a whole number answer
* float: For survey questions expecting a decimal number
* multiplechoice: For survey questions where one option from a list is required
* multiselect: For survey questions where multiple items from a presented list can be selected

Each item must contain a `question_name` and `question_description` field that describes the survey question itself.
The `variable` elements of each survey items represents the key that will be given to the playbook when the job template
is launched.  It will contain the value as a result of the survey.

Here is a more comprehensive example showing the various question types and their acceptable parameters:

    {
        "name": "Simple",
        "description": "Description",
        "spec": [
            {
        	"type": "text",
        	"question_name": "cantbeshort",
        	"question_description": "What is a long answer",
        	"variable": "long_answer",
        	"choices": "",
        	"min": 5,
        	"max": "",
        	"required": false,
        	"default": "yes"
            },
            {
        	"type": "text",
        	"question_name": "cantbelong",
        	"question_description": "What is a short answer",
        	"variable": "short_answer",
        	"choices": "",
        	"min": "",
        	"max": 5,
        	"required": false,
        	"default": "yes"
            },
            {
        	"type": "text",
        	"question_name": "reqd",
        	"question_description": "I should be required",
        	"variable": "reqd_answer",
        	"choices": "",
        	"min": "",
        	"max": "",
        	"required": true,
        	"default": "yes"
            },
            {
        	"type": "multiplechoice",
        	"question_name": "achoice",
        	"question_description": "Need one of these",
        	"variable": "single_choice",
        	"choices": ["one", "two"],
        	"min": "",
        	"max": "",
        	"required": false,
        	"default": "yes"
            },
            {
        	"type": "multiselect",
        	"question_name": "mchoice",
        	"question_description": "Can have multiples of these",
        	"variable": "multi_choice",
        	"choices": ["one", "two", "three"],
        	"min": "",
        	"max": "",
        	"required": false,
        	"default": "yes"
            },
            {
                "type": "integer",
                "question_name": "integerchoice",
                "question_description": "I need an int here",
                "variable": "int_answer",
                "choices": "",
                "min": 1,
                "max": 5,
                "required": false,
                "default": ""
            },
            {
                "type": "float",
                "question_name": "float",
                "question_description": "I need a float here",
                "variable": "float_answer",
                "choices": "",
                "min": 2,
                "max": 5,
                "required": false,
                "default": ""
            }
        ]
    }