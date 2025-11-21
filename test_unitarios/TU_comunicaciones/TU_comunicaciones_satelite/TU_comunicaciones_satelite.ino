#include <SoftwareSerial.h>
int i;
SoftwareSerial mySerial(10, 11); // RX, TX 
void setup() {
   mySerial.begin(9600);
   mySerial.println("Empezamos");
   i=1;
}
void loop() {
   delay (3000);
   mySerial.print("Envío: ");
   mySerial.println(i);
   i=i+1;
}