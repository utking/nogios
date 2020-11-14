import sys
from django.core.management.base import BaseCommand
from apps.commands.views import reload_commands
from apps.time_periods.views import reload_time_periods
from apps.services.views import reload_services
from apps.hosts.views import reload_hosts
from apps.contacts.views import reload_contacts
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Verify/reload config files'

    def __init__(self):
        super().__init__()
        self.save = False

    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true', help='Save after verified')

    def handle(self, *args, **options):
        if options['save']:
            cache.clear()
            self.save = True
            print('Configuration will be saved after verified')
        try:
            commands = reload_commands(save=self.save)
            time_periods = reload_time_periods(save=self.save)
            users, groups = reload_contacts(save=self.save)
            reload_services(users=users, groups=groups, cmds=commands, time_periods=time_periods, save=self.save)
            reload_hosts(users=users, groups=groups, time_periods=time_periods, save=self.save)
            self.stdout.write(self.style.SUCCESS('No errors'))
        except Exception as e:
            self.stderr.write(self.style.ERROR('Error'))
            print(e)
            sys.exit(1)
