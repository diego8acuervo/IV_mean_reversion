"""IB connector – thin wrapper around ib_insync for IV data collection."""

import os
from ib_insync import IB, Stock, Option, util

IB_HOST = os.getenv("IB_HOST", "127.0.0.1")
IB_PORT = int(os.getenv("IB_PORT", 7497))
IB_CLIENT_ID = int(os.getenv("IB_CLIENT_ID", 1))


def connect(host: str = IB_HOST, port: int = IB_PORT, client_id: int = IB_CLIENT_ID) -> IB:
    """Return a connected IB instance."""
    ib = IB()
    ib.connect(host, port, clientId=client_id)
    return ib


def get_option_chain(ib: IB, underlying: str, exchange: str = "SMART", currency: str = "USD"):
    """Fetch option chain contracts for *underlying*."""
    stock = Stock(underlying, exchange, currency)
    ib.qualifyContracts(stock)
    chains = ib.reqSecDefOptParams(stock.symbol, "", stock.secType, stock.conId)
    return chains


def get_market_data(ib: IB, contract, snapshot: bool = True):
    """Request market data (including IV) for *contract*."""
    ticker = ib.reqMktData(contract, genericTickList="106", snapshot=snapshot)
    ib.sleep(2)
    return ticker
