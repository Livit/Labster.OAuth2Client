"""
Utils for django models.
"""


def help_text(field_name, model_type):
    """
    Get help text from the model field.

    Args:
        field_name (str):
        model_type (type):

    Returns:
        str: help_text defined on the model
    """
    # noinspection PyUnresolvedReferences,PyProtectedMember
    return model_type._meta.get_field(field_name).help_text
