import socket

def puerto_en_uso(puerto, host="localhost"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        resultado = s.connect_ex((host, puerto))
        return resultado == 0

# Ejemplo
puerto = 1000
if puerto_en_uso(puerto):
    print(f"El puerto {puerto} está en uso")
else:
    print(f"El puerto {puerto} está libre")



import psutil
def proceso_en_puerto(puerto):
    for conn in psutil.net_connections():
        if conn.laddr.port == puerto:
            try:
                proceso = psutil.Process(conn.pid)
                return proceso.name(), conn.pid
            except:
                return "Proceso desconocido", conn.pid
    return None

# Ejemplo
puerto = 1000
info = proceso_en_puerto(puerto)

if info:
    nombre, pid = info
    if nombre == "rocketbot.exe":
        import webbrowser

        url = "http://localhost:1000/#!/edit/Integrator2"
        webbrowser.open(url)
    print(f"Puerto {puerto} en uso por {nombre} (PID {pid})")
else:
    print(f"Puerto {puerto} no está en uso")