class Dad:
    def son(self):
        print("old son")

class Son(Dad):
    def son(self, name):
        print(f"new son {name}")

dad = Dad()
son = Son()
dad.son()
son.son("jozko")
son.son()