from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class UserOwnedViewSet(viewsets.ModelViewSet):
    """Base for models owned by current user"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return super().get_queryset().filter(user=self.request.user)
        return super().get_queryset()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
