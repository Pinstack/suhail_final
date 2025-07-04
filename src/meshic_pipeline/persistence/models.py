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
    landuseagroup = Column(String)
    landuseadetailed = Column(String)
    subdivision_no = Column(String)
    transaction_price = Column(Float)
    zoning_id = Column(BigInteger)
    neighborhood_id = Column(BigInteger, ForeignKey('neighborhoods.neighborhood_id'), nullable=True)
    block_no = Column(String)
    neighborhood_ar = Column(String)
    subdivision_id = Column(BigInteger)
    price_of_meter = Column(Float)
    shape_area = Column(Float)
    zoning_color = Column(String)
    ruleid = Column(String, ForeignKey('zoning_rules.ruleid'), nullable=True)
    province_id = Column(BigInteger, ForeignKey('provinces.province_id'), nullable=True)
    municipality_ar = Column(String)
    parcel_id = Column(BigInteger)
    parcel_no = Column(String)

    # From DB Report (audit columns)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, nullable=False, server_default=text('true'))
    geometry_hash = Column(String, nullable=True)
    enriched_at = Column(DateTime(timezone=True))

    neighborhood = relationship("Neighborhood", back_populates="parcels")
    province = relationship("Province", back_populates="parcels")
    zoning_rule = relationship("ZoningRule", back_populates="parcels")
    transactions = relationship("Transaction", back_populates="parcel")
    price_metrics = relationship("ParcelPriceMetric", back_populates="parcel")
    building_rules = relationship("BuildingRule", back_populates="parcel")


class Transaction(Base):
    __tablename__ = "transactions"
    # From DB Report
    transaction_id = Column(BigInteger, primary_key=True)
    parcel_objectid = Column(BigInteger, ForeignKey('parcels.parcel_objectid'), nullable=True)
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
    parcel_objectid = Column(BigInteger, ForeignKey('parcels.parcel_objectid'), nullable=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    metrics_type = Column(String, nullable=False)
    average_price_of_meter = Column(Float)
    neighborhood_id = Column(BigInteger, ForeignKey('neighborhoods.neighborhood_id'), nullable=True)
    
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
    neighborhood_ar = Column(String)
    region_id = Column(BigInteger)
    province_id = Column(BigInteger, ForeignKey('provinces.province_id'), nullable=True)
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
    province_id = Column(BigInteger, ForeignKey('provinces.province_id'), nullable=True)
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
    province_id = Column(BigInteger, ForeignKey('provinces.province_id'), nullable=True)

    province = relationship("Province", back_populates="subdivisions")

class ParcelsBase(Base):
    __tablename__ = 'parcels_base'
    parcel_id = Column(String, primary_key=True)
    geometry = Column(Geometry('GEOMETRY', srid=4326))

class ZoningRule(Base):
    __tablename__ = 'zoning_rules'
    ruleid = Column(String, primary_key=True)
    description = Column(String)
    
    parcels = relationship("Parcel", back_populates="zoning_rule")

class LandUseGroup(Base):
    __tablename__ = 'land_use_groups'
    landuse_group = Column(String, primary_key=True)
    description = Column(String)

class NeighborhoodsCentroids(Base):
    __tablename__ = 'neighborhoods_centroids'
    id = Column(Integer, primary_key=True, autoincrement=False)
    geometry = Column(Geometry(geometry_type='POINT', srid=4326))
    neighborh_aname = Column(String)
    province_id = Column(Integer)

class MetroLines(Base):
    __tablename__ = 'metro_lines'
    id = Column(Integer, primary_key=True, autoincrement=False)
    geometry = Column(Geometry(geometry_type='MULTILINESTRING', srid=4326))
    track_color = Column(String)
    track_length = Column(Float)
    track_name = Column(String)

class ParcelsCentroids(Base):
    __tablename__ = 'parcels_centroids'
    parcel_no = Column(String, primary_key=True)
    geometry = Column(Geometry('POINT', srid=4326))
    transaction_date = Column(DateTime)
    transaction_price = Column(Float)
    price_of_meter = Column(Float)

class BusLines(Base):
    __tablename__ = 'bus_lines'
    id = Column(Integer, primary_key=True, autoincrement=False)
    geometry = Column(Geometry('MULTILINESTRING', srid=4326))
    busroute = Column(String)
    route_name = Column(String)
    route_type = Column(String)

class MetroStations(Base):
    __tablename__ = 'metro_stations'
    station_code = Column(String, primary_key=True)
    geometry = Column(Geometry('POINT', srid=4326))
    station_name = Column(String)
    line = Column(String)

class RiyadhBusStations(Base):
    __tablename__ = 'riyadh_bus_stations'
    station_code = Column(String, primary_key=True)
    geometry = Column(Geometry('POINT', srid=4326))
    station_name = Column(String)
    route = Column(String)

class QIPopulationMetrics(Base):
    __tablename__ = 'qi_population_metrics'
    grid_id = Column(String, primary_key=True)
    population = Column(Integer)
    geometry = Column(Geometry('POLYGON', srid=4326))

class QIStripes(Base):
    __tablename__ = 'qi_stripes'
    strip_id = Column(String, primary_key=True)
    geometry = Column(Geometry('POLYGON', srid=4326))
    value = Column(Float) 