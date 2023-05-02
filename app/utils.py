import os


def get_environment_variable(name: str) -> str:
    """Возвращает переменную окружения по имени name или поднимает KeyError,
    если переменная не найдена.
    """
    try:
        return os.environ[name]
    except KeyError:
        raise KeyError(f'Environment variable "{name}" not set.')
