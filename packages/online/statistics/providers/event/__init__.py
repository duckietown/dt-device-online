import os
import glob
from typing import List

from .GenericFileEventProvider import GenericFileEventProvider


def glob_event_providers(directory: str, regex: str) -> List[GenericFileEventProvider]:
    regex = os.path.join(directory, regex.lstrip('/'))
    files = glob.glob(regex)
    providers = []
    for file in files:
        providers.append(GenericFileEventProvider(file))
    return providers
