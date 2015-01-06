"""Defines application models"""

import oz.sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Date

class Option(oz.sqlalchemy.Base):
    __tablename__ = "options"
    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False)
    value = Column(String(), nullable=False)

    def __unicode__(self):
        return self.key
