class Pizza:
    toppings: list

    def is_vegetarian(self):
        return all(t.vegetarian for t in self.toppings)
