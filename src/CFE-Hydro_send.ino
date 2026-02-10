/*
   Autor : André Luiz Rocha
   PID   : CFE-Hydro_send.ino
   Placa : ESP32 Dev Module
   Função: Enviar dados sensoriados para o broker MQTT
   Date  : 06/02/2026 - 07:36h
   L.U.  : 09/02/2026 - 23:54h
   Referências:
      - WifiManager : https://github.com/tzapu/WiFiManager
      - PubSubClient: https://github.com/knolleary/pubsubclient
      - NTPClient   : https://github.com/arduino-libraries/NTPClient
      - CFE-Hydro   : https://github.com/bps90/cfe-hydro

   Pendências:
      - Calibrar os sensores
      -
*/

// IMPORTA BIBLIOTECAS ==================================
// #include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiManager.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <EEPROM.h>
#include <WiFiUdp.h>
#include <NTPClient.h>

// DEFINE VARIÁVEIS =====================================
// WiFi Configuration
// const char* wifi_ssid = "Wifi_Client";
// const char* wifi_password = "Wifi_Password";

// MQTT Configuration
const char* mqtt_server = "test.mosquitto.org";
const int mqtt_port = 1883;
const char* mqtt_topic_data = "cfe-hydro/data";
const char* mqtt_topic_status = "cfe-hydro/status";
const char* mqtt_topic_heartbeat = "cfe-hydro/heartbeat";
const char* mqtt_client_id = "ESP32_Hydro_01";

// Configura intervalos
const unsigned long sampling_interval = 30000;     // 30 seconds
const unsigned long transmission_interval = 60000; // 60 seconds
const unsigned long heartbeat_interval = 20000;    // 20 seconds

// Variáveis Globais
unsigned long last_sample_time = 0;
unsigned long last_transmission_time = 0;
unsigned long last_heartbeat_time = 0;
unsigned long lastNTPUpdate = 0;
const unsigned long ntpUpdateInterval = 3600000; // 1 hour

bool wifi_connected = false;
bool ntpInitialized = false;

// ESTANCIA OBJETOS =====================================
// WiFi / MQTT
WiFiClient espClient;
PubSubClient client(espClient);

// NTP
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", -10800, 60000); // UTC-3 (Brasília): -3 * 3600 = -10800

// DEFINE PINOS =========================================
#define DHTPIN 15
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

#define PH_SENSOR_PIN 34
#define TDS_SENSOR_PIN 35
#define DO_SENSOR_PIN 32
#define STATUS_LED 2

// ADC Configuration
#define ADC_RESOLUTION 4095.0
#define VREF 3.3
#define ADC_SAMPLES 10

// ESTRUTURAS DE DADOS ==================================
// Data Structures
enum SensorType {
   TEMPERATURE = 0,
   PH,
   ELECTRICAL_CONDUCTIVITY,
   DISSOLVED_OXYGEN
};

enum InterpolationType {
   LINEAR = 0,
   LOGARITHMIC,
   POLYNOMIAL,
   SIGMOIDAL
};

struct SensorData {
   SensorType type;
   float value;
   unsigned long timestamp;  // Timestamp em MILISSEGUNDOS
   InterpolationType interpolation;
   String unit;
   String description;
   float optimal_min;
   float optimal_max;
   bool valid;
};

struct CalibrationData {
   float ph_calibration_offset;
   float ec_calibration_factor;
   float do_calibration_factor;
   uint8_t checksum;
};

SensorData current_readings[4];
CalibrationData calibration = {0.0, 1.0, 1.0, 0};

// ================= HELPER FUNCTIONS =================
String sensorTypeToString(SensorType type) {
   switch(type) {
      case TEMPERATURE: return "temperature";
      case PH: return "ph";
      case ELECTRICAL_CONDUCTIVITY: return "ec";
      case DISSOLVED_OXYGEN: return "do";
      default: return "unknown";
   }
}

String interpolationTypeToString(InterpolationType type) {
   switch(type) {
      case LINEAR: return "linear";
      case LOGARITHMIC: return "logarithmic";
      case POLYNOMIAL: return "polynomial";
      case SIGMOIDAL: return "sigmoidal";
      default: return "linear";
   }
}

float rnd_float(int min, int max) {
   return min + (float)random(1000)/999.0 * (max - min);
}

