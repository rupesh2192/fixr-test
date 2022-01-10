from rest_framework import mixins, viewsets, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Event, Order
from .serializers import EventSerializer, OrderSerializer


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.prefetch_related('ticket_types')


class OrderViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related("cancellations")

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        order.book_tickets()
        if not order.fulfilled:
            order.delete()
            raise exceptions.ValidationError("Couldn't book tickets")

    @action(methods=["POST"], detail=True)
    def cancel(self, request, **kwargs):
        instance = self.get_object()
        instance.cancel(quantity=int(self.request.data["quantity"]), user=self.request.user)
        instance.refresh_from_db()
        return Response(self.serializer_class(instance).data)
