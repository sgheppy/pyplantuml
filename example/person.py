class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.__cf = ""

    def myfunc(abc):
        print("Hello my name is " + abc.name)

    def myfunc2(abc):
        pass


class Person2(Person):

    def myfunc3(abc):
        print("Hello my name is " + abc.name)

    def myfunc4(abc):
        pass

class Couple():
    def __init__(self):
        self.p1 = Person("an",32)
        self.p2 = Person("mi",45)