// ================= TIMESTAMP FUNCTIONS =================
// Função para obter timestamp atual em MILISSEGUNDOS (epoch time * 1000)
unsigned long getCurrentTimestamp() {
    if (ntpInitialized) {
        // Atualizar o cliente NTP para obter dados atualizados
        timeClient.update();
        
        // Retorna epoch time em MILISSEGUNDOS (segundos * 1000)
        unsigned long epochSeconds = timeClient.getEpochTime();
        unsigned long timestampMs = epochSeconds * 1000UL;

/*
        // DEBUG: Mostrar ambos os formatos
        Serial.print("Timestamp (segundos): ");
        Serial.print(epochSeconds);
        Serial.print(" -> (milissegundos): ");
        Serial.println(timestampMs);
*/

        return timestampMs;
    } else {
        // Fallback: milissegundos desde a inicialização
        unsigned long timestamp = millis();
        Serial.print("NTP não inicializado. Usando millis(): ");
        Serial.println(timestamp);
        return timestamp;
    }
}

// Função para obter timestamp em SEGUNDOS (para debug)
unsigned long getCurrentTimestampSeconds() {
    if (ntpInitialized) {
        timeClient.update();
        return timeClient.getEpochTime();
    } else {
        return millis() / 1000;
    }
}

// Função para formatar timestamp em string usando NTPClient
String formatTimestamp() {
    if (ntpInitialized) {
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
    } else {
        // Se NTP não estiver inicializado, mostrar tempo desde inicialização
        unsigned long seconds = millis() / 1000;
        unsigned long minutes = seconds / 60;
        unsigned long hours = minutes / 60;
        seconds %= 60;
        minutes %= 60;
        
        char buffer[50];
        snprintf(buffer, sizeof(buffer), "%02lu:%02lu:%02lu (desde inicialização)", hours, minutes, seconds);
        return String(buffer);
    }
}

// Função para inicializar NTP
bool initNTP() {
    Serial.println("Inicializando NTP...");
    timeClient.begin();
    timeClient.setTimeOffset(-10800); // UTC-3 para Brasília
    
    int attempts = 0;
    while (attempts < 10) {
        if (timeClient.update()) {
            ntpInitialized = true;
            Serial.println("NTP inicializado com sucesso!");
            
            // Mostrar a data e hora atuais
            Serial.print("Data/hora atual (UTC-3): ");
            Serial.println(formatTimestamp());

/*
            // Mostrar timestamp atual
            Serial.print("Timestamp atual (s): ");
            Serial.println(getCurrentTimestampSeconds());
            Serial.print("Timestamp atual (ms): ");
            Serial.println(getCurrentTimestamp());
*/

            return true;
        }
        delay(1000);
        attempts++;
    }
    
    Serial.println("Falha ao inicializar NTP!");
    return false;
}

// ================= SENSOR FUNCTIONS =================
void initSensors() {
    Serial.println("Inicializando sensores...");
    dht.begin();
    delay(2000);
    
    pinMode(PH_SENSOR_PIN, INPUT);
    pinMode(TDS_SENSOR_PIN, INPUT);
    pinMode(DO_SENSOR_PIN, INPUT);
    
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);
    
    Serial.println("Sensores inicializados");
}

float readAnalogAverage(int pin) {
    float sum = 0;
    for (int i = 0; i < ADC_SAMPLES; i++) {
        sum += analogRead(pin);
        delay(2);
    }
    return sum / ADC_SAMPLES;
}

float readTemperature() {
    float temp = dht.readTemperature();
    if (isnan(temp)) {
        Serial.println("Erro na leitura do DHT22!");
        return -999.0;
    }
    Serial.print("Temperatura: ");
    Serial.print(temp);
    Serial.println(" °C");
    return temp;
}

float readPH() {
    float analogValue = readAnalogAverage(PH_SENSOR_PIN);
    float voltage = analogValue * VREF / ADC_RESOLUTION;
    
    // Simulação de leitura de pH
    float ph_value = rnd_float(5.5, 7.8);
    
    Serial.print("pH: ");
    Serial.print(ph_value, 2);
    Serial.print(" (Voltagem: ");
    Serial.print(voltage, 3);
    Serial.println("V)");
    
    return ph_value;
}

float readElectricalConductivity() {
    float analogValue = readAnalogAverage(TDS_SENSOR_PIN);
    float voltage = analogValue * VREF / ADC_RESOLUTION;
    
    // Simulação de leitura de condutividade
    float ec_value = rnd_float(0.000, 5.000);
    
    Serial.print("EC: ");
    Serial.print(ec_value, 3);
    Serial.print(" mS/cm (Voltagem: ");
    Serial.print(voltage, 3);
    Serial.println("V)");
    
    return ec_value;
}

float readDissolvedOxygen() {
    float analogValue = readAnalogAverage(DO_SENSOR_PIN);
    float voltage = analogValue * VREF / ADC_RESOLUTION;
    
    // Simulação de leitura de oxigênio dissolvido
    float do_value = rnd_float(1.000, 5.000);
    
    Serial.print("OD: ");
    Serial.print(do_value, 2);
    Serial.print(" mg/L (Voltagem: ");
    Serial.print(voltage, 3);
    Serial.println("V)");
    
    return do_value;
}

