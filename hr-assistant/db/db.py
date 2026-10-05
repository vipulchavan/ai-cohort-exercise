from db.models import DB_PATH
from db.models import Conversation, ChatMessage
from sqlalchemy.orm import sessionmaker  
from sqlalchemy import engine, create_engine

def create_conversation(title):
    new_conversation = Conversation(title=title)
    db_session.add(new_conversation)
    db_session.commit()
    db_session.refresh(new_conversation)
    return new_conversation

def list_conversations():
    return db_session.query(Conversation).all()

def create_chat_message(conversation_id:str, text:str, role:str, tokens_spent:int=0):
    new_message = ChatMessage(conversation_id=conversation_id, role=role, text=text, tokens_spent=tokens_spent)
    db_session.add(new_message)
    db_session.commit()
    db_session.refresh(new_message)
    return new_message

def list_messages_in_conversation(conversation_id):
    return db_session.query(ChatMessage).filter(ChatMessage.conversation_id == conversation_id).all()

def update_tokens_usage(conversation_id, tokens_spent):
    conversation = db_session.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.tokens_spent += tokens_spent
        db_session.commit()

def update_conversation_summary(conversation_id, summary):
    # Check if a summary already exists for the conversation
    existing_summary = db_session.query(ConversationSummary).filter(ConversationSummary.conversation_id == conversation_id).first()
    
    if existing_summary:
        # Update the existing summary
        existing_summary.summary_text = summary
    else:
        # Create a new summary
        new_summary = ConversationSummary(conversation_id=conversation_id, summary_text=summary)
        db_session.add(new_summary)
    
    db_session.commit()

def get_conversation_summary(conversation_id):
    return db_session.query(ConversationSummary).filter(ConversationSummary.conversation_id == conversation_id).first() 

engine = create_engine(DB_PATH)
db_session = sessionmaker(bind=engine)()    