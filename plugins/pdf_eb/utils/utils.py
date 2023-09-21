from datetime import datetime
from pathlib import Path
from string import Template
from typing import List, Union

import yaml

def read_yaml(yaml_path: Union[str, Path]):
    with open(str(yaml_path), "rb") as f:
        data = yaml.load(f, Loader=yaml.Loader)
    return data

def make_prompt(query: str, context: str = None, custom_prompt: str = None) -> str:
    if not context:
        return query 

    print("custom_prompt = ", custom_prompt)
    if "$query" not in custom_prompt or "$context" not in custom_prompt:
        raise ValueError("prompt中必须含有$query和$context两个值")

    msg_template = Template(custom_prompt)
    message = msg_template.substitute(query=query, context=context)
    return message