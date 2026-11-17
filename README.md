# AquaWaterTech 🐟💧

**Sistema IoT de Monitoramento da Qualidade da Água para Piscicultura**

Projeto desenvolvido para o Instituto Federal de Rondônia (IFRO) — Campus Porto Velho Calama.

---

## 🎯 Objetivo

O **AquaWaterTech** permite monitorar a qualidade da água em tanques de piscicultura coletando dados em tempo real de **Oxigênio Dissolvido (OD)**, **pH** e **Temperatura**. O sistema gera alertas automáticos caso algum parâmetro ultrapasse os limites configurados e garante o isolamento seguro dos dados de cada produtor.

---

## 🚀 Tecnologias

- **Backend:** Python 3.12 + Flask
- **Banco de Dados:** SQLAlchemy ORM (SQLite para desenvolvimento / compatível com PostgreSQL)
- **Autenticação:** Flask-Login com hash seguro de senhas (Werkzeug)
- **Frontend:** HTML5, CSS3 responsivo, Bootstrap 5, Bootstrap Icons e Chart.js
- **IoT & Simulação:** API REST HTTP (JSON) pronta para microcontroladores ESP32 e simulador integrado

---

## 📋 Funcionalidades Implementadas

- **Autenticação e Perfis (RF01, RF02, RF03):** Cadastro de piscicultor, login com verificação de status e encerramento de sessão.
- **Gerenciamento de Tanques (RF04, RF09):** Cadastro, edição, remoção e isolamento total entre produtores.
- **Registro de Medições (RF05):** Ingestão via endpoint REST HTTP (`/api/medicoes`) ou entrada manual para testes.
- **Visualização e Histórico (RF06):** Painel com valores atuais, gráficos temporais em Chart.js e tabela cronológica de amostras.
- **Configuração de Limites de Alerta (RF07):** Definição personalizada de valores mínimos e máximos por tanque e por parâmetro.
- **Central de Alertas (RF08):** Disparo e registro automático de anomalias com possibilidade de resolução pelo piscicultor.
- **Painel Administrativo (RF10):** Consulta de usuários cadastrados e desativação/reativação de contas pelo administrador.

---

## 🛠️ Como Executar o Projeto

### 1. Pré-requisitos
- Python 3.10+ instalado

### 2. Ativar o Ambiente Virtual e Instalar Dependências
```powershell
# Ativar o venv existente
.\venv\Scripts\Activate.ps1

# Ou instalar as dependências
pip install -r requirements.txt
```

### 3. Iniciar o Servidor Flask
```powershell
python run.py
```
A aplicação estará disponível em: `http://localhost:5000`

> **Credenciais iniciais do Administrador:**
> - **E-mail:** `admin@aquawatertech.com`
> - **Senha:** `admin123`

---

## 📡 Simulador de Sensores IoT (ESP32)

Para testar o envio de dados via sensores sem a necessidade do hardware físico:

Com o servidor Flask rodando em um terminal, abra outro terminal e execute:
```powershell
python simulator.py [ID_DO_TANQUE]
```
*(Se omitido, o ID padrão é 1)*. O simulador enviará leituras periódicas e alternará leituras ideais com anomalias propositais para testar o disparo de alertas.

---

## 🧪 Executando os Testes Automatizados

Para executar todos os testes de aceitação (CA01 ao CA10):
```powershell
python -m unittest discover tests
```

