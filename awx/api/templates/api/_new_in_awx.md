{% if not version_label_flag or version_label_flag == 'true' %}
{% if new_in_13 %}> _Added in AWX 1.3_{% endif %}
{% if new_in_14 %}> _Added in AWX 1.4_{% endif %}
{% if new_in_145 %}> _Added in Ansible Tower 1.4.5_{% endif %}
{% if new_in_148 %}> _Added in Ansible Tower 1.4.8_{% endif %}
{% if new_in_200 %}> _Added in Ansible Tower 2.0.0_{% endif %}
{% if new_in_220 %}> _Added in Ansible Tower 2.2.0_{% endif %}
{% if new_in_230 %}> _Added in Ansible Tower 2.3.0_{% endif %}
{% if new_in_240 %}> _Added in Ansible Tower 2.4.0_{% endif %}
{% if new_in_300 %}> _Added in Ansible Tower 3.0.0_{% endif %}
{% if new_in_310 %}> _New in Ansible Tower 3.1.0_{% endif %}
{% if new_in_320 %}> _New in Ansible Tower 3.2.0_{% endif %}
{% endif %}
