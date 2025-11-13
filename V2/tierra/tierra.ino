#include <SoftwareSerial.h>

int i;
SoftwareSerial mySerial(10, 11); // RX, TX
long nextMillis1; 
long nextMillis2; 
long nextMillis3; 
long nextMillisLED; 
int interval1 = 3000; // Intervalo de solicitud datos
const int interval2 = 1000; // Intervalo apagar LED 
const int interval3 = 7000; // Timeout de error
const int intervalLED = 1000; // LEDs encendidos 
const int LedEarth = 2; 
const int LedComms = 7; 
const int LedErrorDatos = 4; 

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  mySerial.println("Empezamos");
  i = 1;
  pinMode(LedEarth, OUTPUT);
  pinMode(LedComms, OUTPUT);
  pinMode(LedErrorDatos, OUTPUT);
  digitalWrite(LedEarth, LOW);
  digitalWrite(LedComms, LOW);
  digitalWrite(LedErrorDatos, LOW);
  
  nextMillis1 = millis() + interval1;
  nextMillis2 = millis();
  nextMillis3 = millis() + interval3;
  nextMillisLED = millis();
}

void loop() {
  if(Serial.available()) {
    String orden = Serial.readStringUntil('\n');

    if (orden[0] == '4'){             // Código 4: Cambiar periodo
      int inicio = orden.indexOf(':', 0) + 1;
      int fin = orden.indexOf('\n', inicio);
      if (fin == -1) fin = orden.length();
      interval1 = orden.substring(inicio, fin).toInt();
      Serial.print("Período actualizado a: ");
      Serial.println(interval1);
      mySerial.println(orden);        // Enviar también al satélite
    }
    else {
      mySerial.println(orden);        // Transmite otras órdenes al satélite
    }
  }
  
  if (millis() >= nextMillisLED){
    digitalWrite(LedEarth, LOW);
  }
  
  if (millis() >= nextMillis1){
    mySerial.print("1:"); // Código 1: Solicitud de datos
    mySerial.println(i);
    nextMillis1 = millis() + interval1; 
    i = i + 1;
    Serial.println(i);
  }
  
  if (mySerial.available()) {       // Recibir datos del satélite
    digitalWrite(LedEarth, HIGH); 
    nextMillisLED = millis() + intervalLED; 
    
    digitalWrite(LedComms, LOW); 
    nextMillis3 = millis() + interval3; 
    
    String mensaje = mySerial.readStringUntil('\n');
    Serial.print(mensaje);
    
    if (mensaje[0] == '0'){
      digitalWrite(LedErrorDatos, HIGH); // Error en captura de datos del satélite
      Serial.println(" - Error de datos del satélite");
    }
    else if (mensaje[0] == '1'){
      digitalWrite(LedErrorDatos, LOW);
    }
  }
  
  else if (millis() >= nextMillis3){
    digitalWrite(LedComms, HIGH); // Error de comunicaciones descubierto
    Serial.println("0:ErrorComunicaciones");
  }
}
