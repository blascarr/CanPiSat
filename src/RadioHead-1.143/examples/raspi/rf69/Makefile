
# Makefile
# Example for RH_RF69 on Raspberry Pi
# Requires pigpio to be installed: http://abyz.me.uk/rpi/pigpio/

CC            = g++
CFLAGS        = -DRASPBERRY_PI -pthread
LIBS          = -lpigpio -lrt
RADIOHEADBASE = ../../..
INCLUDE       = -I$(RADIOHEADBASE)


all: rf69_client base_rf69_client

#RasPi.o: $(RADIOHEADBASE)/RHutil/RasPi.cpp
#	$(CC) $(CFLAGS) -c $(RADIOHEADBASE)/RHutil/RasPi.cpp $(INCLUDE)

RasPi.o: $(RADIOHEADBASE)/RHutil_pigpio/RasPi.cpp
	$(CC) $(CFLAGS) -c $(RADIOHEADBASE)/RHutil_pigpio/RasPi.cpp $(INCLUDE)

rf69_client.o: rf69_client.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

base_rf69_client.o: base_rf69_client.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

RH_RF69.o: $(RADIOHEADBASE)/RH_RF69.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

RHReliableDatagram.o: $(RADIOHEADBASE)/RHReliableDatagram.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

RHDatagram.o: $(RADIOHEADBASE)/RHDatagram.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

RHHardwareSPI.o: $(RADIOHEADBASE)/RHHardwareSPI.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

RHSPIDriver.o: $(RADIOHEADBASE)/RHSPIDriver.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

RHGenericDriver.o: $(RADIOHEADBASE)/RHGenericDriver.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

RHGenericSPI.o: $(RADIOHEADBASE)/RHGenericSPI.cpp
	$(CC) $(CFLAGS) -c $(INCLUDE) $<

rf69_client: rf69_client.o RH_RF69.o RHReliableDatagram.o RHDatagram.o RasPi.o RHHardwareSPI.o RHGenericDriver.o RHGenericSPI.o RHSPIDriver.o
	$(CC) $^ $(LIBS) -o rf69_client

base_rf69_client: base_rf69_client.o RH_RF69.o RasPi.o RHHardwareSPI.o RHGenericDriver.o RHGenericSPI.o RHSPIDriver.o
	$(CC) $^ $(LIBS) -o base_rf69_client

clean:
	rm -rf *.o rf69_client base_rf69_client
