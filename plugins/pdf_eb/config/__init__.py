import os
from ..utils.utils import read_yaml
config = read_yaml(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./config.yaml"))
