from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        # Replace '0125_some_name' with the ACTUAL name of the last file in the folder
        ('main', '0125_some_name'), 
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_reset_required',
            field=models.BooleanField(default=False, help_text='Force the user to reset their password on next login.'),
        ),
    ]