from sqlalchemy import Column, Integer, String, DateTime, func, Text
from server.db_manager import Base

class RagflowModel(Base):
    __tablename__ = 'ragflow'

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(64), nullable=False, index=True)
    chat_id = Column(String(64), nullable=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    ragflow_data = Column(Text, nullable=True)
    create_at = Column(DateTime, default=func.now(), nullable=False)
    update_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False) 