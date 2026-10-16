class Shape:                                   # ABSTRACTION: hide details, expose interface
    def area(self):
        raise NotImplementedError

class Rect(Shape):                             # INHERITANCE: reuse/extend parent
    def __init__(self, w, h):
        self.__w, self.__h = w, h              # ENCAPSULATION: private data
    def area(self):                            # POLYMORPHISM: same method, different behavior
        return self.__w * self.__h

class Circle(Shape):
    def __init__(self, r):
        self._r = r
    def area(self):
        return 3.14159 * self._r ** 2

for s in (Rect(2, 3), Circle(1)):
    print(type(s).__name__, s.area())