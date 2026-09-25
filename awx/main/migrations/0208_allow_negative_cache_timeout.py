import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0207_alter_skip_tags_to_textfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorysource',
            name='update_cache_timeout',
            field=models.IntegerField(
                default=0,
                help_text='Time in seconds to cache inventory sync. Set to -1 to force update on every launch.',
                validators=[django.core.validators.MinValueValidator(-1)],
            ),
        ),
    ]