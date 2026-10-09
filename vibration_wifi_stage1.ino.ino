#include <WiFi.h>
#include <WiFiUdp.h>

const char* ssid = "RIDEGUARD-ESP32";
const char* password = "rideguard123";

WiFiUDP udp;

const int UDP_PORT = 4210;

void setup() {
  Serial.begin(115200);

  WiFi.softAP(ssid, password);

  Serial.println();
  Serial.println("RIDEGUARD ESP32");
  Serial.println("----------------");
  Serial.print("Wi-Fi network: ");
  Serial.println(ssid);

  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.softAPIP());

  udp.begin(UDP_PORT);

  Serial.print("UDP listening on port: ");
  Serial.println(UDP_PORT);
}

void loop() {
  int packetSize = udp.parsePacket();

  if (packetSize) {
    char incomingPacket[100];

    int len = udp.read(incomingPacket, sizeof(incomingPacket) - 1);

    if (len > 0) {
      incomingPacket[len] = '\0';
    }

    Serial.print("Received: ");
    Serial.println(incomingPacket);
  }
}