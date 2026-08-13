from sqlalchemy import inspect


def to_dict(model):
    if model is None:
        return None
    return {column.key: getattr(model, column.key) for column in inspect(model).mapper.column_attrs}


def to_dicts(models):
    return [to_dict(model) for model in models]
