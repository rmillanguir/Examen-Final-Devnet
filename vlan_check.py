# Script de Consulta de VLAN - Examen Final Devnet

print("--------------------------------------------------")
print("          VERIFICADOR DE RANGOS DE VLAN           ")
print("--------------------------------------------------")

entrada = input("Por favor, ingrese el numero de VLAN a consultar: ").strip()

try:
    vlan = int(entrada)
    if 1 <= vlan <= 1005:
        print(f"\n[RANGO NORMAL] La VLAN {vlan} corresponde al rango normal de VLANs.")
    elif 1006 <= vlan <= 4094:
        print(f"\n[RANGO EXTENDIDO] La VLAN {vlan} corresponde al rango extendido de VLANs.")
    elif vlan == 0 or vlan == 4095:
        print(f"\n[RESERVADO] La VLAN {vlan} es una VLAN reservada del sistema (invalida).")
    else:
        print(f"\n[FUERA DE RANGO] El numero {vlan} no corresponde a una VLAN respectiva (rango valido: 1-4094).")
except ValueError:
    print(f"\n[ERROR] '{entrada}' no es un numero entero valido.")

print("--------------------------------------------------")
