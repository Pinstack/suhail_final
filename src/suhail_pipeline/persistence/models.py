from geoalchemy2 import Geometry
from sqlalchemy import (
    create_engine,
    ForeignKey,
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    JSON,
    Boolean,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Parcel(Base):
    __tablename__ = "parcels"

    # From DB Report
    parcel_objectid = Column(BigInteger, primary_key=True)
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)
    landuse_group = Column(String)
    landuse_detailed = Column(String)
    subdivision_no = Column(String)
    transaction_price = Column(Float)
    zoning_id = Column(BigInteger)
    neighborhood_id = Column(BigInteger, ForeignKey('neighborhoods.neighborhood_id'))
    block_no = Column(String)
    neighborhood_name = Column(String)
    subdivision_id = Column(BigInteger)
    price_of_meter = Column(Float)
    shape_area = Column(Float)
    zoning_color = Column(String)
    zoning_rule_id = Column(String, ForeignKey('zoning_rules.zoning_rule_id'))
    province_id = Column(BigInteger, ForeignKey('provinces.province_id'))
    municipality_name = Column(String)
    parcel_id = Column(BigInteger)
    parcel_no = Column(String)

    # From DB Report (audit columns)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    geometry_hash = Column(String, nullable=True)
    enriched_at = Column(DateTime(timezone=True))

    neighborhood = relationship("Neighborhood", back_populates="parcels")
    province = relationship("Province", back_populates="parcels")
    transactions = relationship("Transaction", back_populates="parcel")
    price_metrics = relationship("ParcelPriceMetric", back_populates="parcel")
    building_rules = relationship("BuildingRule", back_populates="parcel")


class Transaction(Base):
    __tablename__ = "transactions"
    # From DB Report
    transaction_id = Column(BigInteger, primary_key=True)
    parcel_objectid = Column(BigInteger, ForeignKey('parcels.parcel_objectid'), nullable=False)
    transaction_price = Column(Float)
    price_of_meter = Column(Float)
    transaction_date = Column(DateTime)
    area = Column(Float)
    raw_data = Column(JSON)
    
    parcel = relationship("Parcel", back_populates="transactions")

    __table_args__ = (
        UniqueConstraint('transaction_id', 'parcel_objectid', name='_transaction_parcel_uc'),
    )


class ParcelPriceMetric(Base):
    __tablename__ = "parcel_price_metrics"
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_objectid = Column(BigInteger, ForeignKey('parcels.parcel_objectid'), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    metrics_type = Column(String, nullable=False)
    average_price_of_meter = Column(Float)
    neighborhood_id = Column(BigInteger, ForeignKey('neighborhoods.neighborhood_id'))
    
    parcel = relationship("Parcel", back_populates="price_metrics")
    neighborhood = relationship("Neighborhood", back_populates="price_metrics")

    __table_args__ = (
        UniqueConstraint(
            "parcel_objectid", "month", "year", "metrics_type", name="_parcel_metric_uc"
        ),
    )


class BuildingRule(Base):
    __tablename__ = "building_rules"
    parcel_objectid = Column(BigInteger, ForeignKey('parcels.parcel_objectid'), primary_key=True)
    building_rule_id = Column(String, primary_key=True)
    zoning_id = Column(Integer)
    zoning_color = Column(String)
    zoning_group = Column(String)
    landuse = Column(String)
    description = Column(String)
    name = Column(String)
    coloring = Column(String)
    coloring_description = Column(String)
    max_building_coefficient = Column(String)
    max_building_height = Column(String)
    max_parcel_coverage = Column(String)
    max_rule_depth = Column(String)
    main_streets_setback = Column(String)
    secondary_streets_setback = Column(String)
    side_rear_setback = Column(String)
    raw_data = Column(JSON)
    
    parcel = relationship("Parcel", back_populates="building_rules")

    __table_args__ = (
        UniqueConstraint('parcel_objectid', 'building_rule_id', name='_parcel_rule_uc'),
    )
    
class Neighborhood(Base):
    __tablename__ = 'neighborhoods'
    neighborhood_id = Column(BigInteger, primary_key=True)
    geometry = Column(Geometry('GEOMETRY', srid=4326))
    neighborhood_name = Column(String)
    region_id = Column(BigInteger)
    province_id = Column(BigInteger, ForeignKey('provinces.province_id'))
    price_of_meter = Column(Float)
    shape_area = Column(Float)
    transaction_price = Column(Float)
    zoning_id = Column(BigInteger)
    zoning_color = Column(String)
    geometry_hash = Column(String, nullable=True)

    parcels = relationship("Parcel", back_populates="neighborhood")
    price_metrics = relationship("ParcelPriceMetric", back_populates="neighborhood")
    province = relationship("Province", back_populates="neighborhoods")

class Province(Base):
    __tablename__ = 'provinces'
    province_id = Column(BigInteger, primary_key=True)
    province_name = Column(String)
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326))

    parcels = relationship("Parcel", back_populates="province")
    neighborhoods = relationship("Neighborhood", back_populates="province")
    municipalities = relationship("Municipality", back_populates="province")
    subdivisions = relationship("Subdivision", back_populates="province")

class Municipality(Base):
    __tablename__ = 'municipalities'
    municipality_id = Column(BigInteger, primary_key=True)
    municipality_name = Column(String)
    province_id = Column(BigInteger, ForeignKey('provinces.province_id'))
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326))

    province = relationship("Province", back_populates="municipalities")

class Subdivision(Base):
    __tablename__ = 'subdivisions'
    subdivision_id = Column(BigInteger, primary_key=True)
    geometry = Column(Geometry('GEOMETRY', srid=4326))
    subdivision_no = Column(String)
    shape_area = Column(Float)
    transaction_price = Column(Float)
    price_of_meter = Column(Float)
    zoning_id = Column(BigInteger)
    zoning_color = Column(String)
    province_id = Column(BigInteger, ForeignKey('provinces.province_id'))

    province = relationship("Province", back_populates="subdivisions")

class ParcelsBase(Base):
    __tablename__ = 'parcels_base'
    parcel_id = Column(String, primary_key=True)
    geometry = Column(Geometry('GEOMETRY', srid=4326))

class Street(Base):
    __tablename__ = 'streets'
    street_id = Column(BigInteger, primary_key=True)
    geometry = Column(Geometry('MULTILINESTRING', srid=4326))

class ZoningRule(Base):
    __tablename__ = 'zoning_rules'
    zoning_rule_id = Column(String, primary_key=True)
    description = Column(String)

class LandUseGroup(Base):
    __tablename__ = 'land_use_groups'
    landuse_group = Column(String, primary_key=True)
    description = Column(String) 