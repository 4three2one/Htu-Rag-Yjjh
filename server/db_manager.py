import os
import pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from src import config
from server.models import Base
from server.models.user_model import User
from server.models.thread_model import Thread
from server.models.kb_models import KnowledgeDatabase, KnowledgeFile, KnowledgeNode, KnowledgeHierarchy
from src.utils import logger
from server.models.ragflow_model import RagflowModel

class DBManager:
    """数据库管理器 - 只提供基础的数据库连接和会话管理"""

    def __init__(self):
        self.db_path = os.path.join(config.save_dir, "database", "server.db")
        self.ensure_db_dir()

        # 创建SQLAlchemy引擎
        self.engine = create_engine(f"sqlite:///{self.db_path}")

        # 创建会话工厂
        self.Session = sessionmaker(bind=self.engine)

        # 确保表存在
        self.create_tables()

    def ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        pathlib.Path(db_dir).mkdir(parents=True, exist_ok=True)

    def create_tables(self):
        """创建数据库表"""
        # 确保所有表都会被创建
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created/checked")

    def get_session(self):
        """获取数据库会话"""
        return self.Session()

    @contextmanager
    def get_session_context(self):
        """获取数据库会话的上下文管理器"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            session.close()

    def check_first_run(self):
        """检查是否首次运行"""
        session = self.get_session()
        try:
            # 检查是否有任何用户存在
            return session.query(User).count() == 0
        finally:
            session.close()

    def add_knowledge_hierarchy(self, db_id, parent_db_id=None, order=0):
        """添加知识库层级关系"""
        with self.get_session_context() as session:
            hierarchy = KnowledgeHierarchy(db_id=db_id, parent_db_id=parent_db_id, order=order)
            session.add(hierarchy)
            session.commit()
            return hierarchy.to_dict()  # 返回字典格式

    def get_knowledge_hierarchy(self, db_id):
        """获取某知识库的层级信息"""
        with self.get_session_context() as session:
            result = session.query(KnowledgeHierarchy).filter_by(db_id=db_id).first()
            return result.to_dict() if result else None  # 返回字典格式

    def get_children_knowledge(self, parent_db_id):
        """获取某父级下的所有子知识库"""
        with self.get_session_context() as session:
            results = session.query(KnowledgeHierarchy).filter_by(parent_db_id=parent_db_id).all()
            return [result.to_dict() for result in results]  # 返回字典列表

    def delete_knowledge_hierarchy(self, db_id):
        """删除某知识库的层级关系"""
        with self.get_session_context() as session:
            session.query(KnowledgeHierarchy).filter_by(db_id=db_id).delete()
            session.query(KnowledgeHierarchy).filter_by(parent_db_id=db_id).delete()
            session.commit()

    def get_all_knowledge_hierarchy(self):
        """获取所有知识库层级关系"""
        with self.get_session_context() as session:
            results = session.query(KnowledgeHierarchy).all()
            return [result.to_dict() for result in results]  # 返回字典列表

    def add_ragflow(self, thread_id, chat_id=None, session_id=None):
        """新增 ragflow 记录"""
        with self.get_session_context() as session:
            ragflow = RagflowModel(thread_id=thread_id, chat_id=chat_id, session_id=session_id)
            session.add(ragflow)
            session.commit()
            return ragflow

    def get_ragflow_by_id(self, ragflow_id):
        """通过 id 获取 ragflow 记录"""
        with self.get_session_context() as session:
            ragflow = session.query(RagflowModel).filter_by(id=ragflow_id).first()
            return ragflow

    def get_ragflow_by_thread_id(self, thread_id):
        """通过 thread_id 获取 ragflow 记录"""
        with self.get_session_context() as session:
            ragflow = session.query(RagflowModel).filter_by(thread_id=thread_id).first()
            return ragflow

    def update_ragflow(self, ragflow_id, **kwargs):
        """更新 ragflow 记录"""
        with self.get_session_context() as session:
            ragflow = session.query(RagflowModel).filter_by(id=ragflow_id).first()
            if not ragflow:
                return None
            for key, value in kwargs.items():
                if hasattr(ragflow, key):
                    setattr(ragflow, key, value)
            session.commit()
            return ragflow

    def delete_ragflow_by_id(self, ragflow_id):
        """通过 id 删除 ragflow 记录"""
        with self.get_session_context() as session:
            session.query(RagflowModel).filter_by(id=ragflow_id).delete()
            session.commit()

    def get_all_ragflow(self):
        """获取所有 ragflow 记录"""
        with self.get_session_context() as session:
            ragflows = session.query(RagflowModel).all()
            return ragflows

# 创建全局数据库管理器实例
db_manager = DBManager()
