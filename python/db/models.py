from typing import List, Optional
from sqlalchemy import (
        ForeignKey,
        String,
        UniqueConstraint,
)
from sqlalchemy.orm import (
        DeclarativeBase,
        Mapped,
        mapped_column,
        relationship,
)

class Base(DeclarativeBase):
    pass

class Chains(Base):
    __tablename__ = "chains"

    chain_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    native_token: Mapped[str] = mapped_column(String(6))
    evm: Mapped[bool]
    
    tokens: Mapped[List["Tokens"]] = relationship(back_populates="chains")
    dex: Mapped[List["Dexs"]] = relationship(back_populates="chains")
    pools: Mapped[List["Pools"]] = relationship(back_populates="chains")
    
    def __repr__(self) -> str:
        return f"Chain(id={self.chain_id}, name={self.name})"

class Tokens(Base):
    __tablename__ = "tokens"

    coin_id: Mapped[int] = mapped_column(primary_key=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("chains.chain_id"))
    name: Mapped[str] = mapped_column(String(40))
    symbol: Mapped[str] = mapped_column(String(6))
    address: Mapped[str] = mapped_column(String(45))
    decimals: Mapped[int]
    
    __table_args__ = (
            UniqueConstraint("address", "chain_id", name="uq_tokens_address_chain"),
    )

    chains: Mapped[Chains] = relationship(back_populates="tokens")
    pools_as_token0: Mapped[List["Pools"]] = relationship(
            foreign_keys="Pools.token0", 
            back_populates="tokens0",
    )
    pools_as_token1: Mapped[List["Pools"]] = relationship(
            foreign_keys="Pools.token1", 
            back_populates="tokens1",
    )
    
    def __repr__(self) -> str:
        return f"Token(id={self.coin_id}, chain_id={self.chain_id}, \
symbol={self.symbol}, address={self.address})"
       
class Dexs(Base):
    __tablename__ = "dexs"

    dex_id: Mapped[int] = mapped_column(primary_key=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("chains.chain_id"))
    name: Mapped[str] = mapped_column(String(30)) 
    dex_type: Mapped[str] = mapped_column(String(5))
    factory_address: Mapped[str] = mapped_column(String(45))
    quoter_address: Mapped[Optional[str]]
    
    __table_args__ = (
            UniqueConstraint("factory_address", "chain_id", name="uq_dex_address_chain"),
    )

    chains: Mapped[Chains] = relationship(back_populates="dex")
    pools: Mapped[List["Pools"]] = relationship(back_populates="dex")
    def __repr__(self) -> str:
        return f"Dex(id={self.dex_id}, chain_id={self.chain_id}, name={self.name}, \
dex_type={self.dex_type})"

class Pools(Base):
    __tablename__ = "pools"

    chain_id: Mapped[int] = mapped_column(
            ForeignKey("chains.chain_id"),
            primary_key=True
    )
    pool_address: Mapped[str] = mapped_column(
            String(45),
            primary_key=True
    )
    dex_id: Mapped[int] = mapped_column(ForeignKey("dexs.dex_id"))
    token0: Mapped[str] = mapped_column(ForeignKey("tokens.coin_id"))
    token1: Mapped[str] = mapped_column(ForeignKey("tokens.coin_id"))
    fee: Mapped[int] 
    tick_spacing: Mapped[Optional[int]]
    active: Mapped[Optional[bool]]
    
    chains: Mapped[Chains] = relationship(back_populates="pools")
    dex: Mapped[Dexs] = relationship(back_populates="pools")
    tokens0: Mapped[Tokens] = relationship(
            back_populates="pools_as_token0",
            foreign_keys=[token0]
    )
    tokens1: Mapped[Tokens] = relationship(
            back_populates="pools_as_token1",
            foreign_keys=[token1]
    )

    def __repr__(self) -> str:
        return f"Pool(chain_id={self.chain_id}, dex_id={self.dex_id}, \
pool_address={self.pool_address})"

