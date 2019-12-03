import sqlalchemy.types as types

class BetDecimal(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = int(round(value * 10, 0))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value / 10
        return value

class IntCurrency(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = int(round(value * 100, 0))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value / 100
        return value

class FantasyPts(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = int(round(value * 100, 0))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value / 100
        return value

class FantasyStats(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = int(round(value * 1000000, 0))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value / 1000000
        return value

class SalaryCapDecimal(types.TypeDecorator):
    impl = types.Integer

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = int(round(value * 10000, 0))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value / 10000
        return value
