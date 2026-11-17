"""
AquaWaterTech - Simulador de Sensores IoT (ESP32)
Este script gera medições simuladas de Oxigênio Dissolvido, pH e Temperatura
e as envia via HTTP POST para a API do AquaWaterTech.
"""

import sys
import time
import random
import urllib.request
import json

DEFAULT_API_URL = "http://localhost:5000/api/medicoes"

def gerar_leitura_simulada(com_anomalia=False):
    """
    Gera leituras normais ou com anomalias propositais para testar os alertas.
    """
    if com_anomalia:
        # Gera valores anômalos (ex: oxigênio baixo ou pH extremo)
        tipo_anomalia = random.choice(['oxigenio_baixo', 'ph_alto', 'temperatura_alta'])
        if tipo_anomalia == 'oxigenio_baixo':
            oxigenio = round(random.uniform(2.0, 3.8), 2)  # Crítico (< 4.0 mg/L)
            ph = round(random.uniform(6.8, 7.8), 2)
            temperatura = round(random.uniform(25.0, 29.0), 1)
        elif tipo_anomalia == 'ph_alto':
            oxigenio = round(random.uniform(5.0, 7.5), 2)
            ph = round(random.uniform(8.8, 9.5), 2)  # Crítico (> 8.5)
            temperatura = round(random.uniform(25.0, 29.0), 1)
        else:
            oxigenio = round(random.uniform(5.0, 7.0), 2)
            ph = round(random.uniform(6.8, 7.8), 2)
            temperatura = round(random.uniform(33.0, 36.5), 1)  # Crítico (> 32.0 °C)
    else:
        # Valores ideais para cultivo de peixes
        oxigenio = round(random.uniform(5.0, 8.5), 2)
        ph = round(random.uniform(6.8, 7.8), 2)
        temperatura = round(random.uniform(26.0, 29.5), 1)

    return oxigenio, ph, temperatura

def enviar_medicao(api_url, tanque_id, oxigenio, ph, temperatura):
    payload = {
        "tanque_id": tanque_id,
        "oxigenio_dissolvido": oxigenio,
        "ph": ph,
        "temperatura": temperatura,
        "origem": "simulador_esp32"
    }

    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        api_url,
        data=req_data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            alertas = res_json.get('alertas_gerados', [])
            print(f"[{time.strftime('%H:%M:%S')}] Medição enviada: OD={oxigenio} mg/L | pH={ph} | Temp={temperatura}°C")
            if alertas:
                print(f"   ⚠️ ATENÇÃO: {len(alertas)} ALERTA(S) DISPARADO(S)!")
                for a in alertas:
                    print(f"      -> Parâmetro: {a['parametro']} | Valor: {a['valor_observado']} | Limite: {a['limite_acionado']}")
            else:
                print("   ✅ Parâmetros normais (sem alertas).")
            return True
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Falha ao enviar medição: {e}")
        return False

def main():
    print("=" * 60)
    print("   AquaWaterTech - Simulador IoT (ESP32)")
    print("=" * 60)

    tanque_id = 1
    if len(sys.argv) > 1:
        try:
            tanque_id = int(sys.argv[1])
        except ValueError:
            print("ID do tanque inválido. Usando ID 1 por padrão.")

    print(f"Alvo: {DEFAULT_API_URL}")
    print(f"Tanque ID: {tanque_id}")
    print("Pressione Ctrl+C para encerrar o simulador a qualquer momento.\n")

    contador = 0
    while True:
        contador += 1
        # A cada 4 medições, simula uma medição anômala para disparar alertas
        anomalia = (contador % 4 == 0)
        ox, ph, temp = gerar_leitura_simulada(com_anomalia=anomalia)
        enviar_medicao(DEFAULT_API_URL, tanque_id, ox, ph, temp)
        time.sleep(5)

if __name__ == '__main__':
    main()
