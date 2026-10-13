from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0002_filterrule_messageattachment_reconcilecursor_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="in_reply_to",
            field=models.CharField(blank=True, db_index=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="message",
            name="references_text",
            field=models.TextField(blank=True, default=""),
        ),
    ]
