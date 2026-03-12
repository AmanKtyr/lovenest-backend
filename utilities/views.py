from rest_framework import viewsets, permissions
from .models import GiftIdea, Expense
from .serializers import GiftIdeaSerializer, ExpenseSerializer
from api.models import Couple

def get_couple(user):
    """Safely get the couple for a user."""
    couple = Couple.objects.filter(partner_1=user).first() or \
             Couple.objects.filter(partner_2=user).first()
    return couple

class GiftIdeaViewSet(viewsets.ModelViewSet):
    serializer_class = GiftIdeaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # IMPORTANT: Only return gifts created by the current user to keep them SECRET
        return GiftIdea.objects.filter(creator=self.request.user)

    def perform_create(self, serializer):
        couple = get_couple(self.request.user)
        serializer.save(creator=self.request.user, couple=couple)

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        couple = get_couple(self.request.user)
        if couple:
            return Expense.objects.filter(couple=couple).order_by('-date')
        return Expense.objects.none()

    def perform_create(self, serializer):
        couple = get_couple(self.request.user)
        serializer.save(payer=self.request.user, couple=couple)
