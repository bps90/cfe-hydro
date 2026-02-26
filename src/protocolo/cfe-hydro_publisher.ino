/*
   Autor : André Luiz Rocha
   PID   : cfe-hydro_publisher.ino
   Placa : ESP32 Dev Module
   Função: Enviar dados sensoriados para o broker MQTT
           usando protocolo cfe-hydro.h
   Date  : 25/02/2026 - 19:35h
   L.U.  : 26/02/2026 - 02:10h
   Referências:
      - 
   Pendências:
      - 
*/

// Importa Bibliotecas ========================================
#include <WiFi.h>
#include <PubSubClient.h>
#include "cfe-hydro.h"
#include <WiFiUdp.h>
#include <NTPClient.h>

// Configurações de rede e MQTT ===============================
const char* ssid = "AP DO PAI"; // "SEU_SSID";
const char* password = "Vitor2005#"; // "SUA_SENHA";
const char* mqtt_server = "test.mosquitto.org"; // "BROKER_EXEMPLO.com";
const int mqtt_port = 1883;
const char* mqtt_topic = "cfe-hydro/data";

// Define variáveis ===========================================
const int interval = 60000; // 1 minuto
String timestamp;
float temp = 0.00;
float ph = 0.00;
float ec = 0.00;
float od = 0.00;

// Estancia Funções ===========================================
void setup_wifi();
void reconnect();
float rnd_float(int, int);
String formatTimestamp();

// Estancia Objetos ===========================================
WiFiClient espClient;
PubSubClient mqttClient(espClient);
// NTP
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", -10800, 60000); // UTC-3 (Brasília): -3 * 3600 = -10800

// Configuração estática dos sensores
CFEHydro::SensorConfig sensores[] = {
    {"temperatura", "°C", "Temperatura da Água", 18.0, 30.0, "linear"},
    {"ph", "pH", "Nível de pH", 5.5, 7.0, "logarithmic"},
    {"ec", "mS/cm", "EC", 0.0, 5.0, "polynomial"},
    {"od", "mg/L", "OD", 0.0, 6.0, "polynomial"}
};
int numSensores = sizeof(sensores) / sizeof(sensores[0]);

// Instância do protocolo (modo estático)
CFEHydro hydro("dispositivo_001", 10, 60, sensores, numSensores);

void setup() {
   Serial.begin(115200);

   setup_wifi();
   mqttClient.setServer(mqtt_server, mqtt_port);
   mqttClient.setBufferSize(2048);

   timeClient.begin();
}

void loop() {
   if (!mqttClient.connected()) {
      reconnect();
   }
   mqttClient.loop();

   // SIMULA leituras dos sensores
   timestamp = formatTimestamp();
   temp = rnd_float(23, 28);
   ph = rnd_float(4.5, 6.5);
   ec = rnd_float(1, 3);
   od = rnd_float(1, 5);

   // Exibe valores lidos
   Serial.print("Timestamp: ");
   Serial.print(timestamp);
   Serial.print("  T: ");
   Serial.print(temp, 2);
   Serial.print("  pH: ");
   Serial.print(ph, 2);
   Serial.print("  EC: ");
   Serial.print(ec, 3);
   Serial.print("  OD: ");
   Serial.println(od, 2);

   // Atualiza os valores no objeto
   hydro.updateSensor("temperatura", temp);
   hydro.updateSensor("ph", ph);
   hydro.updateSensor("ec", ec);
   hydro.updateSensor("od", od);
   hydro.setTimestamp(timestamp.c_str());

   // Envia os dados
   if (hydro.send(mqttClient, mqtt_topic)) {
      Serial.println("Dados enviados com sucesso");
   } else {
      Serial.println("Falha no envio");
   }

   delay(interval);
}

void setup_wifi() {
    delay(10);
    Serial.println();
    Serial.print("Conectando ao WiFi ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi conectado");
}

void reconnect() {
    while (!mqttClient.connected()) {
        if (WiFi.status() != WL_CONNECTED) {
            Serial.println("WiFi desconectado. Reconectando...");
            setup_wifi();
        }
        Serial.print("Conectando ao MQTT...");
        String clientId = "ESP32Client-" + String(random(0xffff), HEX);
        if (mqttClient.connect(clientId.c_str())) {
            Serial.println("conectado");
        } else {
            Serial.print("falha, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" tentando novamente em 5s");
            delay(5000);
        }
    }
}

float rnd_float(int min, int max) {
   return min + (float)random(1000)/999.0 * (max - min);
}

// Função para formatar timestamp em string usando NTPClient
String formatTimestamp() {
   // Atualizar o cliente NTP para obter dados atualizados
   timeClient.update();
        
   // Obter a data completa do NTPClient
   String formattedDate = timeClient.getFormattedDate();
        
   // O formato retornado é: "2026-02-06T22:48:00Z"
   // Extrair componentes
   String year = formattedDate.substring(0, 4);
   String month = formattedDate.substring(5, 7);
   String day = formattedDate.substring(8, 10);
   String hour = formattedDate.substring(11, 13);
   String minute = formattedDate.substring(14, 16);
   String second = formattedDate.substring(17, 19);
        
   // Obter milissegundos do sistema
   unsigned long milliseconds = millis() % 1000;
        
   // Formatar no estilo brasileiro: "DD/MM/AAAA HH:MM:SS.mmm"
   String formatted = day + "/" + month + "/" + year + " " + 
                      hour + ":" + minute + ":" + second + ".";
        
   // Adicionar milissegundos com 3 dígitos
   if (milliseconds < 10) {
      formatted += "00";
   } else if (milliseconds < 100) {
      formatted += "0";
   }
   formatted += String(milliseconds);
        
   return formatted;
}
