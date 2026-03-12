from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from api.models import Couple
from .models import QuizQuestion, QuizAnswer, Badge, CoupleBadge, Streak
from .serializers import QuizQuestionSerializer, QuizAnswerSerializer, BadgeSerializer, CoupleBadgeSerializer, StreakSerializer
from .streak_service import StreakService
import random

class DailyQuizView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        couple = request.user.couple_as_p1 if hasattr(request.user, 'couple_as_p1') else getattr(request.user, 'couple_as_p2', None)
        if not couple:
            return Response({"error": "No couple found"}, status=status.HTTP_404_NOT_FOUND)

        from django.utils import timezone
        today = timezone.now().date()
        
        # Check if I have answered today
        my_answer_today = QuizAnswer.objects.filter(couple=couple, user=request.user, answered_at__date=today).first()
        
        if my_answer_today:
            partner_answer = QuizAnswer.objects.filter(couple=couple, question=my_answer_today.question).exclude(user=request.user).first()
            if partner_answer:
                return Response({
                    "status": "completed",
                    "question": QuizQuestionSerializer(my_answer_today.question).data,
                    "my_answer": my_answer_today.my_own_answer,
                    "my_guess": my_answer_today.guess_partner_answer,
                    "partner_answer": partner_answer.my_own_answer,
                    "partner_guess": partner_answer.guess_partner_answer,
                    "partner_name": partner_answer.user.username,
                })
            else:
                return Response({
                    "status": "waiting",
                    "question": QuizQuestionSerializer(my_answer_today.question).data,
                    "message": "Waiting for your partner to answer..."
                })

        # I haven't answered today. Did my partner answer today?
        partner_answer_today = QuizAnswer.objects.filter(couple=couple, answered_at__date=today).exclude(user=request.user).first()
        
        if partner_answer_today:
            question = partner_answer_today.question
        else:
            # Pick a question neither has answered ever
            answered_questions = QuizAnswer.objects.filter(couple=couple).values_list('question_id', flat=True)
            question = QuizQuestion.objects.filter(is_active=True).exclude(id__in=answered_questions).first()

            if not question:
                return Response({"status": "no_more_questions", "message": "You've answered all our questions! Come back later."}, status=status.HTTP_200_OK)

        return Response({
            "status": "pending",
            "question": QuizQuestionSerializer(question).data,
            "partner_answered": bool(partner_answer_today)
        })

    def post(self, request):
        couple = request.user.couple_as_p1 if hasattr(request.user, 'couple_as_p1') else getattr(request.user, 'couple_as_p2', None)
        if not couple:
            return Response({"error": "No couple found"}, status=status.HTTP_404_NOT_FOUND)

        question_id = request.data.get('question_id')
        my_answer = request.data.get('my_own_answer')
        guess = request.data.get('guess_partner_answer')

        if not all([question_id, my_answer, guess]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        question = get_object_or_404(QuizQuestion, id=question_id)
        
        answer, created = QuizAnswer.objects.update_or_create(
            question=question,
            couple=couple,
            user=request.user,
            defaults={
                'my_own_answer': my_answer,
                'guess_partner_answer': guess
            }
        )

        # Update streak on interaction
        StreakService.update_interaction(couple)

        return Response({"message": "Answer submitted! Streak updated! ✨"}, status=status.HTTP_201_CREATED)

class GamificationStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        couple = request.user.couple_as_p1 if hasattr(request.user, 'couple_as_p1') else getattr(request.user, 'couple_as_p2', None)
        if not couple:
            return Response({"error": "No couple found"}, status=status.HTTP_404_NOT_FOUND)

        streak, _ = Streak.objects.get_or_create(couple=couple)
        badges = CoupleBadge.objects.filter(couple=couple)
        
        return Response({
            "streak": StreakSerializer(streak).data,
            "badges": CoupleBadgeSerializer(badges, many=True).data
        })
