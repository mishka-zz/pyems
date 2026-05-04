from abc import ABC, abstractmethod
from pyems.simulation import Simulation


class Structure(ABC):
    """
    Base class for all other structures.  Provides the capability to
    position and transform any structure.
    """

    unique_index = 0

    def __init__(self, sim: Simulation):
        """
        :param sim: The Simulation to which this object will be added.
        """
        self._sim = sim
        self._polygons = None

    @abstractmethod
    def construct(self, position) -> None:
        """
        Build the structure.
        """
        pass

    @property
    def sim(self) -> Simulation:
        return self._sim

    @property
    def polygons(self) -> list:
        """
        Retrieve ``Structure`` polygons.
        """
        return self._polygons

    @classmethod
    def _get_ctr(cls):
        """Retrieve unique counter."""
        return cls.unique_index

    @classmethod
    def _inc_ctr(cls):
        """Increment unique counter."""
        cls.unique_index += 1

    @classmethod
    def _get_inc_ctr(cls):
        """Retrieve and increment unique counter."""
        ctr = cls._get_ctr()
        cls._inc_ctr()
        return ctr
