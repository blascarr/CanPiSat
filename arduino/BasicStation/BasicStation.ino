#include <RH_RF69.h>
#include <SPI.h>

#define CANSAT 1
#define BASE 2

// Connection Pins
#define RFM69_INT 3 // DIO0
#define RFM69_CS 10 // NSS
#define RFM69_RST 4 // RESET
#define RF69_FREQ 868.0

RH_RF69 driver(RFM69_CS, RFM69_INT);

uint8_t data[] = "And hello back to you";
uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];

// Defaults after init are 868.0MHz, modulation GFSK_Rb250Fd250, +13dbM (for
// low power module)

void resetRadio() {
	pinMode(RFM69_RST, OUTPUT);
	digitalWrite(RFM69_RST, LOW);
	delay(100);
	digitalWrite(RFM69_RST, HIGH);
	delay(100);
	digitalWrite(RFM69_RST, LOW);
	delay(100);
}

void setup() {
	Serial.begin(9600);
	while (!Serial)
		;

	resetRadio();

	if (!driver.init())
		Serial.println("init failed");

	driver.setTxPower(20, true);
	driver.setFrequency(868.0);
	driver.setCADTimeout(50);
	driver.setModemConfig(RH_RF69::GFSK_Rb250Fd250);

	uint8_t version = driver.spiRead(0x10);
	Serial.print("Versión RFM69 detectada: 0x");
	Serial.println(version, HEX);
	if (version == 0x24) {
		Serial.println("El módulo está funcionando correctamente ✅");
	} else {
		Serial.println("Versión inesperada. Puede haber problema de "
					   "comunicación o daño ❌");
	}

	Serial.println("Radio Base STATION Initialized");
	delay(2000);
}

void loop() {
	if (driver.available()) {

		uint8_t len = sizeof(buf);
		uint8_t from;
		if (driver.recv(buf, &len)) {
			Serial.print("Respuesta: ");
			for (uint8_t i = 0; i < len; i++) {
				Serial.print((char)buf[i]);
			}
			Serial.println();
		}
	}
}