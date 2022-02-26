#include <stdio.h>  // sscanf
#include <stdlib.h> // atoi
#include <string.h> // strlen
#include <WiFi.h>
#include <WiFiUdp.h>
#include <EEPROM.h>
#include "secret.h"

// Include the AccelStepper library:
#include <AccelStepper.h>
// http://www.airspayce.com/mikem/arduino/AccelStepper/classAccelStepper.html

// UPD client:
// nc -u 192.168.2.164 4210
#define UDP_PORT          4210

#define CMD_GOTO          1 // 1 33 44
#define CMD_STOP          2 // 2
#define CMD_MODE          3
#define CMD_SET           4 // 4 2 400 400
#define CMD_GET           5 // 5 4
#define CMD_EE_READ       6 // 6 0
#define CMD_EE_WRITE      7 // 7 0 55

#define CMD_SUB_SPEED     1
#define CMD_SUB_MAX_SPEED 2
#define CMD_SUB_ACCEL     3
#define CMD_SUB_POS       4

#define POS_COMMAND       0
#define POS_SUB_COMMAND   1

#define POS_MODE          1
#define POS_TARGET_LEFT   1
#define POS_TARGET_RIGHT  2
#define POS_SET_PARAM_L   2
#define POS_SET_PARAM_R   3
#define POS_EE_ADR        1
#define POS_EE_VAL        2

#define MODE_STB          0
#define MODE_START        1
#define MODE_STOP         2
#define MODE_RUN          3

// Right motor pin definitions:
#define motorPin1R  22     // IN1 on the ULN2003 driver
#define motorPin2R  21     // IN2 on the ULN2003 driver
#define motorPin3R  17     // IN3 on the ULN2003 driver
#define motorPin4R  16     // IN4 on the ULN2003 driver
// Left motor pin definitions:
#define motorPin1L  26     // IN1 on the ULN2003 driver
#define motorPin2L  18     // IN2 on the ULN2003 driver
#define motorPin3L  19     // IN3 on the ULN2003 driver
#define motorPin4L  23     // IN4 on the ULN2003 driver

// Define the AccelStepper interface type; 4 wire motor in half step mode:
#define MotorInterfaceType 8

struct Frame {
    char rawData[50];
    int data[10];
    int length = 0;
    int newCommand = 0;
};

// UDP
WiFiUDP UDP;
char packet[255];
char response[255] = "ok\n";
char reply[] = "Packet received!";
struct Frame frame;

// Initialize with pin sequence IN1-IN3-IN2-IN4 for using the AccelStepper library with 28BYJ-48 stepper motor:
AccelStepper stepperL = AccelStepper(MotorInterfaceType, motorPin1L, motorPin3L, motorPin2L, motorPin4L);
AccelStepper stepperR = AccelStepper(MotorInterfaceType, motorPin1R, motorPin3R, motorPin2R, motorPin4R);

struct { 
  unsigned int val = 0;
} eepromdata;
int addr = 0; // only 1 address used to store the random list index

int mode = MODE_STB;

long targetLeft = 0, targetRight = 0;
long currentLeft = 0, currentRight = 0;

void setup() {
  // Configure serial line
  Serial.begin(115200);
  Serial.println("Starting...");
  // flush serial line
  while(Serial.available() > 0) {
    char t = Serial.read();
  }

  // Begin WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  // Connecting to WiFi...
  Serial.print("Connecting to ");
  Serial.print(WIFI_SSID);
  // Loop continuously while WiFi is not connected
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(100);
    Serial.print(".");
  }
  
  // Connected to WiFi
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());
 
  // Begin listening to UDP port
  UDP.begin(UDP_PORT);
  Serial.print("Listening on UDP port ");
  Serial.println(UDP_PORT);

  
  // Init EEPROM
  EEPROM.begin(4);  //Initialize EEPROM
  // Set the maximum steps per second:
  stepperL.setMaxSpeed(1000);
  stepperR.setMaxSpeed(1000);
  // Set the maximum acceleration in steps per second^2:
  stepperL.setAcceleration(200);
  stepperR.setAcceleration(200);
}

void loop() {
  // Receive serial frame if available
  receiveSerialFrame();
  // Receive UDP frame if available
  receiveUDPFrame();
  // Decode command and set variables
  decodeCommand();
  // Handle command received before for motion
  runCommand();
}

void runCommand(){
  int stepL, stepR;
  
  if(mode == MODE_START){
    stepperR.move(targetRight);
    stepperL.move(targetLeft);
    Serial.println("Start.");
    mode = MODE_RUN;
  }
  else if(mode == MODE_RUN){
    stepL = stepperL.run();
    stepR = stepperR.run();
    
    if((stepL == false) and (stepR == false)) mode = MODE_STOP;
  }
  else if(mode == MODE_STOP){
    stepperR.stop();
    stepperL.stop();
    Serial.println("Stop.");
    mode = MODE_STB;
  }
  else if(mode == MODE_STB){
  }
}

