# Generated by Django 2.2.6 on 2022-01-09 20:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ticket', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='updated_on',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='tickettype',
            name='quantity',
            field=models.PositiveIntegerField(default=1, editable=False, help_text='The number of actual tickets available upon creation'),
        ),
        migrations.CreateModel(
            name='CancelledOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cancellations', to='ticket.Order')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cancellations', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
