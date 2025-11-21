#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX

int i;

bool MediaTER = false;
int TempMax = 0;
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
const int LedTempMax = 8;

// MEDIA DE TEMPERATURA
bool calcularmedia = true;
int j = 0;                    // Indice para el vector de sumadatosT
bool contdatosT = false;      // Contador del numero de datos de temperatura enviados 
double sumadatosT[10];         // Suma de datos
double sumadatosFT;           // Suma de datos finales de temperatura del vector sumadatosT
double mediaT = 0;            // Media de la temperatura
const int Tmax = 32;          // Tempertura maxima que no volem superar
int Tmaxsobrepasada = 0;      // La temperatura màxima ha sigut  sobrepasada
double temp;
char info[5];

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  mySerial.println("Empezamos");
  i = 1;
  pinMode(LedEarth, OUTPUT);
  pinMode(LedComms, OUTPUT);
  pinMode(LedErrorDatos, OUTPUT);
  pinMode(LedTempMax, OUTPUT);
  digitalWrite(LedEarth, LOW);
  digitalWrite(LedComms, LOW);
  digitalWrite(LedErrorDatos, LOW);
  digitalWrite(LedTempMax , LOW);
  
  nextMillis1 = millis() + interval1;
  nextMillis2 = millis();
  nextMillis3 = millis() + interval3;
  nextMillisLED = millis();
}

void loop() {
  if(Serial.available()) {
    String orden = Serial.readStringUntil('\n');

    if (orden[0] == '3'){ 
      if(orden[5] == "MediaTER")      // 3:MediaTER (Se calcula la media en la estacion de tierra)
        MediaTER == true;
      else if (orden == "MediaSAT")   // 3:MediaSAT (Se calcula la media en el satelite)
        MediaTER == false;
    }
    else if (orden[0] == '4'){             // Código 4: Cambiar periodo
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
  
  if (millis() >= nextMillis2){
    digitalWrite(LedEarth, LOW);
  }
  
  if (millis() >= nextMillis1){
    mySerial.print("1:"); // Código 1: Solicitud de datos
    mySerial.println(i);
    nextMillis1 = millis() + interval1; 
    i = i + 1;
    //Serial.println(i); // QUITAR!!!
  }
  
  if (mySerial.available()) {       //Recibir datos del satélite
    digitalWrite(LedComms, LOW); 
    nextMillis3 = millis() + interval3; 
    
    String mensaje = mySerial.readStringUntil('\n');
    Serial.print(mensaje + "\n");
    
    if (mensaje[0] == '0'){
      digitalWrite(LedErrorDatos, HIGH); // Error en captura de datos del satélite
      Serial.println(" - Error de datos del satélite");
    }
    else if (mensaje[0] == '1'){
      digitalWrite(LedEarth, HIGH);
      nextMillis2 = millis() + interval2; //Para que se apague luego

      digitalWrite(LedErrorDatos, LOW);
      if (MediaTER == true){
        int ini = mensaje.indexOf(':', 0) +1;
        int fini = mensaje.indexOf(':', ini);
        for (int b = 0; b <= fini-ini; b++){
          info[b] = mensaje[ini + b];
        }
        temp = int(info);
        sumadatosT[j] = temp;
        j = j +1;
        if(j == 10){
          j = 0;
          contdatosT = true;
        }
        if (contdatosT == true) {
          for(int a = 0; a<10; a++){
            sumadatosFT = sumadatosFT + sumadatosT[a];
          }
          mediaT = sumadatosFT/10;
          if (mediaT < Tmax){     // Temperatura max superada ?
            Tmaxsobrepasada = 0;
          }
          else {
            Tmaxsobrepasada = 1;
          }
        }
      }
    }
    else if (mensaje[0] == '4'){
      int ini = mensaje.indexOf(':', 0) +1;
      int fini = mensaje.indexOf(':', ini);
      String TM = mensaje.substring(fini +1);
      TempMax = TM.toInt();
      if (TempMax == 1){
        digitalWrite(LedTempMax, HIGH);
      }
      else {
        digitalWrite(LedTempMax, LOW);
      }
    }
  }
  else if (millis() >= nextMillis3){
    digitalWrite(LedComms, HIGH); // Error de comunicaciones descubierto
    Serial.println("0:ErrorComunicaciones");
  }
}
