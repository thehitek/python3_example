from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app.all_models import Role, PlayerSlot, Game

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.utils import datetime_now

association_polygon_object_player_slot = Table(
    "filter_polygon_obj_player_slot",
    Base.metadata,
    Column(
        "polygon_object_id",
        mysql.INTEGER(unsigned=True),
        ForeignKey("polygon_object.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
    Column(
        "player_slot_id",
        mysql.INTEGER(unsigned=True),
        ForeignKey("player_slot.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    ),
)


class PolygonObject(Base):
    __tablename__ = "polygon_object"
    id: Mapped[int] = mapped_column(
        mysql.INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )

    __table_args__ = (
        UniqueConstraint("id_on_map", "polygon_config_id", name="unique_polygon_obj"),
    )

    color: Mapped[list[int]] = mapped_column(mysql.JSON())
    position: Mapped[list] = mapped_column(mysql.JSON())
    id_on_map: Mapped[int] = mapped_column(mysql.SMALLINT(unsigned=True))
    scale: Mapped[float] = mapped_column(mysql.FLOAT(), default=float(1.0))

    description: Mapped[str] = mapped_column(mysql.VARCHAR(255), default="")

    ind_for_led_controller: Mapped[int | None] = mapped_column(
        mysql.SMALLINT(unsigned=True), nullable=True
    )

    role: Mapped["Role"] = relationship(back_populates="polygons")
    role_id: Mapped[int] = mapped_column(
        mysql.INTEGER(unsigned=True), ForeignKey("role.id", onupdate="CASCADE")
    )

    players_home_obj: Mapped[list["PlayerSlot"]] = relationship(
        back_populates="home_obj"
    )

    polygon_config: Mapped["PolygonConfig"] = relationship(
        back_populates="polygon_objects"
    )
    polygon_config_id: Mapped[int] = mapped_column(
        mysql.INTEGER(unsigned=True),
        ForeignKey("polygon_config.id", ondelete="CASCADE", onupdate="CASCADE"),
    )

    player_slots: Mapped[list["PlayerSlot"]] = relationship(
        secondary=association_polygon_object_player_slot, back_populates="filter"
    )


class PolygonConfig(Base):
    __tablename__ = "polygon_config"

    # __table_args__ = (
    #     UniqueConstraint("name", "created_at",
    #                      name="unique_polygon_config_ind"),
    # )

    id: Mapped[int] = mapped_column(
        mysql.INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )

    name: Mapped[str] = mapped_column(mysql.VARCHAR(255), default="string", unique=True)
    description: Mapped[str] = mapped_column(mysql.VARCHAR(511), default="string")
    arena_width: Mapped[float] = mapped_column(mysql.FLOAT(), default=8.0)
    created_at: Mapped[datetime] = mapped_column(
        mysql.TIMESTAMP(fsp=6), default=datetime_now
    )
    polygon_objects: Mapped[list["PolygonObject"]] = relationship(
        back_populates="polygon_config", cascade="all, delete", passive_deletes=True
    )

    games: Mapped[list["Game"]] = relationship(back_populates="polygon_config")
