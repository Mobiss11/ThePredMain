"""Support ticket endpoints"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from app.core.database import get_db
from app.models.support import SupportTicket, SupportMessage, TicketStatus, TicketPriority
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging
import aiohttp
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


async def send_telegram_notification(telegram_id: int, ticket_id: int, subject: str):
    """Send Telegram notification to user about admin reply"""
    logger.info(f"Attempting to send Telegram notification to user {telegram_id} for ticket {ticket_id}")
    logger.info(f"BOT_TOKEN configured: {bool(settings.BOT_TOKEN)}")
    logger.info(f"WEBAPP_URL: {settings.WEBAPP_URL}")

    if not settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN not configured, skipping Telegram notification")
        return

    try:
        message = f"""
💬 <b>Новый ответ в тикете поддержки</b>

Администратор ответил на ваш тикет <b>#{ticket_id}</b>

📝 Тема: <b>{subject}</b>

Откройте приложение для просмотра ответа 👇
"""

        keyboard = {
            "inline_keyboard": [[
                {
                    "text": "📱 Открыть тикет",
                    "web_app": {"url": f"{settings.WEBAPP_URL}?startapp=support_ticket_{ticket_id}"}
                }
            ]]
        }

        url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info(f"Telegram notification sent to user {telegram_id} for ticket {ticket_id}")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to send Telegram notification: {response.status} - {error_text}")

    except Exception as e:
        logger.error(f"Error sending Telegram notification: {e}")


class CreateTicketRequest(BaseModel):
    subject: str
    message: str
    priority: TicketPriority = TicketPriority.MEDIUM


class SendMessageRequest(BaseModel):
    message: str


class TicketResponse(BaseModel):
    id: int
    subject: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    admin_replied: bool
    unread_count: int = 0
    last_message: Optional[str] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    ticket_id: int
    is_admin: bool
    message: str
    attachment_url: Optional[str]
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/tickets")
async def create_ticket(
    user_id: int = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    priority: str = Form("medium"),
    attachment: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new support ticket"""
    try:
        # Verify user exists
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Upload attachment to S3 if provided
        attachment_url = None
        if attachment:
            from app.core.s3 import s3_client
            attachment_url = await s3_client.upload_file(
                attachment.file.read(),
                f"support/{user_id}/{datetime.now(timezone.utc).timestamp()}_{attachment.filename}",
                attachment.content_type
            )

        # Create ticket
        ticket = SupportTicket(
            user_id=user_id,
            subject=subject,
            priority=TicketPriority(priority),
            status=TicketStatus.OPEN
        )
        db.add(ticket)
        await db.flush()

        # Create first message
        first_message = SupportMessage(
            ticket_id=ticket.id,
            user_id=user_id,
            is_admin=False,
            message=message,
            attachment_url=attachment_url
        )
        db.add(first_message)
        await db.commit()
        await db.refresh(ticket)

        return {
            "success": True,
            "ticket_id": ticket.id,
            "message": "Ticket created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tickets/{user_id}", response_model=List[TicketResponse])
