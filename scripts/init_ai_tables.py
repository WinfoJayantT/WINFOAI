from app.models.orm import Base
from app.repositories.db import engine

print("Initializing AI internal tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
