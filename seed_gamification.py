import os
import sys
import django

# Add Super Admin folder to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Super Admin'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lovenest_backend.settings')
django.setup()

from gamification.models import QuizQuestion, Badge

def seed_data():
    # Quiz Questions
    questions = [
        ("What is your partner's favorite comfort food?", "Daily"),
        ("Where would your partner go on a dream vacation?", "Future"),
        ("What was your partner's first impression of you?", "Memories"),
        ("What is one thing that always makes your partner laugh?", "Personality"),
        ("What is your partner's top love language?", "Romance"),
        ("If your partner could have any superpower, what would it be?", "Fun"),
        ("What is your partner's biggest pet peeve?", "Personality"),
        ("What is the most romantic thing you've done together?", "Romance"),
        ("What is a financial goal your partner is currently working towards?", "Finance"),
        ("If your partner could master any new skill instantly, what would it be?", "Future"),
        ("What is a small, everyday habit your partner does that you love?", "Daily"),
        ("How does your partner prefer to decompress after a long, stressful day?", "Personality"),
        ("What was the exact moment you knew you were falling for your partner?", "Memories"),
        ("What is your partner's favorite way to show they care without using words?", "Romance"),
        ("If you had to describe your relationship using a movie title, what would it be?", "Fun"),
        ("What is a career milestone your partner hopes to hit in the next 5 years?", "Future"),
        ("What is your partner's most cherished childhood memory?", "Memories"),
        ("If your partner were to give a TED talk, what topic would it be on?", "Fun"),
        ("What makes your partner feel the most safe and secure?", "Romance"),
        ("How does your partner prefer to handle disagreements?", "Personality"),
        ("What is one place your partner has never been to but constantly talks about visiting?", "Future"),
        ("What is a boundary your partner has set that you deeply respect?", "Personality"),
        ("If you had an unexpected day entirely free, how would your partner want to spend it?", "Daily"),
        ("What is one accomplishment that your partner is incredibly proud of?", "Memories"),
        ("How does your partner prefer to celebrate a big win or success?", "Fun"),
        ("What is the most thoughtful gift your partner has ever received?", "Gifts"),
        ("What values are most important to your partner in a friendship?", "Personality"),
        ("What is a book or movie that profoundly changed your partner's perspective?", "Memories"),
    ]

    for text, cat in questions:
        QuizQuestion.objects.get_or_create(text=text, category=cat)

    # Badges
    badges = [
        ("Love Spark", "Logged memories 3 days in a row!", "Zap", "streak", 3),
        ("Steady Flame", "30 day login streak! Wow!", "Flame", "streak", 30),
        ("Memory Keepers", "Uploaded your first 10 memories.", "Camera", "milestone", 10),
        ("Golden Couple", "Celebrating 1 year together on LoveNest!", "Trophy", "milestone", 365),
        ("Quiz Masters", "Completed 10 daily quizzes together.", "Gamepad2", "engagement", 10),
    ]

    for name, desc, icon, btype, req in badges:
        Badge.objects.get_or_create(
            name=name, 
            description=desc, 
            icon_name=icon, 
            badge_type=btype, 
            requirement_value=req
        )

    print("Successfully seeded gamification data!")

if __name__ == "__main__":
    seed_data()
