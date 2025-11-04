lista = ['a' * 283645]

n_paquetes = len(lista[0]) // 200
try:
    n_paquetes = float(n_paquetes)
except ValueError:
    n_paquetes = 0
n_paquetes = round(n_paquetes) + 1

print(n_paquetes)