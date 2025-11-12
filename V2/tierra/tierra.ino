#include <SoftwareSerial.h>
int i;
SoftwareSerial mySerial(10, 11); // RX, TX

long nextMillis1; // Enviar mensaje para recibir datos
long nextMillis2; // Apagar led de recibir datos
long nextMillis3; // Error de comunicaciones

const int interval1 = 3000;
const int interval2 = 1000;
const int interval3 = 7000;

const int LedEarth = 2;    //Recibe datos 
const int LedComms = 7;   //Error de comunicacions

void setup() {
   Serial.begin(9600);
   mySerial.begin(9600);
   mySerial.println("Empezamos");
   i=1;

   pinMode(LedEarth, OUTPUT); 
   pinMode(LedComms, OUTPUT);
   nextMillis1 = millis() + interval1;
   nextMillis2 = millis();
   nextMillis3 = millis() + interval3;
}

void loop() {
   if(Serial.available()) {
      String orden = Serial.readStringUntil('\n'); // Lee orden de la interfaz 
      mySerial.println(orden);                     
   }
   if (millis() >= nextMillis2){
      digitalWrite(LedEarth, LOW);
   }
   if (millis() >= nextMillis1){
      mySerial.print("Envio: ");
      mySerial.println(i);
      i=i+1;
      nextMillis1 = millis() + interval1;
   }
   if (mySerial.available()) {
      digitalWrite(LedEarth, HIGH);          // Recibe datos
      nextMillis2 = millis() + interval2;
      digitalWrite(LedComms, LOW);           // No hay error de comunicaciones
      nextMillis3 = millis() + interval3;

      String mensaje = mySerial.readString(); 
      Serial.print(mensaje);                 // Envia datos a python
   }
   else if (millis() >= nextMillis3){
      digitalWrite(LedComms, HIGH);    // Error de comunicaciones descubierto
      Serial.println("0:ErrorComunicaciones");
   }
}