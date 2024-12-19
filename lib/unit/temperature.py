from enum import Enum

from lib.unit._util import _ValueWithUnit


# Conversions see https://en.wikipedia.org/wiki/Conversion_of_scales_of_temperature
class TemperatureCelsius(_ValueWithUnit):
    unit = "°C"

    def si_value(self) -> float:
        return self.value + 273.15

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureCelsius':
        return TemperatureCelsius(value - 273.15)


class TemperatureFahrenheit(_ValueWithUnit):
    unit = "°F"

    def si_value(self) -> float:
        return (self.value + 459.67) / 1.8

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureFahrenheit':
        return TemperatureFahrenheit(value * 1.8 - 459.67)


class TemperatureKelvin(_ValueWithUnit):
    unit = "K"

    def si_value(self) -> float:
        return self.value

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureKelvin':
        return TemperatureKelvin(value)


class TemperatureRankine(_ValueWithUnit):
    unit = "°Ra"

    def si_value(self) -> float:
        return self.value / 1.8

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureRankine':
        return TemperatureRankine(value * 1.8)


class TemperatureReaumur(_ValueWithUnit):
    unit = "°Ré"

    def si_value(self) -> float:
        return (self.value - 273.15) * 0.8

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureReaumur':
        return TemperatureReaumur(value / 0.8 + 273.15)


class TemperatureRomer(_ValueWithUnit):
    unit = "°Rø"

    def si_value(self) -> float:
        return (self.value - 273.15) * 0.525 + 7.5

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureRomer':
        return TemperatureRomer((value - 7.5) / 0.525 + 273.15)


class TemperatureDelisle(_ValueWithUnit):
    unit = "°De"

    def si_value(self) -> float:
        return (373.15 - self.value) * 1.5

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureDelisle':
        return TemperatureDelisle(373.15 - value / 1.5)


class TemperatureNewton(_ValueWithUnit):
    unit = "°N"

    def si_value(self) -> float:
        return (self.value - 273.15) * 0.33

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureNewton':
        return TemperatureNewton(value / 0.33 + 273.15)


TemperatureUnits = {
    TemperatureCelsius.unit: TemperatureCelsius,
    TemperatureFahrenheit.unit: TemperatureFahrenheit,
    TemperatureKelvin.unit: TemperatureKelvin,
    TemperatureReaumur.unit: TemperatureReaumur,
    TemperatureRankine.unit: TemperatureRankine,
    TemperatureRomer.unit: TemperatureRomer,
    TemperatureDelisle.unit: TemperatureDelisle,
    TemperatureNewton.unit: TemperatureNewton,
}
