from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import AIGeneratorService

class DatePlannerView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        location = data.get('location')
        budget = data.get('budget', '$$')
        vibe = data.get('vibe', 'Romantic')
        preferences = data.get('preferences', '')
        
        if not location:
            return Response({"error": "Location is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            ideas = AIGeneratorService.generate_date_ideas(
                location=location,
                budget=budget,
                vibe=vibe,
                preferences=preferences
            )
            return Response({"ideas": ideas}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RelationshipCoachView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        history = data.get('history', [])
        new_message = data.get('message')
        
        if not new_message:
            return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user
        couple = getattr(user, 'couple_as_p1', None) or getattr(user, 'couple_as_p2', None)
        
        # Build Context for the AI
        context_parts = [
            f"User Name: {user.first_name or user.username}",
            f"User Current Mood: {user.current_mood or 'Not set'}",
        ]
        
        if couple:
            partner = couple.get_other_user(user)
            if partner:
                context_parts.append(f"Partner Name: {partner.first_name or partner.username}")
                context_parts.append(f"Partner Current Mood: {partner.current_mood or 'Not set'}")
            
            # Fetch Space Data
            from api.models import Todo, ImportantDate, Rule, BucketItem
            
            # 1. Pending Todos
            todos = Todo.objects.filter(couple=couple, is_completed=False)[:5]
            if todos.exists():
                todo_list = ", ".join([t.title for t in todos])
                context_parts.append(f"Pending Shared Todos: {todo_list}")
            
            # 2. Upcoming Dates
            from django.utils import timezone
            dates = ImportantDate.objects.filter(couple=couple, date__gte=timezone.now().date()).order_by('date')[:3]
            if dates.exists():
                date_list = ", ".join([f"{d.title} on {d.date}" for d in dates])
                context_parts.append(f"Upcoming Special Occasions: {date_list}")
                
            # 3. Relationship Rules
            rules = Rule.objects.filter(couple=couple)[:3]
            if rules.exists():
                rule_list = " | ".join([r.text for r in rules])
                context_parts.append(f"Shared Relationship Rules: {rule_list}")
                
            # 4. Bucket List items
            bucket_items = BucketItem.objects.filter(couple=couple, is_completed=False)[:3]
            if bucket_items.exists():
                bucket_list = ", ".join([b.title for b in bucket_items])
                context_parts.append(f"Bucket List Goals: {bucket_list}")

        context_str = "\n".join(context_parts)
            
        try:
            reply = AIGeneratorService.relationship_coach_chat(
                history=history,
                new_message=new_message,
                context=context_str
            )
            return Response({"reply": reply}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GenerateMemoryCaptionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        image_file = request.FILES.get('image')
        
        if not image_file:
            return Response({"error": "Image file is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            result = AIGeneratorService.generate_memory_caption(image_data=image_file)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GiftGeneratorView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        data = request.data
        gender = data.get('gender', 'Partner')
        occasion = data.get('occasion', 'Just Because')
        budget = data.get('budget', 'Mid-Range')
        interests = data.get('interests', '')
        extra_info = data.get('extra_info', '')
        
        if not interests:
            return Response({"error": "Interests are required for better suggestions."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            ideas = AIGeneratorService.generate_gift_ideas(
                gender=gender,
                occasion=occasion,
                budget=budget,
                interests=interests,
                extra_info=extra_info
            )
            return Response({"ideas": ideas}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
