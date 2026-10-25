#Импотр типов для аннотаций
from __future__ import annotations

from typing import Any, Hashable, Iterable, Iterator, List, Optional, Tuple
#Создаем кортеж
Entry = Tuple[int, Any]  # (hash(элемента), элемент)


class _HashTable:
    """Хеш-таблица с цепочками: массив бакетов, каждый бакет список (hash, элемент).

    Индекс бакета: hash(element) % capacity. При коэффициенте заполнения > 0.75
    ёмкость удваивается и все элементы перераспределяются (rehash).
    """

    INITIAL_CAPACITY = 8 #начальное количество бакетов
    MAX_LOAD_FACTOR = 0.75 #максимальный коэффициент заполнения

    def __init__(self) -> None:
        #создаем список из 8 пустых бакетов
        self._buckets: List[List[Entry]] = [[] for _ in range(self.INITIAL_CAPACITY)]
        # счетчик числа кортежей
        self._size = 0

    @property
    def capacity(self) -> int:
        """Текущее число бакетов"""
        return len(self._buckets)

    @property
    def load_factor(self) -> float:
        """Коэффициент заполнения: элементов на бакет"""
        return self._size / self.capacity

    def __len__(self) -> int:
        """Размер таблицы через len()"""
        return self._size

    def _bucket(self, h: int) -> List[Entry]:
        """Возвращает бакет, в который должен попасть элемент с хешем h"""
        return self._buckets[h % self.capacity]

    @staticmethod
    def _find(bucket: List[Entry], h: int, item: Any) -> int:
        """Позиция элемента в цепочке или -1. Сначала сравниваем хеши, если хеши совпали, то и сами объекты."""
        for i, (eh, elem) in enumerate(bucket):
            if eh == h and (elem is item or elem == item):
                return i
        return -1

    def contains(self, item: Hashable) -> bool:
        """Есть ли элемент в таблице. Нехешируемый элемент -> TypeError."""
        h = hash(item)
        return self._find(self._bucket(h), h, item) != -1

    def add(self, item: Hashable) -> bool:
        """Добавить элемент; True, если он был новым."""
        h = hash(item)
        bucket = self._bucket(h)
        # проверим, если элемент уже есть
        if self._find(bucket, h, item) != -1:
            return False
            # добавляем новую запись в конец цепочки
        bucket.append((h, item))
        self._size += 1
        # увеличиваем таблицу, если нужно
        if self.load_factor > self.MAX_LOAD_FACTOR:
            self._rehash(self.capacity * 2)
        return True

    def remove(self, item: Hashable) -> None:
        """Удалить элемент; если его нет ошибка.
        Ставим на место удаляемого элемента последний, затем удаляем последний
        """
        h = hash(item)
        bucket = self._bucket(h)
        i = self._find(bucket, h, item)
        if i == -1:
            raise KeyError(item) #если элемента, который хотели удалить нет, то ошибка
        bucket[i] = bucket[-1]  # ставим последний на место удаляемого
        bucket.pop() #удаляем последний
        self._size -= 1

    def _rehash(self, new_capacity: int) -> None:
        """Увеличить таблицу и перераспределить элементы по новому массиву бакетов (хеши уже сохранены)
        Вызывается если load_factor > MAX_LOAD_FACTOR
        Создает новый массив бакетов большего размера и перекладывает туда
        все элементы, заново вычисляя индекс
        """
        # сохраняем ссылку на первый массив данных
        old = self._buckets
        # создаем новый пустой массив
        self._buckets = [[] for _ in range(new_capacity)]
        # перебираем все старые бакеты
        for bucket in old:
            # вычисляем новый индекс
            for h, elem in bucket:
                # кладем запись в конец цепочки нового бакета
                self._buckets[h % new_capacity].append((h, elem))

    def __iter__(self) -> Iterator[Any]:
        #перебираем все бакеты
        for bucket in self._buckets:
            #внутри каждого бакета перебираем все записи
            for _, elem in bucket:
                yield elem


