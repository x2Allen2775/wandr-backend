from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from datetime import datetime

from app.database import get_db
from app.utils.jwt import get_current_user
from app.models.user import User, follows
from app.models.message import Conversation, Message
from app.schemas.chat import MessageCreate, MessageResponse, ConversationResponse, InboxResponse
from app.schemas.post import PostAuthorResponse

router = APIRouter(tags=["Chat System"])

@router.post("/send/{receiver_id}", response_model=MessageResponse)
def send_message(
    receiver_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message. Creates a Conversation if none exists.
    If the receiver does not follow the sender natively, the Conversation status will default to 'pending' (Message Request).
    """
    if str(current_user.id) == receiver_id:
        raise HTTPException(status_code=400, detail="Cannot send message to yourself.")
        
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found.")

    # 1. Ensure conversation exists
    conversation = db.query(Conversation).filter(
        or_(
            and_(Conversation.user1_id == current_user.id, Conversation.user2_id == receiver_id),
            and_(Conversation.user1_id == receiver_id, Conversation.user2_id == current_user.id)
        )
    ).first()

    if not conversation:
        # Check if the receiver follows the sender OR sender follows receiver (mutual or one-way acceptance based on business logic)
        # For Instagram style: if the receiver follows the sender, it goes to inbox. Otherwise, Requests.
        # We query the `follows` association table where follower_id is the receiver and following_id is the sender.
        is_receiver_following_sender = db.execute(
            follows.select().where(
                and_(
                    follows.c.follower_id == receiver_id,
                    follows.c.following_id == current_user.id
                )
            )
        ).first()

        initial_status = "accepted" if is_receiver_following_sender else "pending"
        
        conversation = Conversation(
            user1_id=current_user.id,
            user2_id=receiver_id,
            status=initial_status
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Create the new message
    new_message = Message(
        conversation_id=conversation.id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=payload.content,
        iv=payload.iv,
        media_url=payload.media_url
    )
    db.add(new_message)
    
    # Touch conversation updated_at
    conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_message)
    
    return new_message


@router.get("/inbox", response_model=InboxResponse)
def get_inbox(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all active Conversations partitioned into "Inbox" (accepted) and "Requests" (pending sent TO current_user).
    """
    conversations = db.query(Conversation).filter(
        or_(
            Conversation.user1_id == current_user.id,
            Conversation.user2_id == current_user.id
        )
    ).order_by(desc(Conversation.updated_at)).all()

    inbox = []
    requests = []

    for conv in conversations:
        other_user_str = conv.user2_id if str(conv.user1_id) == str(current_user.id) else conv.user1_id
        other_user = db.query(User).filter(User.id == other_user_str).first()
        
        if not other_user: continue

        # Format profile safely
        mini_profile = PostAuthorResponse(
            id=other_user.id,
            username=other_user.username,
            full_name=other_user.full_name,
            profile_picture=other_user.profile_picture
        )

        last_msg_orm = db.query(Message).filter(Message.conversation_id == conv.id).order_by(desc(Message.timestamp)).first()
        
        last_msg = None
        if last_msg_orm:
            last_msg = MessageResponse.model_validate(last_msg_orm)

        payload = ConversationResponse(
            id=conv.id,
            status=conv.status,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            other_user=mini_profile,
            last_message=last_msg
        )

        if conv.status == "accepted":
            inbox.append(payload)
        else:
            # If it's pending, only show it in Requests if the *current_user* is the RECEIVER of the initial connection thread
            # Conversation user1_id is always the initializer of the thread. So if current_user == user2_id, they are receiving the request.
            if str(conv.user2_id) == str(current_user.id):
                requests.append(payload)
            else:
                # If current_user sent the pending request, we still show it in their inbox (or a 'sent requests' tab, but typically inbox)
                inbox.append(payload)

    return InboxResponse(inbox=inbox, requests=requests)


@router.get("/{user_id}", response_model=list[MessageResponse])
def get_chat_history(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all messages in a 1-on-1 thread.
    """
    conversation = db.query(Conversation).filter(
        or_(
            and_(Conversation.user1_id == current_user.id, Conversation.user2_id == user_id),
            and_(Conversation.user1_id == user_id, Conversation.user2_id == current_user.id)
        )
    ).first()

    if not conversation:
        return []

    messages = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.timestamp.asc()).all()
    
    # Mark messages as read if sent by exact opposite user
    unread_messages = [m for m in messages if str(m.receiver_id) == str(current_user.id) and not m.is_read]
    for m in unread_messages:
        m.is_read = True
    
    if unread_messages:
        db.commit()

    return messages


@router.post("/accept/{conversation_id}")
def accept_request(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accept an incoming Message Request.
    """
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
        
    if str(current_user.id) not in [str(conversation.user1_id), str(conversation.user2_id)]:
        raise HTTPException(status_code=403, detail="You can only accept requests targeted at you.")

    conversation.status = "accepted"
    db.commit()
    return {"message": "Chat request accepted!"}
