"""评价元数据 service。"""


class MetadataService:
    def __init__(self, ctx):
        self._ctx = ctx

    @property
    def _ui(self):
        return self._ctx.ui

    def get_all(self) -> dict:
        ui = self._ui
        return {
            'car_model': getattr(ui, 'preset_car_model', ''),
            'tuning_parts': getattr(ui, 'preset_tuning_parts', ''),
            'evaluator': getattr(ui, 'preset_evaluator', ''),
            'condition': getattr(ui, 'preset_condition', ''),
        }

    def set_fields(self, car_model=None, tuning_parts=None,
                   evaluator=None, condition=None) -> dict:
        ui = self._ui
        changed = {}

        if car_model is not None:
            ui.preset_car_model = str(car_model)
            changed['car_model'] = str(car_model)
        if tuning_parts is not None:
            ui.preset_tuning_parts = str(tuning_parts)
            changed['tuning_parts'] = str(tuning_parts)
        if evaluator is not None:
            ui.preset_evaluator = str(evaluator)
            changed['evaluator'] = str(evaluator)
        if condition is not None:
            ui.preset_condition = str(condition)
            changed['condition'] = str(condition)

        return changed
