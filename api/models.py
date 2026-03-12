from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non-binary', 'Non-Binary'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    RELATIONSHIP_CHOICES = [
        ('single', 'Single'),
        ('dating', 'Dating'),
        ('engaged', 'Engaged'),
        ('married', 'Married'),
        ('complicated', 'It\'s Complicated'),
    ]

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    relationship_status = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    anniversary_date = models.DateField(blank=True, null=True)
    
    # Email Verification
    email_verified = models.BooleanField(default=False)

    
    current_mood = models.CharField(max_length=20, blank=True, null=True)
    mood_updated_at = models.DateTimeField(auto_now=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Super Admin Analytics Fields
    last_seen = models.DateTimeField(null=True, blank=True)
    total_active_seconds = models.PositiveIntegerField(default=0)

class Couple(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Using OneToOne to ensure a user is only in ONE couple at a time for simplicity
    partner_1 = models.OneToOneField(User, related_name='couple_as_p1', on_delete=models.CASCADE)
    partner_2 = models.OneToOneField(User, related_name='couple_as_p2', on_delete=models.CASCADE, null=True, blank=True)
    invite_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    anniversary_start = models.DateTimeField(null=True, blank=True)
    theme_color = models.CharField(max_length=50, default='rose') # e.g. 'rose', 'blue', 'amber', 'emerald'
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Deletion Request Fields
    is_deletion_pending = models.BooleanField(default=False)
    deletion_requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deletion_requests')
    deletion_requested_at = models.DateTimeField(null=True, blank=True)
    
    # Super Admin Control Fields
    is_blocked = models.BooleanField(default=False)

    def get_other_user(self, user):
        if user == self.partner_1:
            return self.partner_2
        return self.partner_1

    def __str__(self):
        return f"Couple: {self.partner_1.username} & {self.partner_2.username if self.partner_2 else 'Pending'}"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions', null=True, blank=True)
    verb = models.CharField(max_length=255)
    target_model = models.CharField(max_length=100, null=True, blank=True)  # e.g., 'Todo', 'Question'
    target_id = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient}: {self.verb}"

class Memory(models.Model):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='memories')
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    image = models.ImageField(upload_to='memories/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ImportantDate(models.Model):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='important_dates')
    title = models.CharField(max_length=200)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']

    def __str__(self):
        return self.title

class Rule(models.Model):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='rules')
    text = models.TextField()
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]

class BucketItem(models.Model):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='bucket_items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    
    CATEGORY_CHOICES = [
        ('travel', 'Travel & Trips'),
        ('adventure', 'Adventure & Outdoor'),
        ('food', 'Dining & Food'),
        ('romance', 'Romantic Dates'),
        ('experience', 'Life Experiences'),
        ('home', 'Home & Living'),
        ('other', 'Something Else'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class LoveNote(models.Model):
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='love_notes')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notes')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note from {self.sender.username}"

# Phase 1: Advanced Features

class LoveLanguage(models.Model):
    """Track each user's love language preferences"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='love_languages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='love_language')
    
    LANGUAGE_CHOICES = [
        ('words', 'Words of Affirmation'),
        ('acts', 'Acts of Service'),
        ('gifts', 'Receiving Gifts'),
        ('quality', 'Quality Time'),
        ('touch', 'Physical Touch'),
    ]
    
    primary_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    secondary_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, blank=True)
    quiz_completed = models.BooleanField(default=False)
    quiz_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['couple', 'user']

    def __str__(self):
        return f"{self.user.username}'s Love Language: {self.get_primary_language_display()}"

class LoveLanguageAction(models.Model):
    """Track love language actions between partners"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='love_actions')
    giver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_love_actions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_love_actions')
    
    LANGUAGE_CHOICES = [
        ('words', 'Words of Affirmation'),
        ('acts', 'Acts of Service'),
        ('gifts', 'Receiving Gifts'),
        ('quality', 'Quality Time'),
        ('touch', 'Physical Touch'),
    ]
    
    language_type = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.giver.username} → {self.receiver.username}: {self.get_language_type_display()}"

