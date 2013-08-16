"""Defines application models"""

from oz.plugins import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Date

class Option(sqlalchemy.Base):
    __tablename__ = "options"
    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False)
    value = Column(String(), nullable=False)

    def __unicode__(self):
        return self.key
