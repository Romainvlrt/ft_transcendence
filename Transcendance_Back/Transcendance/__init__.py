import random

# Créer un tableau de 50 nombres aléatoires
numbers = [random.randint(1, 100) for _ in range(50)]

# Trier le tableau dans l'ordre croissant
numbers.sort()

print(numbers)
