#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)

bool enviardatos = true;
bool fallodatos = false;

long nextMillis;  // Envia datos
long nextMillis2; // Error de datos
int interval = 1000;
const int interval2 = 4000;
float periodoTH;

#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const int LedSat = 4;      //Envia datos
const int LedDatos = 7;   //Error de datos

void setup(){
   Serial.begin(9600);
   Serial.println("Empezamos la recepción");
   mySerial.begin(9600);
   dht.begin();

   pinMode(LedSat, OUTPUT);
   pinMode(LedDatos, OUTPUT);
   digitalWrite(LedSat, LOW);
   nextMillis = millis() + interval;
}   
void loop(){
   if (millis() >= nextMillis){
      digitalWrite(LedSat,LOW);
   }
   if (mySerial.available()) {
      String data = mySerial.readStringUntil('\n'); // Lee orden
      Serial.println(data);

      int fin = data.indexOf(':',0); 
      int codigo = data.substring(0, fin).toInt(); 
      int inicio = fin+1;
      char orden;
      if (codigo == 1){
         fin=data.indexOf(':',inicio);
         periodoTH = data.substring(inicio, fin).toInt();
         interval = int(periodoTH)*1000;
      }
      if (codigo == 3){
         fin=data.indexOf(':',inicio);
         orden = data.substring(inicio, fin).toInt();
      }






      if (orden == "reanudar" || data == "Inicio"){
         enviardatos = true;
         nextMillis = millis() + interval; // Reinicia el temporizador para evitar salto
      } 
      if (orden == "parar"){
         enviardatos = false;
      } 
      if (enviardatos==true && millis() >= nextMillis){     // Si no es orden envia datos captados
         digitalWrite(LedSat, HIGH);
         nextMillis = millis() + interval;
         
         float hum = dht.readHumidity();
         float temp = dht.readTemperature();
         if ((isnan(hum) || isnan(temp)) && (fallodatos == false)){  // Empieza ha no captar datos
            nextMillis2 = millis() + interval2;
            fallodatos = true;
         }
         else if (!(isnan(hum) || isnan(temp))){   // Capta datos
            fallodatos = false;
            digitalWrite(LedDatos, LOW);  // Envia datos
            mySerial.print("1:");
            mySerial.print(temp);
            mySerial.print(":");
            mySerial.println(hum);
         }
         else if ((millis() >= nextMillis2) && (fallodatos == true)){   // No ha captado datos durante X tiempo
            digitalWrite(LedDatos, HIGH);
            mySerial.println("0:ErrorCapturaDatos");
         }
      }  
   } 
}