class GratitudeEntry(models.Model):
    """Daily gratitude journal entries"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='gratitude_entries')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gratitude_entries')
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Gratitude Entries'

    def __str__(self):
        return f"{self.author.username}'s gratitude on {self.date}"

class DateIdea(models.Model):
    """Date night ideas and planning"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='date_ideas')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_date_ideas')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    CATEGORY_CHOICES = [
        ('romantic', 'Romantic'),
        ('adventure', 'Adventure'),
        ('cozy', 'Cozy Night In'),
        ('budget', 'Budget-Friendly'),
        ('luxury', 'Luxury'),
        ('active', 'Active/Sports'),
        ('cultural', 'Cultural'),
        ('foodie', 'Foodie'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Completion tracking
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    notes = models.TextField(blank=True)  # Post-date notes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

class Question(models.Model):
    """Questions for couples to answer"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='questions')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_questions')
    text = models.CharField(max_length=500)
    
    CATEGORY_CHOICES = [
        ('deep', 'Deep Dive'),
        ('fun', 'Fun & Quirky'),
        ('future', 'Future Plans'),
        ('values', 'Values & Beliefs'),
        ('daily', 'Daily Check-in'),
        ('spicy', 'Intimacy & Romance'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='daily')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.text

class Answer(models.Model):
    """Answers to questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['question', 'author']  # One answer per person per question

    def __str__(self):
        return f"Answer by {self.author.username} to: {self.question.text[:30]}"

class Todo(models.Model):
    """Shared todo items for the couple"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_todos')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_todos')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['is_completed', 'due_date', '-created_at']

    def __str__(self):
        return self.title


# Phase 2: Super Admin Features

class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} - {'Resolved' if self.is_resolved else 'Pending'}"

class AnnouncementPopup(models.Model):
    FREQUENCY_CHOICES = [
        ('once', 'Once per user forever'),
        ('session', 'Once per session (until tab closed)'),
        ('every_time', 'Every time dashboard loads'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    image = models.ImageField(upload_to='popups/', null=True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    display_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='session')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Popup: {self.title} - {'Active' if self.is_active else 'Inactive'}"

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField(default=0)
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Coupon {self.code} (-{self.discount_percentage}%)"
        
    @property
    def is_valid(self):
        from django.utils import timezone
        return self.is_active and self.current_uses < self.max_uses and timezone.now() < self.valid_until

class DailyVisit(models.Model):
    date = models.DateField(unique=True)
    visitor_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Visits on {self.date}: {self.visitor_count}"

class SupportTicket(models.Model):
    TICKET_STATUS = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='support_tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=TICKET_STATUS, default='open')
    admin_reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket {self.id}: {self.subject} ({self.status})"

class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_messages')
    message = models.TextField()
    is_admin_reply = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message on {self.ticket.id} by {self.sender.username}"

class VerificationCode(models.Model):
    PURPOSE_CHOICES = [
        ('register', 'Registration'),
        ('forgot_password', 'Forgot Password'),
        ('space_create', 'Space Creation/Join'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Code for {self.user.username} ({self.purpose})"
        
    @property
    def is_valid(self):
        from django.utils import timezone
        return not self.is_verified and timezone.now() < self.expires_at

class SiteSetting(models.Model):
    """Dynamic configuration for the application (Super Admin controlled).
    There should only ever be one instance of this model.
    """
    smtp_host = models.CharField(max_length=255, default='smtp.gmail.com', help_text="e.g., smtp.gmail.com")
    smtp_port = models.IntegerField(default=587)
    smtp_user = models.EmailField(blank=True, null=True, help_text="e.g., ktyrpro@gmail.com")
    smtp_password = models.CharField(max_length=255, blank=True, null=True, help_text="App Password")
    use_tls = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Global Site Settings"
        
    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

