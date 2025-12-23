from typing import List
from sqlachemy import ForeignKey, String
from sqlalchemy.orm import (
        DeclarativeBase,
        Mapped,
        mapped_column,
        relationship
)

class Base(DelcarativeBase):
    pass

class Chains(Base):
    __tablename__ = "chains"

    chain_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    native_token: Mapped[str] = mapped_column(String(6))
    evm_compatible: Mapped[bool]
    
    tokens: Mapped[List["Tokens"]] = relationship(back_populates="chain")
    dex: Mapped[List["Dex"]] = relationship(back_populates="chain")
    pools: Mapped[List["Pools"]] = relationship(back_populates="chain")
    
    def __repr__(self) -> str:
        return f"Chain(id={self.chain_id}, name={self.name})"

class Tokens(Base):
    __tablename__ = "tokens"

    cmc_id: Mapped[int] = mapped_column(primary_key=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("chains.chain_id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str] = mapped_column(String(6))
    token_address: Mapped[str] = mapped_column(String(45))
    decimals: Mapped[int]
    
    chains: Mapped[Chains] = relationship(back_populates="tokens")
    pools: Mapped[List["Pools"]] = relationship(back_populates="tokens")
    
    def __repr__(self) -> str:
        return f"Token(id={self.cmc_id}, chain_id={self.chain_id}, symbol={self.symbol},\
address={self.token_address})"
       
class Dex(Base):
    __tablename__ = "dex"

    dex_id: Mapped[int] = mapped_column(primary_key=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("chains.chain_id"))
    name: Mapped[str] = mapped_column(String(20)) 
    dex_type: Mapped[Optional[str]]
    factory_address: Mapped[Optional[str]]
    router_address: Mapped[Optional[str]]

    chains: Mapped[List[Chains]] = relationship(back_populates="dex")
    pools: Mapped["Pools"] = relationship(back_populates="dex")

    def __repr__(self) -> str:
        return f"Dex(id={self.dex_id}, chain_id={self.chain_id}, name={self.name}, dex_type={self.dex_type})"

class Pools(Base):
    __tablename__ = "pools"

    chain_id: Mapped[int] = mapped_column(ForeignKey("chains.chain_id"), primary_key=True)
    dex_id: Mapped[int] = mapped_column(ForeignKey("dex.dex_id"), primary_key=True)
    pool_address: Mapped[str] = mapped_column(String(45))
    token0: Mapped[str] = mapped_column(ForeignKey("tokens.cmc_id"), primary_key=True)
    token1: Mapped[str] = mapped_column(ForeignKey("tokens.cmc_id"), primary_key=True)
    fee: Mapped[int] = mapped_column(primary_key=True)
    tick_spacing: Mapped[Optional[int]]
    active: Mapped[Optional[bool]]

    chains: Mapped[Chains] = relationship(back_populates="pools")
    dex: Mapped[Dex] = relationship(back_populates="pools")
    tokens: Mapped[List[Tokens]] = relationship(back_populates="pools")

    def __repr__(self) -> str:
        return f"Pool(chain_id={self.chain_id}, dex_id={self.dex_id}, pool_address={self.pool_addess})"

