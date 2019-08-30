from fractions import Fraction as BuiltinFraction
from abc import ABC, abstractmethod
import sys


class Node(ABC):
    __slots__ = ["ismono", "modreverse", "hasmono"]

    def __init__(self, ismono, modreverse, hasmono):
        self.ismono = ismono  # Node is only executed forwards
        self.modreverse = modreverse  # Node modifies a non-mono variable
        self.hasmono = hasmono  # Node makes use of mono variables

    @abstractmethod
    def search(self, condition):
        pass


class Fraction(BuiltinFraction):
    ismono = False
    modreverse = False
    hasmono = False

    def search(self, condition):
        self.hasmono = True
        return condition(self)


class Binop(Node):
    __slots__ = ["lhs", "op", "rhs", "name"]

    def __init__(self, lhs, op, rhs, name="UNNAMED", **kwargs):
        super().__init__(**kwargs)
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.name = name

    def search(self, condition):
        return (condition(self)
                or self.lhs.search(condition)
                or self.rhs.search(condition))

print(Binop(1,2,3, ismono=5, hasmono=8, modreverse=0).hasmono)
