from sqlalchemy.orm import declarative_base

# Single declarative base to be shared across modules so relationships
# and ForeignKey constraints across auth and database models resolve
# correctly without creating multiple registries.
Base = declarative_base()
