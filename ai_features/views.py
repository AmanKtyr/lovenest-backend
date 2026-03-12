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
            
        try:
            reply = AIGeneratorService.relationship_coach_chat(
                history=history,
                new_message=new_message
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
