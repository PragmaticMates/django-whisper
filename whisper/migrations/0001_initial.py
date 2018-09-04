# Generated by Django 2.0.6 on 2018-09-04 11:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'message',
                'verbose_name_plural': 'messages',
                'ordering': ('created',),
                'default_permissions': ('list', 'view', 'add', 'change', 'delete'),
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('slug', models.SlugField(unique=True)),
                ('name', models.CharField(max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'room',
                'verbose_name_plural': 'rooms',
                'ordering': ('-modified',),
                'default_permissions': ('list', 'view', 'add', 'change', 'delete'),
            },
        ),
        migrations.CreateModel(
            name='RoomUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('last_read', models.DateTimeField(blank=True, default=None, null=True)),
                ('last_notified', models.DateTimeField(default=django.utils.timezone.now)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='member_set', related_query_name='member', to='whisper.Room')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='room',
            name='users',
            field=models.ManyToManyField(through='whisper.RoomUser', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='whisper.Room'),
        ),
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
