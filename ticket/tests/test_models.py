from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import G, F
from rest_framework.exceptions import ValidationError

from ticket.models import Event, TicketType, Order, CancelledOrder


class TicketTypeTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = G(Event)

    def test_avaialble_tickets(self):
        ticket_type = G(TicketType, name='Test', quantity=5, event=self.event)
        all_tickets = list(ticket_type.tickets.all())

        five_available_tickets = set(ticket_type.available_tickets())

        # book one ticket
        ticket = all_tickets[0]
        ticket.order = G(Order, ticket_type=ticket_type, quantity=1)
        ticket.save()

        four_available_tickets = set(ticket_type.available_tickets())

        self.assertCountEqual(five_available_tickets, all_tickets)
        self.assertCountEqual(four_available_tickets, set(all_tickets) - {ticket})

    def test_save(self):
        """ Verifying that the save method creates Ticket(s) upon TicketType creation """

        ticket_type_1 = G(TicketType, name='Without quantity', event=self.event)
        ticket_type_5 = G(TicketType, name='Test', quantity=5, event=self.event)

        one_ticket = ticket_type_1.tickets.count()
        five_tickets = ticket_type_5.tickets.count()

        self.assertEqual(one_ticket, 1)
        self.assertEqual(five_tickets, 5)


class OrderTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = G(get_user_model())

    def test_book_tickets(self):
        order = G(Order, ticket_type=F(quantity=5), quantity=3)

        pre_booking_ticket_count = order.tickets.count()
        order.book_tickets()
        post_booking_ticket_count = order.tickets.count()

        with self.assertRaisesRegexp(Exception, r'Order already fulfilled'):
            order.book_tickets()

        self.assertEqual(pre_booking_ticket_count, 0)
        self.assertEqual(post_booking_ticket_count, 3)

    def test_cancel_tickets(self):
        order = G(Order, ticket_type=F(quantity=5), quantity=3)
        order.created_on = timezone.now() - timedelta(days=1)
        order.save()
        order.book_tickets()
        with self.assertRaisesRegexp(ValidationError, 'Booking older than 30 minutes cannot be cancelled'):
            order.cancel(quantity=1, user=self.user)
        order.created_on = timezone.now()
        order.save()
        with self.assertRaisesRegexp(ValidationError, 'Cancel quantity must be 1 or more'):
            order.cancel(quantity=0, user=get_user_model())
        with self.assertRaisesRegexp(ValidationError, 'Cancel quantity cannot be greater than total booked quantity'):
            order.cancel(quantity=20, user=get_user_model())

        order.cancel(quantity=1, user=self.user)
        self.assertEqual(CancelledOrder.objects.filter(order=order).count(), 1)
        # Total: 5, Booked: 3, Cancelled: 1, Remaining: 3
        self.assertEqual(order.ticket_type.available_tickets().count(), 3)
        with self.assertRaisesRegexp(ValidationError, 'Cancel quantity cannot be greater than remaining quantity'):
            order.cancel(quantity=3, user=get_user_model())
