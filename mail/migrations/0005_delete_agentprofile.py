from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0004_workspace"),
    ]

    operations = [
        migrations.DeleteModel(name="AgentProfile"),
    ]
