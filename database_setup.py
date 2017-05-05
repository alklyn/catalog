from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class ISP(Base):
    __tablename__ = "isp"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))  # The user that added it
    user = relationship(User)

    @property
    def serialize(self):
        """
        Return object data in easily serializeable format.
        """
        data = {
            "id": self.id,
            "name": self.name
        }
        return data


class Package(Base):
    __tablename__ = "package"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    bandwidth = Column(Integer, nullable=False)
    cap = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    isp_id = Column(Integer, ForeignKey('isp.id'))
    isp = relationship(ISP)
    user_id = Column(Integer, ForeignKey('user.id'))  # The user that added it
    user = relationship(User)

    @property
    def serialize(self):
        """
        Return object data in easily serializeable format.
        """
        data = {
            "id": self.id,
            "name": self.name,
            "bandwidth": self.bandwidth,
            "cap": self.cap,
            "price": self.price
        }
        return data

# The string form of the URL is dialect[+driver]://user:password@host/dbname
engine = create_engine('postgresql://catalogger:gIrHaUcRe3@localhost/isp')
Base.metadata.create_all(engine)
