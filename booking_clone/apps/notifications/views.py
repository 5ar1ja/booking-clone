# Python modules
import asyncio
import logging
from typing import AsyncGenerator

# Django modules
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse

# Third-party modules
from asgiref.sync import sync_to_async
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

# Project modules
from .models import Notification
from .serializers import NotificationSerializer
from .utils import format_sse_event, get_user_from_jwt


logger = logging.getLogger('apps.notifications')

SSE_POLL_INTERVAL_SECONDS = 1


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    '''Lists authenticated user notifications and allows marking them as read.'''

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self) -> QuerySet[Notification]:
        return Notification.objects.filter(user=self.request.user).select_related('booking')

    @action(methods=['patch'], detail=True, url_path='mark-read')
    def mark_read(self, request: Request, pk: int | None = None) -> Response:
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        return Response(self.get_serializer(notification).data, status=status.HTTP_200_OK)

    @action(methods=['patch'], detail=False, url_path='mark-all-read')
    def mark_all_read(self, request: Request) -> Response:
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'updated': updated}, status=status.HTTP_200_OK)


def _extract_token(request: HttpRequest) -> str | None:
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ', 1)[1]
    return request.GET.get('token')


def _parse_last_event_id(request: HttpRequest) -> int:
    raw_value = request.headers.get('Last-Event-ID') or request.GET.get('last_event_id')
    if not raw_value:
        return 0
    try:
        return max(int(raw_value), 0)
    except (TypeError, ValueError):
        return 0


def _get_notifications_for_user(user_id: int, *, after_id: int) -> list[Notification]:
    return list(
        Notification.objects.filter(user_id=user_id, id__gt=after_id)
        .select_related('booking')
        .order_by('id')
    )


async def notification_event_generator(
    user_id: int,
    *,
    last_event_id: int = 0,
) -> AsyncGenerator[str, None]:
    '''Replays missed notifications and keeps polling for new ones.'''

    current_event_id = last_event_id
    logger.info('User %s subscribed to SSE stream from event %s.', user_id, last_event_id)
    yield 'event: connected\ndata: {"info":"Connected to notification stream"}\n\n'

    while True:
        notifications = await sync_to_async(_get_notifications_for_user)(
            user_id,
            after_id=current_event_id,
        )
        if notifications:
            for notification in notifications:
                current_event_id = notification.id
                yield format_sse_event(notification)
            continue

        yield ': ping\n\n'
        await asyncio.sleep(SSE_POLL_INTERVAL_SECONDS)

async def stream_notifications(request: HttpRequest) -> HttpResponse | StreamingHttpResponse:
    '''
    Async SSE endpoint with JWT auth and replay support via Last-Event-ID.
    '''
    token = _extract_token(request)
    if not token:
        return HttpResponse('Unauthorized', status=401)

    user = await sync_to_async(get_user_from_jwt)(token)
    if not user:
        return HttpResponse('Invalid Token', status=401)

    last_event_id = _parse_last_event_id(request)
    response = StreamingHttpResponse(
        notification_event_generator(user.id, last_event_id=last_event_id),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Connection'] = 'keep-alive'
    return response
