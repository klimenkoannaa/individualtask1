import random

import pytest

from hash_set import HashSet, _HashTable


class Collide:
    """Разные объекты с одинаковым хешем, искусственные коллизии"""

    def __init__(self, value: int) -> None:
        self.value = value

    def __hash__(self) -> int:
        return 42

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Collide) and self.value == other.value

    def __repr__(self) -> str:
        return f"Collide({self.value})"


# ---------- создание
#Проверяем коррректное создание пустого
def test_empty():
    s = HashSet()
    assert len(s) == 0
    assert list(s) == []
    assert repr(s) == "HashSet()"

#проверяем создание множества из разных итерируемых объектов
def test_from_iterable_and_generator():
    assert HashSet([1, 2, 2, 3]) == HashSet({1, 2, 3})
    assert HashSet(x * 2 for x in range(3)) == HashSet([0, 2, 4])
    assert HashSet("abca") == HashSet(["a", "b", "c"])

# проверяем что при передаче неитерируемого объекта будет ошибка
def test_init_rejects_non_iterable():
    with pytest.raises(TypeError):
        HashSet(5)


# ---------- add / remove / contains
#проверяем что добавляет элементы, а дубликаты игнорирует
def test_add_and_duplicates():
    s = HashSet()
    s.add(1)
    s.add(1)
    s.add("a")
    assert len(s) == 2
    assert 1 in s and s.contains("a")


def test_remove():
    s = HashSet([1, 2, 3])
    s.remove(2)
    assert 2 not in s
    assert len(s) == 2
# проверяет что удаление несуществующего дает ошибку

def test_remove_missing_raises_key_error():
    s = HashSet([1])
    with pytest.raises(KeyError):
        s.remove(99)
    s.remove(1)
    with pytest.raises(KeyError):
        s.remove(1)  # повторное удаление
    with pytest.raises(KeyError):
        HashSet().remove(None)
# проверяем что поиск отсутствующего дает ошибку

def test_contains_missing():
    s = HashSet([1, 2])
    assert not s.contains(3)
    assert 3 not in s
    assert not HashSet().contains(1)

# проверяем что None хешируемый
def test_none_as_element():
    s = HashSet([None])
    assert None in s
    assert len(s) == 1
    s.remove(None)
    assert None not in s

# Проверяет, что 1, 1.0 и True считаются одним элементом (как в set)
def test_equal_values_of_different_types_are_one_element():
    s = HashSet([1, 1.0, True])
    assert len(s) == 1
    assert 1 in s and 1.0 in s and True in s
    assert list(s) == [1]  # хранится первый добавленный, как во встроенном set
    s.remove(True)
    assert len(s) == 0

# Проверяет, что 0, False, 0.0 — один элемент, "0" — другой, "" — третий.
def test_zero_false_and_strings_vs_numbers():
    s = HashSet([0, False, 0.0, "0", ""])
    assert len(s) == 3  # 0/False/0.0, "0", ""


# ---------- нехешируемые элементы
@pytest.mark.parametrize("bad", [[1, 2], {"a": 1}, {1, 2}, HashSet([1])])
def test_unhashable_raises_type_error(bad):
    # Проверяет, что при работе с нехешируемыми объектами кидается TypeError
    s = HashSet()
    with pytest.raises(TypeError):
        s.add(bad)
    with pytest.raises(TypeError):
        s.contains(bad)
    with pytest.raises(TypeError):
        _ = bad in s
    with pytest.raises(TypeError):
        s.remove(bad)
    with pytest.raises(TypeError):
        HashSet([1, bad])


def test_hashset_itself_is_unhashable():
    # Проверяет, что HashSet нельзя хешировать (как и встроенный set)
    with pytest.raises(TypeError):
        hash(HashSet())


# ---------- union / intersection / difference
def test_union():
    a, b = HashSet([1, 2]), HashSet([2, 3])
    assert a.union(b) == HashSet([1, 2, 3])
    assert a.union([3, 4]) == HashSet([1, 2, 3, 4])


def test_intersection():
    a, b = HashSet([1, 2, 3]), HashSet([2, 3, 4])
    assert a.intersection(b) == HashSet([2, 3])
    assert a.intersection([5]) == HashSet()
    assert a.intersection((3, 3, 1)) == HashSet([1, 3])


def test_difference():
    a, b = HashSet([1, 2, 3]), HashSet([2])
    assert a.difference(b) == HashSet([1, 3])
    assert b.difference(a) == HashSet()


