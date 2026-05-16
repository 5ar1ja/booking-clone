from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(
        _("Created at"),
        auto_now_add=True,
        db_index=True,
        help_text=_("The date and time when the record was created.")
    )
    updated_at = models.DateTimeField(
        _("Updated at"),
        auto_now=True,
        help_text=_("The date and time when the record was last updated.")
    )

    class Meta:
        abstract = True
