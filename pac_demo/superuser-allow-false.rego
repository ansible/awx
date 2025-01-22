package job_template

import rego.v1

violations contains msg if {
	input.created_by.is_superuser == true
    msg := "SuperUser is not allow to launch jobs"
}

response := {
    "allowed": count(violations) == 0,
    "violations": violations
}