def test_operations_with_empty_sets():
    # операции с пустыми множествами
    a, e = HashSet([1, 2]), HashSet()
    assert a.union(e) == a and e.union(a) == a
    assert a.intersection(e) == e and e.intersection(a) == e
    assert a.difference(e) == a and e.difference(a) == e
    assert e.union(e) == e and e.intersection(e) == e and e.difference(e) == e


def test_operations_with_self():
    # операции с самим собой
    a = HashSet([1, 2, 3])
    assert a.union(a) == a
    assert a.intersection(a) == a
    assert a.difference(a) == HashSet()
    assert a.is_subset(a) and a.is_superset(a)
    assert a == HashSet([1, 2, 3])  # исходное не изменилось


def test_operations_do_not_mutate_and_return_new_objects():
    # Проверяет, что операции не меняют исходные множества и возвращают новые
    a, b = HashSet([1, 2]), HashSet([2, 3])
    for op in (a.union, a.intersection, a.difference):
        res = op(b)
        assert res is not a and res is not b
        assert isinstance(res, HashSet)
    assert a == HashSet([1, 2]) and b == HashSet([2, 3])
    # изменение результата не трогает исходные
    u = a.union(b)
    u.add(100)
    assert 100 not in a and 100 not in b


@pytest.mark.parametrize("method", ["union", "intersection", "difference", "is_subset", "is_superset"])
@pytest.mark.parametrize("bad", [5, 3.14, None, object()])
def test_operations_reject_non_iterable(method, bad):
    #Проверяет, что операции кидают TypeError при неитерируемом аргументе
    with pytest.raises(TypeError):
        getattr(HashSet([1]), method)(bad)


def test_operations_with_unhashable_items_in_other():
    #Проверяет, что операции кидают TypeError, если внутри other есть нехешируемые
    with pytest.raises(TypeError):
        HashSet([1]).union([[1]])
    with pytest.raises(TypeError):
        HashSet([1]).intersection([[1]])


# ---------- is_subset / is_superset
def test_subset_superset():
    #Проверяет is_subset и is_superset на обычных множествах
    a, b = HashSet([1, 2]), HashSet([1, 2, 3])
    assert a.is_subset(b) and not b.is_subset(a)
    assert b.is_superset(a) and not a.is_superset(b)
    assert a.is_subset([1, 2, 5, 2])
    assert b.is_superset([3, 3])


def test_subset_superset_equal_sets():
    #Проверяет, что равные множества — подмножества и надмножества друг друга
    a, b = HashSet([1, 2]), HashSet([2, 1])
    assert a.is_subset(b) and a.is_superset(b)
    assert b.is_subset(a) and b.is_superset(a)


def test_subset_superset_empty():
    #Проверяет краевые случаи с пустым множеством
    e, a = HashSet(), HashSet([1])
    assert e.is_subset(a) and e.is_subset(e) and e.is_subset([])
    assert a.is_superset(e) and e.is_superset(e) and a.is_superset([])
    assert not a.is_subset(e)
    assert not e.is_superset(a)


def test_disjoint_sets_not_subsets():
    #проверяет для непересекающихся множеств
    a, b = HashSet([1]), HashSet([2])
    assert not a.is_subset(b) and not a.is_superset(b)


# ---------- len / iter / repr / eq
def test_len_and_iter_have_no_duplicates():
    #Проверяет, что len и iter возвращают одно и то же количество без дубликатов
    data = [5, 3, 5, 1, 3, 3]
    s = HashSet(data)
    items = list(s)
    assert len(s) == 3 == len(items)
    assert sorted(items) == [1, 3, 5]


def test_repr():
    #Проверяет строковое представление множества
    assert repr(HashSet([1])) == "HashSet({1})"
    r = repr(HashSet([1, 2, 3]))
    assert r.startswith("HashSet({") and r.endswith("})")
    assert sorted(int(x) for x in r[9:-2].split(", ")) == [1, 2, 3]
    assert repr(HashSet(["a"])) == "HashSet({'a'})"


def test_eq():
    #Проверяет сравнение множеств
    assert HashSet([1, 2]) == HashSet([2, 1])
    assert HashSet([1, 2]) != HashSet([1])
    assert HashSet([1, 2]) != HashSet([1, 3])
    assert HashSet() == HashSet()
    assert HashSet([1, 2]) == {1, 2}
    assert HashSet([1]) != [1]  # список — не множество


