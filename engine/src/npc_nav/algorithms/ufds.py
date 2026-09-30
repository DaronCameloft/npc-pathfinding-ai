"""UFDS — Union-Find Disjoint Sets para detectar regiones conectadas.

Referencia: Tarjan, R. E. (1975). Efficiency of a good but not linear set
union algorithm. Journal of the ACM 22(2), 215-225.

Pseudocódigo
------------
encontrar(x):
1. subir por los padres hasta la raíz (el representante del conjunto)
2. compresión de caminos: colgar cada nodo recorrido directamente de la raíz

unir(a, b):
3. ra = encontrar(a); rb = encontrar(b); si son iguales, ya están unidos
4. unión por rango: colgar el árbol más bajo del más alto

regiones_conectadas(grafo):
5. crear un conjunto por vértice
6. para cada arista (u, v): unir(u, v)
7. dos vértices están en la misma región si y solo si tienen la misma raíz

Propiedades
-----------
- Cada operación cuesta O(α(V)) amortizado (α es la inversa de Ackermann,
  prácticamente constante). Construir las regiones cuesta O(E · α(V)).
- Permite descartar en O(1) una consulta cuyo destino está en otra región
  (brc201d tiene 167) antes de gastar una búsqueda completa.
- Describe la conectividad del mapa ORIGINAL: si se bloquean celdas hay que
  volver a comprobarla.
"""


class UFDS:
    def __init__(self):
        self.padre = {}
        self.rango = {}
        self.tamano = {}
        self.num_conjuntos = 0

    def agregar(self, x):
        if x not in self.padre:
            self.padre[x] = x
            self.rango[x] = 0
            self.tamano[x] = 1
            self.num_conjuntos += 1

    def encontrar(self, x):
        raiz = x
        while self.padre[raiz] != raiz:                        # 1.
            raiz = self.padre[raiz]
        while self.padre[x] != raiz:                           # 2. compresión
            self.padre[x], x = raiz, self.padre[x]
        return raiz

    def unir(self, a, b) -> bool:
        ra, rb = self.encontrar(a), self.encontrar(b)          # 3.
        if ra == rb:
            return False
        if self.rango[ra] < self.rango[rb]:                    # 4. unión por rango
            ra, rb = rb, ra
        self.padre[rb] = ra
        self.tamano[ra] += self.tamano[rb]
        if self.rango[ra] == self.rango[rb]:
            self.rango[ra] += 1
        self.num_conjuntos -= 1
        return True

    def mismo_conjunto(self, a, b) -> bool:
        return self.encontrar(a) == self.encontrar(b)


def regiones_conectadas(grafo: dict) -> tuple[UFDS, list[int]]:
    """Recibe una lista de adyacencia {nodo: [vecinos]}.

    Devuelve la estructura UFDS y los tamaños de las regiones, de mayor a menor.
    """
    ufds = UFDS()
    for nodo in grafo:                                         # 5.
        ufds.agregar(nodo)
    for nodo, vecinos in grafo.items():                        # 6.
        for vecino in vecinos:
            ufds.unir(nodo, vecino)
    tamanos = sorted((ufds.tamano[nodo] for nodo in grafo      # 7.
                      if ufds.encontrar(nodo) == nodo), reverse=True)
    return ufds, tamanos
