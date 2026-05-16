from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_customuser_avatar'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='customuser',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(('is_superuser', True))
                    | (
                        models.Q(('is_landlord', True), ('is_renter', False))
                        | models.Q(('is_landlord', False), ('is_renter', True))
                    )
                ),
                name='users_regular_user_has_exactly_one_role',
                violation_error_message='You must choose exactly one role: Landlord or Renter.',
            ),
        ),
    ]
