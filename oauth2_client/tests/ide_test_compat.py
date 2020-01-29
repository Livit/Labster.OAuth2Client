"""
Local imports of model-related files are required for in-IDE test runs.
Otherwise a model import is attempted before django.setup() call and
an exception is thrown. This is a (hopefully) temporary fix.
"""

