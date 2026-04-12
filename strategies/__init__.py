from .ma_cross import MACrossStrategy
from .macd import MACDStrategy
from .rsi import RSIStrategy
from .bollinger import BollingerStrategy
from .kdj import KDJStrategy
from .momentum import MomentumStrategy
from .rsi_volume import RSIVolumeStrategy

STRATEGIES = {
    'ma_cross': MACrossStrategy,
    'macd': MACDStrategy,
    'rsi': RSIStrategy,
    'bollinger': BollingerStrategy,
    'kdj': KDJStrategy,
    'momentum': MomentumStrategy,
    'rsi_volume': RSIVolumeStrategy,
}

def get_strategy(name: str, **kwargs):
    """获取策略实例，可传入自定义参数覆盖默认值"""
    cls = STRATEGIES.get(name, MACrossStrategy)
    return cls(**kwargs)

def list_strategies():
    """列出所有可用策略"""
    return {name: cls().name for name, cls in STRATEGIES.items()}
