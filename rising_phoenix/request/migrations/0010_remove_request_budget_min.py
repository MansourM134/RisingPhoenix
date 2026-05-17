from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('request', '0009_alter_airefinelog_id_alter_request_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='request',
            name='budget_min',
        ),
    ]
