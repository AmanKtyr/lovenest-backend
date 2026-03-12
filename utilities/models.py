from django.db import models
from api.models import Couple, User

class GiftIdea(models.Model):
    """Secret gift vault for planning surprises"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='gift_ideas')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_gifts')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price_estimate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    url = models.URLField(blank=True)
    
    # Event reminder
    for_event = models.CharField(max_length=100, blank=True, help_text="e.g. Birthday, Anniversary")
    event_date = models.DateField(null=True, blank=True)
    
    is_purchased = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gift for {self.couple}: {self.title}"

class Expense(models.Model):
    """Shared finance/expense splitter"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='expenses')
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_expenses')
    
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    
    CATEGORY_CHOICES = [
        ('dates', 'Date Nights'),
        ('travel', 'Travel & Trips'),
        ('food', 'Groceries & Food'),
        ('bills', 'Shared Bills'),
        ('other', 'Other'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    
    split_type = models.CharField(max_length=20, default='50/50', choices=[
        ('50/50', 'Split 50/50'),
        ('payer_full', 'Payer Paid Full'),
        ('other', 'Custom'),
    ])

    def __str__(self):
        return f"{self.title} - {self.amount}"
