from master.database import obtener_lider
lider = obtener_lider()
if lider:
    print(f"Lider actual: Nodo {lider['nodo_id']} ({lider['nodo_hostname']})")
    print(f"URL: {lider['nodo_url']}")
else:
    print("Sin lider")