class HashSet:
    """Множество хешируемых элементов поверх `_HashTable`.

    Как и встроенный set, считает равные элементы с одинаковым хешем одним
    элементом: 1, 1.0 и True это один элемент (хранится первый добавленный).
    """

    __hash__ = None  # изменяемый объект — нехешируемый, как встроенный set

    def __init__(self, iterable: Optional[Iterable[Hashable]] = None) -> None:
        """Пустое множество или множество из элементов iterable."""
        #создаем внутреннюю хеш-таблицу
        self._table = _HashTable()
        # если передан iteratable, добавляем все элементы
        if iterable is not None:
            for item in _as_iterable(iterable):
                self._table.add(item)

    # базовые операции
    def add(self, x: Hashable) -> None:
        """Добавить элемент (дубликаты игнорируются)."""
        self._table.add(x)

    def remove(self, x: Hashable) -> None:
        """Удалить элемент; KeyError, если его нет."""
        self._table.remove(x)

    def contains(self, x: Hashable) -> bool:
        """Принадлежит ли элемент множеству."""
        return self._table.contains(x)

    def __contains__(self, x: object) -> bool:
        """Позволяет использовать оператор in"""
        return self._table.contains(x)

    def __len__(self) -> int:
        """Позволяет использовать len"""
        return len(self._table)

    def __iter__(self) -> Iterator[Any]:
        """Позволяет перебирать элементы"""
        return iter(self._table)

    # операции над множествами
    def union(self, other: Iterable[Hashable]) -> "HashSet":
        """Объединение: новый HashSet из всех элементов self и other, исходные не меняются O(n + m)"""
        #создаем копию self
        result = HashSet(self)
        # добавим все элементы из other
        for item in _as_iterable(other):
            result.add(item)
        return result

    def intersection(self, other: Iterable[Hashable]) -> "HashSet":
        """Пересечение: новый HashSet из общих элементов self and other O(n + m)"""
        # приводим other to HashSet
        other_set = _as_hash_set(other)
        # для перебора выбираем меньшее множество
        small, big = (self, other_set) if len(self) <= len(other_set) else (other_set, self)
        return HashSet(item for item in small if item in big)

    def difference(self, other: Iterable[Hashable]) -> "HashSet":
        """Разность: элементы self, которых нет в other O(n + m)."""
        other_set = _as_hash_set(other)
        return HashSet(item for item in self if item not in other_set)

    def is_subset(self, other: Iterable[Hashable]) -> bool:
        """Все ли элементы self входят в other."""
        other_set = _as_hash_set(other)
        return len(self) <= len(other_set) and all(item in other_set for item in self)

    def is_superset(self, other: Iterable[Hashable]) -> bool:
        """Входят ли все элементы other в self."""
        return all(item in self for item in _as_iterable(other))

    # представление и сравнение
    def __repr__(self) -> str:
      """Строковое представление для отладки"""  
        if not len(self):
            return "HashSet()" #пустое множество
            # собираем строку из repr каждого элемента
        return "HashSet({" + ", ".join(repr(item) for item in self) + "})"

    def __eq__(self, other: object) -> bool:
        """Равны, если содержат одни и те же элементы (сравнение с set/frozenset тоже работает)"""
        # если other is set or frozenset, то приводим к HashSet
        if isinstance(other, (set, frozenset)):
            other = HashSet(other)
            # Если не Hashset, возвращаем ошибку
        if not isinstance(other, HashSet):
            return NotImplemented
            # сравниваем размеры и наличие всех элементов
        return len(self) == len(other) and all(item in other for item in self)


def _as_iterable(other: Any) -> Iterable[Any]:
    """Проверить, что other итерируемый; иначе TypeError."""
    try:
        iter(other) #пробуем получить итератор
    except TypeError:
        raise TypeError(f"ожидался HashSet или итерируемый объект, получен {type(other).__name__}") from None
    return other


def _as_hash_set(other: Any) -> HashSet:
    """Привести other к HashSet (без копирования, если это уже HashSet)"""
    return other if isinstance(other, HashSet) else HashSet(_as_iterable(other))