void receiveUDPFrame(){
  int packetSize = UDP.parsePacket();
  char delimiter[] = ",; ";
  char *ptr;
  int i = 0;
  // If packet received...
  if (packetSize) {
    Serial.print("UDP: Received packet! Size: ");
    Serial.println(packetSize); 
    frame.length = UDP.read(frame.rawData, 255);
    if (frame.length > 0) frame.rawData[frame.length] = '\0';
    frame.newCommand = 1;
    Serial.print("UDP: Packet received: ");
    Serial.println(frame.rawData);

    // Convert string raw frame to int array
    ptr = strtok(frame.rawData, delimiter);
    while(ptr != NULL) {
      frame.data[i] = atoi(ptr);
      ptr = strtok(NULL, delimiter);
      i++;
    }
    frame.length = i;
  }
}

void decodeCommand(){
  // If a new frame was received
  if(frame.newCommand == 1){
    //Serial.println("New command received");
    //Serial.println("Frame length ok.");
    // Handle data in frame depending on command
    if(frame.data[POS_COMMAND] == CMD_GOTO){
      Serial.println("Goto.");
      targetLeft = frame.data[POS_TARGET_LEFT];
      targetRight = frame.data[POS_TARGET_RIGHT];
      mode = MODE_START;
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_STOP){
      Serial.println("Stop");
      mode = MODE_STOP;
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_MODE){
      Serial.print("MODE: ");
      Serial.println(frame.data[POS_MODE]);
      mode = frame.data[POS_MODE];
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_EE_READ){
      Serial.print("EEPROM value: ");
      EEPROM.get(frame.data[POS_EE_ADR], eepromdata);
      Serial.println(eepromdata.val);
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_EE_WRITE){
      Serial.print("Writing EEPROM value: ");
      Serial.print(frame.data[POS_EE_VAL]);
      Serial.print(" at adr: ");
      Serial.println(frame.data[POS_EE_ADR]);
      eepromdata.val = frame.data[POS_EE_VAL];
      EEPROM.put(frame.data[POS_EE_ADR], eepromdata);
      EEPROM.commit();    //Store data to EEPROM
      delay(100);
      sendUDP("ok\n");
    }
    else if(frame.data[POS_COMMAND] == CMD_SET){
      if(frame.data[POS_SUB_COMMAND] == CMD_SUB_SPEED){
        Serial.print("set speed");
        stepperL.setSpeed(frame.data[POS_SET_PARAM_L]);
        stepperR.setSpeed(frame.data[POS_SET_PARAM_R]);
        sendUDP("ok\n");
      }
      else if(frame.data[POS_SUB_COMMAND] == CMD_SUB_MAX_SPEED){
        Serial.print("set max speed");
        stepperL.setMaxSpeed(frame.data[POS_SET_PARAM_L]);
        stepperR.setMaxSpeed(frame.data[POS_SET_PARAM_R]);
        sendUDP("ok\n");
      }
      else if(frame.data[POS_SUB_COMMAND] == CMD_SUB_ACCEL){
        Serial.print("set acceleration");
        stepperL.setAcceleration(frame.data[POS_SET_PARAM_L]);
        stepperR.setAcceleration(frame.data[POS_SET_PARAM_R]);
        sendUDP("ok\n");
      }        
    }
    else if(frame.data[POS_COMMAND] == CMD_GET){
      if(frame.data[POS_SUB_COMMAND] == CMD_SUB_POS){
        sprintf(response, "Get positions: PosL=%d PosR=%d\n", stepperL.currentPosition(), stepperR.currentPosition());
        Serial.println(response);
        sendUDP(response);
      }
    }
  }
  // reset new command flag
  frame.newCommand = 0;
}

/* Test useless box components */
void receiveSerialFrame(){
  // if there's any serial available, read it:
  while (Serial.available() > 0) {
    
    // look for the next valid integer in the incoming serial stream:
    frame.data[frame.length] = Serial.parseInt();
    frame.length++;
    
    // look for the newline. That's the end of your sentence:
    if (Serial.read() == '\r') {
      frame.newCommand = 1;
      frame.length = 0;
    }
  }
}

void sendUDP(char * buffer){
  // Send return packet
  UDP.beginPacket(UDP.remoteIP(), UDP.remotePort());
  UDP.write((uint8_t*)buffer, strlen(buffer));
  UDP.endPacket();
  Serial.print("UDP: "); Serial.println(buffer);
}