void readAllSensors() {
    Serial.println("\n=== LEITURA DE SENSORES ===");

    // Obter timestamp atual em MILISSEGUNDOS
    unsigned long current_timestamp = getCurrentTimestamp();
    
    // Mostrar o timestamp atual
    Serial.print("Data/hora local: ");
    Serial.println(formatTimestamp());

    // Temperatura
    float temperature = readTemperature();
    current_readings[0] = {
        TEMPERATURE,
        temperature,
        current_timestamp,  // Em MILISSEGUNDOS
        LINEAR,
        "°C",
        "Temperatura da solução nutritiva",
        18.0,
        25.0,
        !isnan(temperature) && temperature > -900.0
    };

    // pH
    float ph_value = readPH();
    current_readings[1] = {
        PH,
        ph_value,
        current_timestamp,  // Em MILISSEGUNDOS
        LOGARITHMIC,
        "pH",
        "Potencial hidrogeniônico - escala logarítmica",
        5.5,
        6.5,
        ph_value >= 0 && ph_value <= 14
    };

    // Condutividade Elétrica
    float ec_value = readElectricalConductivity();
    current_readings[2] = {
        ELECTRICAL_CONDUCTIVITY,
        ec_value,
        current_timestamp,  // Em MILISSEGUNDOS
        POLYNOMIAL,
        "mS/cm",
        "Condutividade elétrica - variação não linear",
        1.0,
        3.0,
        ec_value >= 0 && ec_value < 10.0
    };

    // Oxigênio Dissolvido
    float do_value = readDissolvedOxygen();
    current_readings[3] = {
        DISSOLVED_OXYGEN,
        do_value,
        current_timestamp,  // Em MILISSEGUNDOS
        POLYNOMIAL,
        "mg/L",
        "Oxigênio dissolvido - comportamento polinomial",
        5.0,
        8.0,
        do_value >= 0 && do_value <= 20.0
    };

    int valid_count = 0;
    for (int i = 0; i < 4; i++) {
        if (current_readings[i].valid) valid_count++;
    }

    Serial.print("Leituras válidas: ");
    Serial.print(valid_count);
    Serial.println("/4");
    Serial.println("=== LEITURA CONCLUÍDA ===\n");
}

