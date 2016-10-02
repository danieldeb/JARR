from bootstrap import db
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship


class Icon(db.Model):
    url = Column(String, primary_key=True)
    content = Column(String, default=None)
    mimetype = Column(String, default="application/image")

    # relationships
    feeds = relationship('Feed', backref='icon')
