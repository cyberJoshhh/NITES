# Generated by Django 5.2 on 2025-05-05 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('System', '0024_editableevaluationtable_evaluator_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='editableevaluationtable',
            name='evaluator_type',
            field=models.CharField(choices=[('TEACHER', 'Teacher'), ('PARENT', 'Parent')], max_length=10),
        ),
    ]