void conecta_WiFi() {
   WiFiManager wm;
   bool res;
   res = wm.autoConnect("CFE-Hydro_send");
   if(!res) {
      // wm.resetSettings();
      Serial.println("Falha ao conectar ao WiFi.");
      ESP.restart();
      wifi_connected = false;
   }
   else {
      Serial.println("Conectado ao Wifi!");
      Serial.print(WiFi.SSID());  
      Serial.print("  IP: ");
      Serial.println(WiFi.localIP()); 
      wifi_connected = true;
   }
} // end conectaWiFi()

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Mensagem MQTT [");
    Serial.print(topic);
    Serial.print("]: ");
    
    String message;
    for (int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    Serial.println(message);
}

void reconnect_mqtt() {
    while (!client.connected()) {
        Serial.print("Conectando ao MQTT...");
        String clientId = "CFE-HYDRO-";
        clientId += String(random(0xFFFF), HEX);
        
        if (client.connect(clientId.c_str())) {
            Serial.println("conectado!");
            digitalWrite(STATUS_LED, HIGH);
        } else {
            Serial.print("falhou, rc=");
            Serial.print(client.state());
            Serial.println(" tentando novamente em 5 segundos");
            digitalWrite(STATUS_LED, LOW);
            delay(5000);
        }
    }
}

// ============== FUNÇÕES DE PREPARAÇÃO DE DADOS ==============
String prepareCFEHYDROData() {
    StaticJsonDocument<2048> doc;
    
    doc["protocol"] = "CFE-HYDRO";
    doc["version"] = "1.0";
    doc["device_id"] = mqtt_client_id;
    doc["transmission_timestamp"] = getCurrentTimestamp(); // Em MILISSEGUNDOS
    doc["sampling_interval"] = sampling_interval;
    doc["transmission_interval"] = transmission_interval;
    doc["timezone"] = "UTC-3";

    JsonArray readings = doc.createNestedArray("readings");
    
    for (int i = 0; i < 4; i++) {
        if (current_readings[i].valid) {
            JsonObject reading = readings.createNestedObject();
            reading["sensor_type"] = sensorTypeToString(current_readings[i].type);
            reading["value"] = current_readings[i].value;
            reading["timestamp"] = current_readings[i].timestamp; // Em MILISSEGUNDOS
            reading["interpolation"] = interpolationTypeToString(current_readings[i].interpolation);
            
            // Adicionar metadados
            JsonObject metadata = reading.createNestedObject("metadata");
            metadata["unit"] = current_readings[i].unit;
            metadata["description"] = current_readings[i].description;
            metadata["optimal_min"] = current_readings[i].optimal_min;
            metadata["optimal_max"] = current_readings[i].optimal_max;
        }
    }

    doc["system"]["free_heap"] = ESP.getFreeHeap();
    doc["system"]["wifi_rssi"] = WiFi.RSSI();
    doc["system"]["uptime"] = millis() / 1000;
    
    String output;
    serializeJson(doc, output);
    
    Serial.println("=== DADOS CFE-HYDRO PREPARADOS ===");
    Serial.print("Tamanho: ");
    Serial.print(output.length());
    Serial.println(" bytes");
    
/*
    // DEBUG: Mostrar timestamps enviados
    for (int i = 0; i < 4; i++) {
        if (current_readings[i].valid) {
            Serial.print(sensorTypeToString(current_readings[i].type));
            Serial.print(" timestamp: ");
            Serial.print(current_readings[i].timestamp);
            Serial.print(" ms (");
            Serial.print(current_readings[i].timestamp / 1000);
            Serial.println(" s)");
        }
    }
*/    
    return output;
}

String prepareHeartbeatMessage() {
    StaticJsonDocument<256> doc;
    doc["device"] = mqtt_client_id;
    doc["uptime"] = millis() / 1000;
    doc["free_heap"] = ESP.getFreeHeap();
    doc["rssi"] = WiFi.RSSI();
    
    String output;
    serializeJson(doc, output);
    return output;
}

// =============== ESTANCIA FUNÇÕES ================
void conecta_WiFi();

// ================= ARDUINO SETUP =================
void setup() {
   Serial.begin(115200);
   delay(1000);
    
   Serial.println("\n=== SISTEMA CFE-HYDRO ===");
   Serial.println("Inicializando...");
    
   pinMode(STATUS_LED, OUTPUT);
   digitalWrite(STATUS_LED, LOW);
    
   initSensors();
    
   // WIFI -----------------------------------------
   // WiFi.mode(WIFI_STA);
   // setup_wifi();
   conecta_WiFi();

   if (wifi_connected) {
      client.setServer(mqtt_server, mqtt_port);
      client.setCallback(mqtt_callback);
      client.setBufferSize(2048);
      initNTP();
   }
    
   Serial.println("\n=== CONFIGURAÇÃO DO SISTEMA ===");
   Serial.println("Protocolo: CFE-HYDRO");
   Serial.print("Intervalo de leitura: ");
   Serial.print(sampling_interval / 1000);
   Serial.println(" segundos");
   Serial.print("Intervalo de transmissão: ");
   Serial.print(transmission_interval / 1000);
   Serial.println(" segundos");
   Serial.print("Timestamp enviado em: MILISSEGUNDOS");
   Serial.println("\== SISTEMA PRONTO ===\n");
} //  end setup()

// ================= ARDUINO LOOP =================
void loop() {
   unsigned long current_time = millis();
    
   // Atualizar NTP periodicamente
   if (current_time - lastNTPUpdate >= ntpUpdateInterval || lastNTPUpdate == 0) {
      if (wifi_connected && ntpInitialized) {
         if (timeClient.update()) {
            Serial.print("NTP atualizado: ");
            Serial.println(formatTimestamp());
            Serial.print("Novo timestamp (ms): ");
            Serial.println(getCurrentTimestamp());
         }
         lastNTPUpdate = current_time;
      }
   }
    
   // Ler sensores periodicamente
   if (current_time - last_sample_time >= sampling_interval) {
      readAllSensors();
      last_sample_time = current_time;
   }
    
   // Enviar dados periodicamente
   if (current_time - last_transmission_time >= transmission_interval) {
      if (wifi_connected && client.connected()) {
         Serial.println("\n>>> ENVIANDO DADOS DOS SENSORES VIA CFE-HYDRO <<<");
            
         String sensor_data = prepareCFEHYDROData();
         if (client.publish(mqtt_topic_data, sensor_data.c_str())) {
            Serial.println("✓ Dados enviados com sucesso!");
         } else {
            Serial.println("✗ Falha no envio dos dados");
         }
            
         last_transmission_time = current_time;
      }
   }
    
   // Heartbeat
   if (current_time - last_heartbeat_time >= heartbeat_interval) {
      if (wifi_connected && client.connected()) {
         String heartbeat = prepareHeartbeatMessage();
         client.publish(mqtt_topic_heartbeat, heartbeat.c_str());
         last_heartbeat_time = current_time;
      }
   }
    
   // LED de status
   static unsigned long last_blink = 0;
   if (current_time - last_blink > 1000) {
      digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
      last_blink = current_time;
   }
    
   // Manter conexão MQTT
   if (wifi_connected) {
      if (!client.connected()) {
         reconnect_mqtt();
      }
      client.loop();
   }
    
   delay(100);
} // end loop()