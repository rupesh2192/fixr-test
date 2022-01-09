from rest_framework import serializers

from . import models


class TicketTypeSerializer(serializers.ModelSerializer):
    available_tickets = serializers.SerializerMethodField()

    class Meta:
        model = models.TicketType
        fields = ('id', 'name', 'available_tickets')

    def get_available_tickets(self, instance):
        return instance.available_tickets().count()


class EventSerializer(serializers.ModelSerializer):
    ticket_types = TicketTypeSerializer(many=True)

    class Meta:
        model = models.Event
        fields = ('id', 'name', 'description', 'ticket_types')


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = ('id', 'ticket_type', 'quantity', 'cancelled_quantity')
