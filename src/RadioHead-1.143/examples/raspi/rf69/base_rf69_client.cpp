#include <RH_RF69.h>
#include <pigpio.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

// Pin Definitions
#define RFM69_CS_PIN 8
#define RFM69_IRQ_PIN 17
#define RFM69_LED 4
#define RFM69_RST 25

// Client and Server Addresses
#define CANSAT 1
#define BASE 2

// RFM96 Configuration
#define RFM69_FREQUENCY 868.00
#define RFM69_TXPOWER 20

// Singleton instance of the radio driver
RH_RF69 rf69(RFM69_CS_PIN, RFM69_IRQ_PIN);

// Main Function
int main(int argc, const char *argv[]) {
	if (gpioInitialise() < 0) {
		// printf( "\n\nRPI rf69_client startup Failed.\n" );
		return 1;
	}

	// printf("\nInicio correcto de rf69_client.\n");
	// printf("CS-> GPIO %d | IRQ-> GPIO %d\n", RFM69_CS_PIN, RFM69_IRQ_PIN);
#ifdef RFM69_LED
	gpioSetMode(RFM69_LED, PI_OUTPUT);
	gpioWrite(RFM69_LED, PI_ON);
	gpioDelay(200000);
	gpioWrite(RFM69_LED, PI_OFF);
#endif

	gpioSetMode(RFM69_RST, PI_OUTPUT);
	gpioWrite(RFM69_RST, PI_ON);
	gpioDelay(500000);
	gpioWrite(RFM69_RST, PI_OFF);
	gpioDelay(500000);

	if (!rf69.init()) {
		printf("\n\nRF69 Driver Failed to initialize.\n\n");
		return 1;
	}

	/* Begin Manager/Driver settings code */
	// printf("\nRFM 69 Settings:\n");
	// printf("Frequency= %d MHz\n", (uint16_t) RFM69_FREQUENCY);
	// printf("Power= %d\n", (uint8_t) RFM69_TXPOWER);
	rf69.setTxPower(RFM69_TXPOWER);
	rf69.setFrequency(RFM69_FREQUENCY);
	rf69.setCADTimeout(50);
	rf69.setModemConfig(RH_RF69::GFSK_Rb250Fd250);

	if (argc < 2) {
		printf("Use with msg: ./rf69_client '<mensaje JSON>'\n");
		return 1;
	}
	const char *message = argv[1];

	if (strlen(message) >= RH_RF69_MAX_MESSAGE_LEN) {
		printf("Message too long. Max : %d bytes\n",
			   RH_RF69_MAX_MESSAGE_LEN - 1);
		return 1;
	}

	char data[RH_RF69_MAX_MESSAGE_LEN];
	strncpy(data, message, sizeof(data));
	data[sizeof(data) - 1] = '\0';

	uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];

	// Send a message to manager_server
#ifdef RFM69_LED
	gpioWrite(RFM69_LED, PI_ON);
#endif
	if (rf69.send((uint8_t *)data, strlen(data))) {
		// rf69.waitPacketSent(); // MUY IMPORTANTE
		printf("✅ Mensaje enviado: %s\n", data);
	} else {
		printf("❌ Fallo en envío.\n");
	}
#ifdef RFM69_LED
	gpioWrite(RFM69_LED, PI_OFF);
#endif
	gpioTerminate();
	return 0;
}