# ---------- рост таблицы
def test_growth_with_many_elements():
    #добавляем 10 000 элементов, проверяем рехеширование и удаление
    s = HashSet()
    n = 10_000
    for i in range(n):
        s.add(i)
        assert s._table.load_factor <= _HashTable.MAX_LOAD_FACTOR
    assert len(s) == n
    assert s._table.capacity >= n / _HashTable.MAX_LOAD_FACTOR
    assert all(i in s for i in range(n))
    assert -1 not in s and n not in s
    assert sorted(s) == list(range(n))
    for i in range(0, n, 2):
        s.remove(i)
    assert len(s) == n // 2
    assert all((i in s) == (i % 2 == 1) for i in range(n))


def test_initial_capacity_and_first_rehash():
    #Проверяет, что первое рехеширование происходит ровно при load_factor > 0.75
    s = HashSet()
    assert s._table.capacity == 8
    for i in range(6):  # 6 / 8 = 0.75 — ещё не больше порога
        s.add(i)
    assert s._table.capacity == 8
    s.add(6)  # 7 / 8 > 0.75
    assert s._table.capacity == 16


def test_negative_and_large_hashes():
    #Проверяет, что отрицательные и очень большие хеши не ломают индекс
    s = HashSet([-1, -2, 2**100, -(2**100), "строка"])
    assert len(s) == 5
    assert all(x in s for x in [-1, -2, 2**100, -(2**100), "строка"])


# ---------- коллизии
def test_collisions():
    #Проверяет, что 50 объектов с одинаковым хешем корректно обрабатываются
    objs = [Collide(i) for i in range(50)]
    s = HashSet(objs)
    assert len(s) == 50
    assert all(Collide(i) in s for i in range(50))
    assert Collide(50) not in s
    s.add(Collide(3))  # равный объект — дубликат
    assert len(s) == 50
    s.remove(Collide(10))
    assert Collide(10) not in s and len(s) == 49
    with pytest.raises(KeyError):
        s.remove(Collide(10))
    a, b = HashSet(objs[:30]), HashSet(objs[20:])
    assert len(a.intersection(b)) == 10
    assert len(a.union(b)) == 50
    assert len(a.difference(b)) == 20


def test_collisions_with_mixed_types():
    # Проверяет коллизии между разными типами (Collide и int)
    s = HashSet([Collide(1), 42, Collide(2)])  # hash(42) == 42 тоже коллизия
    assert len(s) == 3
    assert 42 in s and Collide(1) in s


# ---------- property-style сравнение со встроенным set
@pytest.mark.parametrize("seed", range(10))
def test_matches_builtin_set_on_random_data(seed):
    #2000 случайных операций сравниваются со встроенным set
    rnd = random.Random(seed)
    ours, ref = HashSet(), set()
    for _ in range(2000):
        x = rnd.randint(-200, 200)
        op = rnd.random()
        if op < 0.6:
            ours.add(x)
            ref.add(x)
        elif op < 0.85:
            if x in ref:
                ours.remove(x)
                ref.remove(x)
            else:
                with pytest.raises(KeyError):
                    ours.remove(x)
        else:
            assert (x in ours) == (x in ref)
        assert len(ours) == len(ref)
    assert set(ours) == ref

    other_list = [rnd.randint(-200, 200) for _ in range(rnd.randint(0, 300))]
    other_ref = set(other_list)
    other = HashSet(other_list)
    assert set(ours.union(other)) == ref | other_ref
    assert set(ours.intersection(other)) == ref & other_ref
    assert set(ours.difference(other)) == ref - other_ref
    assert set(ours.union(other_list)) == ref | other_ref
    assert ours.is_subset(other) == (ref <= other_ref)
    assert ours.is_superset(other) == (ref >= other_ref)
    assert ours.intersection(other).is_subset(ours)
    assert ours.union(other).is_superset(other_list)
    assert (ours == other) == (ref == other_ref)


@pytest.mark.parametrize("seed", range(5))
def test_matches_builtin_set_mixed_types(seed):
    rnd = random.Random(seed)
    pool = [None, True, False, 0, 1, 1.0, 0.0, 2.5, "a", "b", "", (1, 2), (1,), frozenset({1}), b"x"]
    data = [rnd.choice(pool) for _ in range(100)]
    ours, ref = HashSet(data), set(data)
    assert len(ours) == len(ref)
    assert all(x in ours for x in ref)
    assert set(ours) == ref
