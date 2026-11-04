from django.core.exceptions import ValidationError


def validate_file_size(file):
    """Reject uploads larger than 2 MB."""
    limit_mb = 2
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError(f"File too large. Maximum size is {limit_mb} MB.")
