from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0204_squashed_deletions'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryHostVariablesWithHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variables', models.JSONField()),
                ('inventory', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='inventory_host_variables',
                    to='main.inventory',
                )),
                ('host', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='inventory_host_variables',
                    to='main.host',
                )),
            ],
        ),
        migrations.AddConstraint(
            model_name='inventoryhostvariableswithhistory',
            constraint=models.UniqueConstraint(
                fields=('inventory', 'host'),
                name='unique_inventory_host',
                violation_error_message='Inventory/Host combination must be unique.',
            ),
        ),
    ]
