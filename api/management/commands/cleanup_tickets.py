from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import SupportTicket

class Command(BaseCommand):
    help = 'Deletes SupportTickets that have been resolved for more than 7 days.'

    def handle(self, *args, **kwargs):
        # Calculate the threshold date: 7 days ago mapping to the user's request
        threshold_date = timezone.now() - timedelta(days=7)
        
        # Find tickets that are resolved and have a resolved_at older than 7 days
        tickets_to_delete = SupportTicket.objects.filter(
            status='resolved',
            resolved_at__lt=threshold_date
        )
        
        count = tickets_to_delete.count()
        if count > 0:
            tickets_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} old resolved tickets.'))
        else:
            self.stdout.write(self.style.SUCCESS('No old resolved tickets to delete.'))
