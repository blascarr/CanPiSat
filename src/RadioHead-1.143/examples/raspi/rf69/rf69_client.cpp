#include <pigpio.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <string.h>
#include <RHReliableDatagram.h>
#include <RH_RF69.h>

//Pin Definitions
#define RFM96_CS_PIN 8
#define RFM96_IRQ_PIN 17
#define RFM96_LED 4
#define RFM96_RST 25

//Client and Server Addresses
#define CLIENT_ADDRESS 2
#define SERVER_ADDRESS 1

//RFM96 Configuration
#define RFM96_FREQUENCY  868.00
#define RFM96_TXPOWER 20

// Singleton instance of the radio driver
RH_RF69 rf96(RFM96_CS_PIN, RFM96_IRQ_PIN);

// Class to manage message delivery and receipt, using the driver declared above
RHReliableDatagram manager(rf96, CLIENT_ADDRESS);

//Main Function
int main (int argc, const char* argv[] )
{
  if (gpioInitialise()<0)
  {
    printf( "\n\nRPI rf69_client startup Failed.\n" );
    return 1;
  }

  printf("\nInicio correcto de rf69_client.\n");
  printf("CS-> GPIO %d | IRQ-> GPIO %d\n", RFM96_CS_PIN, RFM96_IRQ_PIN);
#ifdef RFM96_LED
  gpioSetMode(RFM96_LED, PI_OUTPUT);
  gpioWrite(RFM96_LED, PI_ON);
  gpioDelay(200000);
  gpioWrite(RFM96_LED, PI_OFF);
#endif

  gpioSetMode(RFM96_RST, PI_OUTPUT);
  gpioWrite(RFM96_RST, PI_ON);
  gpioDelay(500000);
  gpioWrite(RFM96_RST, PI_OFF);
  gpioDelay(500000);

  if (!rf96.init())
  {
    printf( "\n\nRF96 Driver Failed to initialize.\n\n" );
    return 1;
  }

  /* Begin Manager/Driver settings code */
  printf("\nRFM 96 Settings:\n");
  printf("Frequency= %d MHz\n", (uint16_t) RFM96_FREQUENCY);
  printf("Power= %d\n", (uint8_t) RFM96_TXPOWER);
  printf("Client(This) Address= %d\n", CLIENT_ADDRESS);
  printf("Server Address= %d\n", SERVER_ADDRESS);
  rf96.setTxPower(RFM96_TXPOWER);
  rf96.setFrequency(RFM96_FREQUENCY);
  rf96.setThisAddress(CLIENT_ADDRESS);
  rf96.setHeaderFrom(CLIENT_ADDRESS);
  rf96.setHeaderTo(SERVER_ADDRESS);
  rf96.setCADTimeout(50);
  rf96.setModemConfig(RH_RF69::GFSK_Rb250Fd250);
  /* End Manager/Driver settings code */

  /* Begin Datagram Client Code */
  if (argc < 2) {
    printf("Uso: ./rf69_client '<mensaje JSON>'\n");
    return 1;
  }
  const char* message = argv[1];

  if (strlen(message) >= RH_RF69_MAX_MESSAGE_LEN) {
        printf("Message too long. Max : %d bytes\n", RH_RF69_MAX_MESSAGE_LEN - 1);
        return 1;
   }

  // Dont put this on the stack:
  char data[RH_RF69_MAX_MESSAGE_LEN];
  strncpy( data, message, sizeof( data ));
  data [sizeof( data ) - 1] = '\0';

  uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];

  Serial.println("Sending to rf96_reliable_datagram_server");
  // Send a message to manager_server
#ifdef RFM96_LED
    gpioWrite(RFM96_LED, PI_ON);
#endif
    if (manager.sendtoWait( (uint8_t*)data, strlen(data), SERVER_ADDRESS))
    {
      // Now wait for a reply from the server
      uint8_t len = sizeof(buf);
      uint8_t from;
      if (manager.recvfromAckTimeout(buf, &len, 2000, &from))
      {
	buf[len] = '\0';
	printf("Respuesta del servidor (0x%X): %s\n", from, (char*)buf);
      }
      else
      {
       	printf("No reply, is rf96_reliable_datagram_server running?");
      }
    }
    else{
      printf("sendtoWait failed");
    }
#ifdef RFM96_LED
    gpioWrite(RFM96_LED, PI_OFF);
#endif

  printf( "\nrf96_reliable_datagram_client Tester Ending\n" );
  gpioTerminate();
  return 0;
}

