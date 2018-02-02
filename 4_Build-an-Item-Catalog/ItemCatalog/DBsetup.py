#!/usr/bin/env python3

# import all module
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# Create instance of declarative_base
Base = declarative_base()


# Schema
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = "category"
    name = Column(String(80), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User)

    # JSON
    @property
    def serialize(self):
        # return obj data in easily serializeable format
        return {
            'name': self.name,
        }


class Item(Base):
    __tablename__ = "item"
    name = Column(String(80), primary_key=True, nullable=False)
    description = Column(String(250))
    category_name = Column(String(80), ForeignKey("category.name"))
    category = relationship(Category)

    # JSON
    @property
    def serialize(self):
        # return obj data in easily serializeable format
        return {
            'name': self.name,
            'description': self.description,
        }

# post - Configuration
engine = create_engine("sqlite:///categories.db")
Base.metadata.create_all(engine)
