from sqlmodel import create_engine, SQLModel, Session

sqlite_file_name = "diary.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# connect_args={"check_same_thread": False} is required ONLY for SQLite
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def init_db():
    # This automatically creates the database and tables if they don't exist
    SQLModel.metadata.create_all(engine)

def get_session():
    # Dependency that provides a database session to FastAPI routes
    with Session(engine) as session:
        yield session