async def get_user_tickets(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get all tickets for a user"""
    result = await db.execute(
        select(SupportTicket)
        .where(SupportTicket.user_id == user_id)
        .order_by(desc(SupportTicket.updated_at))
    )
    tickets = result.scalars().all()

    # Get last message for each ticket
    response = []
    for ticket in tickets:
        result = await db.execute(
            select(SupportMessage)
            .where(SupportMessage.ticket_id == ticket.id)
            .order_by(desc(SupportMessage.created_at))
            .limit(1)
        )
        last_msg = result.scalar_one_or_none()

        response.append(TicketResponse(
            id=ticket.id,
            subject=ticket.subject,
            priority=ticket.priority.value,
            status=ticket.status.value,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            admin_replied=ticket.admin_replied,
            unread_count=0,  # TODO: implement read tracking
            last_message=last_msg.message if last_msg else None
        ))

    return response


@router.get("/tickets/{ticket_id}/messages", response_model=List[MessageResponse])
async def get_ticket_messages(ticket_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    """Get all messages in a ticket"""
    # Verify user owns the ticket or is admin
    result = await db.execute(
        select(SupportTicket).where(
            and_(
                SupportTicket.id == ticket_id,
                SupportTicket.user_id == user_id
            )
        )
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get all messages
    result = await db.execute(
        select(SupportMessage)
        .where(SupportMessage.ticket_id == ticket_id)
        .order_by(SupportMessage.created_at)
    )
    messages = result.scalars().all()

    # Get user names
    response = []
    for msg in messages:
        user_name = None
        if msg.user_id:
            result = await db.execute(select(User).where(User.id == msg.user_id))
            user = result.scalar_one_or_none()
            if user:
                user_name = user.username or user.first_name or f"User #{user.telegram_id}"

        response.append(MessageResponse(
            id=msg.id,
            ticket_id=msg.ticket_id,
            is_admin=msg.is_admin,
            message=msg.message,
            attachment_url=msg.attachment_url,
            created_at=msg.created_at,
            user_name=user_name if not msg.is_admin else "Поддержка"
        ))

    return response


@router.post("/tickets/{ticket_id}/messages")
async def send_message(
    ticket_id: int,
    user_id: int = Form(...),
    message: str = Form(...),
    attachment: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Send a message in a ticket"""
    try:
        # Verify ticket exists and user owns it
        result = await db.execute(
            select(SupportTicket).where(
                and_(
                    SupportTicket.id == ticket_id,
                    SupportTicket.user_id == user_id
                )
            )
        )
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Check if ticket is closed
        if ticket.status == TicketStatus.CLOSED:
            raise HTTPException(status_code=400, detail="Cannot send message to closed ticket")

        # Anti-spam protection
        # 1. If admin hasn't replied yet, user can't send more messages
        if not ticket.admin_replied:
            # Check if user has already sent a message
            result = await db.execute(
                select(func.count(SupportMessage.id))
                .where(
                    and_(
                        SupportMessage.ticket_id == ticket_id,
                        SupportMessage.is_admin == False
                    )
                )
            )
            user_msg_count = result.scalar()
            if user_msg_count > 0:
                raise HTTPException(
                    status_code=429,
                    detail="Please wait for admin response before sending another message"
                )

        # 2. Rate limit: max 1 message per 2 minutes
        result = await db.execute(
            select(SupportMessage)
            .where(
                and_(
                    SupportMessage.ticket_id == ticket_id,
                    SupportMessage.user_id == user_id,
                    SupportMessage.is_admin == False
                )
            )
            .order_by(desc(SupportMessage.created_at))
            .limit(1)
        )
        last_message = result.scalar_one_or_none()

        if last_message:
            time_diff = datetime.now(timezone.utc) - last_message.created_at
            if time_diff < timedelta(minutes=2):
                remaining_seconds = 120 - int(time_diff.total_seconds())
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait {remaining_seconds} seconds before sending another message"
                )

        # Upload attachment if provided
        attachment_url = None
        if attachment:
            from app.core.s3 import s3_client
            attachment_url = await s3_client.upload_file(
                attachment.file.read(),
                f"support/{user_id}/{datetime.now(timezone.utc).timestamp()}_{attachment.filename}",
                attachment.content_type
            )

        # Create message
        new_message = SupportMessage(
            ticket_id=ticket_id,
            user_id=user_id,
            is_admin=False,
            message=message,
            attachment_url=attachment_url
        )
        db.add(new_message)

        # Update ticket
        ticket.updated_at = datetime.now(timezone.utc)
        ticket.status = TicketStatus.IN_PROGRESS

        await db.commit()

        return {
            "success": True,
            "message_id": new_message.id,
            "message": "Message sent successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============ Admin Endpoints ============

@router.get("/admin/tickets", response_model=List[dict])
async def get_all_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """Get all support tickets (admin only)"""
    query = select(SupportTicket)

    if status:
        query = query.where(SupportTicket.status == TicketStatus(status))
    if priority:
        query = query.where(SupportTicket.priority == TicketPriority(priority))

    query = query.order_by(desc(SupportTicket.updated_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    tickets = result.scalars().all()

    # Get user info and message count for each ticket
    response = []
    for ticket in tickets:
        # Get user
        result = await db.execute(select(User).where(User.id == ticket.user_id))
        user = result.scalar_one_or_none()

        # Get message count
        result = await db.execute(
            select(func.count(SupportMessage.id))
            .where(SupportMessage.ticket_id == ticket.id)
        )
        message_count = result.scalar()

        # Get last message
        result = await db.execute(
            select(SupportMessage)
            .where(SupportMessage.ticket_id == ticket.id)
            .order_by(desc(SupportMessage.created_at))
            .limit(1)
        )
        last_msg = result.scalar_one_or_none()

        response.append({
            "id": ticket.id,
            "subject": ticket.subject,
            "priority": ticket.priority.value,
            "status": ticket.status.value,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat(),
            "user_id": ticket.user_id,
            "user_name": user.username or user.first_name if user else "Unknown",
            "message_count": message_count,
            "last_message": last_msg.message if last_msg else None,
            "admin_replied": ticket.admin_replied
        })

    return response


@router.post("/admin/tickets/{ticket_id}/reply")
async def admin_reply(
    ticket_id: int,
    message: str = Form(...),
    attachment: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Admin reply to a ticket"""
    try:
        # Get ticket
        result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Upload attachment if provided
        attachment_url = None
        if attachment:
            from app.core.s3 import s3_client
            attachment_url = await s3_client.upload_file(
                attachment.file.read(),
                f"support/admin/{datetime.now(timezone.utc).timestamp()}_{attachment.filename}",
                attachment.content_type
            )

        # Create admin message
        admin_message = SupportMessage(
            ticket_id=ticket_id,
            user_id=None,  # Admin has no user_id
            is_admin=True,
            message=message,
            attachment_url=attachment_url
        )
        db.add(admin_message)

        # Update ticket
        ticket.updated_at = datetime.now(timezone.utc)
        ticket.admin_replied = True
        ticket.status = TicketStatus.WAITING_USER

        await db.commit()

        # Send Telegram notification to user
        try:
            logger.info(f"Preparing to send Telegram notification for ticket {ticket_id}")
            result = await db.execute(select(User).where(User.id == ticket.user_id))
            user = result.scalar_one_or_none()
            logger.info(f"User found: {bool(user)}, user_id: {ticket.user_id}")
            if user:
                logger.info(f"User telegram_id: {user.telegram_id}")
            if user and user.telegram_id:
                logger.info(f"Calling send_telegram_notification for telegram_id {user.telegram_id}")
                await send_telegram_notification(user.telegram_id, ticket_id, ticket.subject)
            else:
                logger.warning(f"Cannot send notification - user: {bool(user)}, telegram_id: {user.telegram_id if user else None}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}", exc_info=True)
            # Don't fail the request if notification fails

        return {
            "success": True,
            "message_id": admin_message.id,
            "message": "Reply sent successfully"
        }

    except Exception as e:
        logger.error(f"Error sending admin reply: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """Update ticket status (admin only)"""
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = TicketStatus(status)
    ticket.updated_at = datetime.now(timezone.utc)

    if status == "closed":
        ticket.closed_at = datetime.now(timezone.utc)

    await db.commit()

    return {"success": True, "status": status}
