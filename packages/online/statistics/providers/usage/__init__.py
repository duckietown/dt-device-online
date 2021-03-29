import os
import glob
from typing import List

from .GenericFileUsageProvider import GenericFileUsageProvider


def glob_usage_providers(directory: str, regex: str, key: str) -> List[GenericFileUsageProvider]:
    regex = os.path.join(directory, regex.lstrip('/'))
    files = glob.glob(regex)
    providers = []
    for file in files:
        providers.append(GenericFileUsageProvider(key, file))
    return providers
