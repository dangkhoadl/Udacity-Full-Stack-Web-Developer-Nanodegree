#!/usr/bin/env python3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DBsetup import Category, Base, Item

engine = create_engine('sqlite:///categories.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Category 1
category1 = Category(
    name="Soccer",
    user_id=1)
session.add(category1)
session.commit()

item1 = Item(
    name="Ball",
    description="kicked ...",
    category=category1)
session.add(item1)
session.commit()

item2 = Item(
    name="Goal",
    description="Goal keeper home ...",
    category=category1)
session.add(item2)
session.commit()

# Category 2
category2 = Category(
    name="Snowboarding",
    user_id=2)
session.add(category2)
session.commit()

item1 = Item(
    name="Snowboard",
    description="thrown ...",
    category=category2)
session.add(item1)
session.commit()

item2 = Item(
    name="Googgles",
    description="wearable ...",
    category=category2)
session.add(item2)
session.commit()
