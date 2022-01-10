from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError


class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    @property
    def booked_quantity(self):
        """
        Returns total no. of tickets booked for the event.
        """
        t = Order.objects.filter(ticket_type__event=self).aggregate(booked_quantity=Sum('quantity'))['booked_quantity']
        return t if t else 0

    @property
    def cancelled_quantity(self):
        """
        Returns total no. of cancelled tickets for the event.
        """
        t = CancelledOrder.objects.filter(order__ticket_type__event=self).aggregate(cancelled_quantity=Sum('quantity'))[
            'cancelled_quantity']
        return t if t else 0

    def summary(self):
        """
        Returns summary data for the event.
        """
        date_with_max_cancellations = None
        try:
            cancellation_rate = round(self.cancelled_quantity / self.booked_quantity * 100, 2)
        except ZeroDivisionError as e:
            cancellation_rate = 0
            pass

        cancellations = list(
            CancelledOrder.objects.filter(order__ticket_type__event=self).values('created_on__date').annotate(
                count=Sum('quantity')).order_by('count'))
        if cancellations:
            date_with_max_cancellations = cancellations[-1].get('created_on__date')

        return {
            'total_orders': Order.objects.filter(ticket_type__event=self).count(),
            'total_booked_quantity': self.booked_quantity,
            'total_cancelled_quantity': self.cancelled_quantity,
            'cancellation_rate': cancellation_rate,
            'date_with_max_cancellations': date_with_max_cancellations
        }


class TicketType(models.Model):
    name = models.CharField(max_length=255)
    event = models.ForeignKey(Event, related_name='ticket_types', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, editable=False)

    quantity.help_text = 'The number of actual tickets available upon creation'

    def available_tickets(self):
        return self.tickets.filter(order__isnull=True)

    def save(self, *args, **kwargs):
        new = not self.pk
        super().save(*args, **kwargs)
        if new:
            self.tickets.bulk_create([Ticket(ticket_type=self)] * self.quantity)


class Ticket(models.Model):
    ticket_type = models.ForeignKey(TicketType, related_name='tickets', on_delete=models.CASCADE)
    order = models.ForeignKey('ticket.Order', related_name='tickets', default=None, null=True,
                              on_delete=models.SET_NULL)


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.PROTECT)
    ticket_type = models.ForeignKey(TicketType, related_name='orders', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    fulfilled = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True)

    def book_tickets(self):
        if self.fulfilled:
            raise Exception('Order already fulfilled')
        qs = self.ticket_type.available_tickets().select_for_update(skip_locked=True)[:self.quantity]
        try:
            with transaction.atomic():
                updated_count = self.ticket_type.tickets.filter(id__in=qs).update(order=self)
                if updated_count != self.quantity:
                    raise Exception
        except Exception:
            return
        self.fulfilled = True
        self.save(update_fields=['fulfilled'])

    def cancel(self, quantity, user):
        if self.created_on < (timezone.now() - timedelta(minutes=30)):
            raise ValidationError('Booking older than 30 minutes cannot be cancelled')
        if quantity <= 0:
            raise ValidationError('Cancel quantity must be 1 or more')
        if quantity > self.quantity:
            raise ValidationError('Cancel quantity cannot be greater than total booked quantity')
        if quantity > (self.quantity - self.cancelled_quantity):
            raise ValidationError('Cancel quantity cannot be greater than remaining quantity')
        with transaction.atomic():
            CancelledOrder.objects.create(order=self, quantity=quantity, user=user)
            tickets = self.ticket_type.tickets.filter(order=self)[:quantity]
            self.ticket_type.tickets.filter(id__in=tickets).update(order=None)

    @property
    def is_cancelled(self):
        return self.cancellations.count() > 0

    @property
    def cancelled_quantity(self):
        if self.is_cancelled:
            return self.cancellations.aggregate(cancelled_quantity=Sum('quantity'))['cancelled_quantity']
        else:
            return 0


class CancelledOrder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='cancellations', on_delete=models.PROTECT)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='cancellations')
    quantity = models.PositiveIntegerField()
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True)
