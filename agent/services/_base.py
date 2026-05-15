"""Service 基类 — 消除重复的 __init__(ctx) / _ui 样板代码。"""


class BaseService:
    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def _ui(self):
        return self._ctx.ui
