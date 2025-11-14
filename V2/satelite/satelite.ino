#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)
bool enviardatos = true; 
bool fallodatos = false; 
long nextMillis; // Envia datos
long nextMillis2; // Error de datos
long nextMillisLED;
int interval = 3000; // Intervalo de envío
const int interval2 = 4000; // Intervalo de error
const int intervalLED = 1000; // LED encendido
float periodoTH;

#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
const int LedSat = 4; // Envia datos
const int LedDatos = 7; // Error de datos

#include <Servo.h>     
Servo myServo;         
const long intervalServoMotor = 40; // Cada 40ms cambia el ángulo
long nextServoMotor;    
int angulo = 0;         // Posición inicial del servo en grados
int paso = 2;           // Cantidad de grados que el servo se moverá en cada iteración (40ms)

// MEDIA DE TEMPERATURA
bool calcularMtemperatura = true; // Controlar si es calcula la temperatura
int i = 0;                    // Indice para el vector de sumadatosT
bool contadatosT = false;           // Contador del numero de datos de temperatura enviados 
double sumadatosT[10];         // Suma de datos
double SumadatosFT;            // Suma de datos finales de temperatura del vector sumadatosT
double mediaT = 0;            // Media de la temperatura
const int Tmax = 32;          // Tempertura maxima que no volem superar
int Tmaxsobrepasada = 0;      // La temperatura màxima ha sigut  sobrepasada

void setup(){
  Serial.begin(9600);
  Serial.println("Empezamos la recepción");
  mySerial.begin(9600);
  dht.begin();
  
  pinMode(LedSat, OUTPUT);
  pinMode(LedDatos, OUTPUT);
  
  digitalWrite(LedSat, LOW); // LEDs apagados inicialmente
  digitalWrite(LedDatos, LOW);
  
  nextMillis = millis() + interval;
  nextMillis2 = millis() + interval2;
  nextMillisLED = millis();

  myServo.attach(3);         
  nextServoMotor = millis() + intervalServoMotor;
}

void loop(){
  if (millis() >= nextMillisLED){   // Apagar LED de envío después de 1 segundo
    digitalWrite(LedSat, LOW);
  }
  if (mySerial.available()) {       // Lee orden del satélite
    String data = mySerial.readStringUntil('\n'); // Lee orden
    Serial.println(data);
    
    int fin = data.indexOf(':', 0);
    int codigo = data.substring(0, fin).toInt();
    int inicio = fin + 1;
    String orden;
    
    if (codigo == 3){               // Código 3: Órdenes de control (inicio, parar, reanudar)
      fin = data.indexOf('\n', inicio);
      if (fin == -1) 
        fin = data.length();
      orden = data.substring(inicio, fin);
      Serial.print("Orden recibida: ");
      Serial.println(orden);
      
      if (orden == "reanudar" || orden == "inicio"){
        enviardatos = true;
        nextMillis = millis() + interval; // Reinicia el temporizador para evitar salto
      }
      if (orden == "parar"){
        enviardatos = false;
      }
      if (orden == "MediaSAT"){ //Orden para calcuar media de temperatura
        calcularMtemperatura = true;
      }
      if (orden == "MediaTER"){ //Orden para calcuar media de temperatura
        calcularMtemperatura = false;
      }
    }
    
    if (codigo == 4){                     // Código 4: Cambiar período
      fin = data.indexOf(':', inicio);
      if (fin == -1) 
        fin = data.length();
      int nuevoPeriodo = data.substring(inicio, fin).toInt();
      interval = nuevoPeriodo;
      Serial.print("Período actualizado a: ");
      Serial.println(interval);
    }
  }
  
  if (enviardatos == true && millis() >= nextMillis){
    digitalWrite(LedSat, HIGH); // Enciende LED de envío
    nextMillisLED = millis() + intervalLED; // LED se apagará 
    nextMillis = millis() + interval; // Reinicia temporizador envio
    
    float hum = dht.readHumidity();
    float temp = dht.readTemperature();
    if ((isnan(hum) || isnan(temp)) && (fallodatos == false)){ // Empieza a no captar datos
      nextMillis2 = millis() + interval2;
      fallodatos = true;
    }
    else if (!(isnan(hum) || isnan(temp))){ // Capta datos correctamente
      fallodatos = false;
      digitalWrite(LedDatos, LOW); // Apaga LED de error
      mySerial.print("1:"); 
      mySerial.print(temp);
      mySerial.print(":");
      mySerial.println(hum);
      if (calcularMtemperatura == true){
        sumadatosT[i] = temp;
        i=i+1;
        if(i == 10){
          i=0;
          contadatosT = true;
        }
        if (contadatosT==true) {
          for(int a =0; a<10; a++){
            SumadatosFT=SumadatosFT+sumadatosT[a];
          }
          mediaT = SumadatosFT/10;
          // Temperatura max superada ?
          if (mediaT < Tmax){ 
          Tmaxsobrepasada = 0;
          }
          else {
            Tmaxsobrepasada = 1;
          }
          // Envia media de temperatura
          mySerial.print("4:"); 
          mySerial.print(mediaT);
          mySerial.print(":");
          mySerial.println(Tmaxsobrepasada);        
        }
      }
    }
  }
  else if ((millis() >= nextMillis2) && (fallodatos == true)){
    digitalWrite(LedDatos, HIGH); // Enciende LED de error
    mySerial.println("0:ErrorCapturaDatos");
  }

  if (millis() >= nextServoMotor) {
    nextServoMotor = millis() + intervalServoMotor;
    myServo.write(angulo);
    angulo = angulo + paso;

    if (angulo >= 180 || angulo <= 0) {
      paso = -paso; // Cambiamos el signo del paso para invertir el movimiento
    }
  }
}