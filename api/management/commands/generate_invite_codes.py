"""
Management command to generate invitation codes for existing couples
"""
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from api.models import Couple


class Command(BaseCommand):
    help = 'Generate invitation codes for couples that don\'t have one'

    def handle(self, *args, **options):
        couples_without_code = Couple.objects.filter(invite_code__isnull=True) | Couple.objects.filter(invite_code='')
        
        if not couples_without_code.exists():
            self.stdout.write(self.style.SUCCESS('All couples already have invitation codes!'))
            return
        
        count = 0
        for couple in couples_without_code:
            couple.invite_code = get_random_string(6).upper()
            couple.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Generated code {couple.invite_code} for couple {couple.id} ({couple.partner_1.username})'
                )
            )
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully generated codes for {count} couple(s)!')
        )
