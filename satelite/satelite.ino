//CONEXIONES E INTERVALOS BASE
#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)

// Función para calcular checksum simple (suma de bytes módulo 256)
uint8_t calcularChecksum(const String& mensaje) {
  uint8_t checksum = 0;
  for (int i = 0; i < mensaje.length(); i++) {
    checksum += (uint8_t)mensaje.charAt(i);
  }
  return checksum;
}
bool enviardatos = false; 
bool fallodatos = false; 
bool enviardistancia = false;
bool enviarorbita = false;
long nextMillis; // Envia datos
long nextMillis2; // Error de datos
long nextMillisLED;
int interval = 5000; // Intervalo de envío
const int interval2 = 6000; // Intervalo de error
const int intervalLED = 1000; // LED encendido
float periodoTH;

#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
const int LedSat = 4; // Envia datos
const int LedDatos = 7; // Error de datos

//SERVOMOTOR
#include <Servo.h>     
Servo myServo;         
const long intervalServoMotor = 3000; // Cada 3 segundos cambia el ángulo
long nextServoMotor;    
int angulo = 100;       // Posición inicial del servo en grados (empieza en 100)
int paso = 20;          // Cantidad de grados que el servo se moverá en cada iteración

// SENSOR DE DISTANCIA ULTRASONIDOS
const int trigPin = 9; 
const int echoPin = 6; 
long nextSensor; 
const long intervalSensor = 3000; // Cada cuanto lee la distancia
long duracionSensor; 
long distanciaSensor; 
int joyX = 0; //Pin analogo al que el joystick X está conectado
int joyY = 1; //Pin analogo al que el joystick Y está conectado

// MEDIA DE TEMPERATURA
bool calcularMtemperatura = true; // Controlar si es calcula la temperatura
int i = 0;                    // Indice para el vector de sumadatosT
bool contadatosT = false;           // Contador del numero de datos de temperatura enviados 
double sumadatosT[10];         // Suma de datos
double SumadatosFT;            // Suma de datos finales de temperatura del vector sumadatosT
double mediaT = 0;            // Media de la temperatura
const int Tmax = 32;          // Tempertura maxima que no volem superar
int Tmaxsobrepasada = 0;      // La temperatura màxima ha sigut  sobrepasada
bool modoAutomatico = false; // Arranca en manual

// Constantes de Orbita satelite
const double G = 6.67430e-11;  // Gravitational constant (m^3 kg^-1 s^-2)
const double M = 5.97219e24;   // Mass of Earth (kg)
const double R_EARTH = 6371000;  // Radius of Earth (meters)
const double ALTITUDE = 400000;  // Altitude of satellite above Earth's surface (meters)
const double EARTH_ROTATION_RATE = 7.2921159e-5;  // Earth's rotational rate (radians/second)
const unsigned long MILLIS_BETWEEN_UPDATES = 10000; // Time in milliseconds between each orbit simulation update
const double  TIME_COMPRESSION = 20.0; // Time compression factor (90x)

// Variables orbita satelite
unsigned long nextUpdate; // Time in milliseconds when the next orbit simulation update should occur
double real_orbital_period;  // Real orbital period of the satellite (seconds)
double r;  // Total distance from Earth's center to satellite (meters)

// Prototipo
void simulate_orbit(unsigned long millis, double inclination, int ecef);

void setup(){
  Serial.begin(9600);
  Serial.println("Empezamos la recepción");
  mySerial.begin(9600);
  dht.begin();
  
  //Codigo de Orbita
  nextUpdate = MILLIS_BETWEEN_UPDATES; 
  r = R_EARTH + ALTITUDE;
  real_orbital_period = 2 * PI * sqrt(pow(r, 3) / (G * M));

  // Fin de codigo de Orbita

  pinMode(LedSat, OUTPUT);
  pinMode(LedDatos, OUTPUT);
  
  digitalWrite(LedSat, LOW); // LEDs apagados inicialmente
  digitalWrite(LedDatos, LOW);
  
  nextMillis = millis() + interval;
  nextMillis2 = millis() + interval2;
  nextMillisLED = millis();

  myServo.attach(3);
  myServo.write(angulo);  // Inicializar servo en 100 grados
  nextServoMotor = millis() + intervalServoMotor;

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  nextSensor = millis() + intervalSensor;
}

void loop(){
    // Codigo Orbita Satelite
    unsigned long currentTime = millis();
    if (enviarorbita && currentTime > nextUpdate) {
        simulate_orbit(currentTime, 0, 0);
        nextUpdate = currentTime + MILLIS_BETWEEN_UPDATES;
    }
    // Fin Codigo Orbita satelite

  if (millis() >= nextMillisLED){   // Apagar LED de envío después de 1 segundo
    digitalWrite(LedSat, LOW);
  }
  if (mySerial.available()) {       // Lee orden desde Tierra
    String data = mySerial.readStringUntil('\n'); // Lee orden completa
    Serial.println(data);
    
    int fin = data.indexOf(':', 0);
    if (fin == -1) return;  // seguridad

    int codigo = data.substring(0, fin).toInt();
    int inicio = fin + 1;
    String orden;

    if (codigo == 3) {               // Código 3: Órdenes de control (inicio, parar, reanudar, órbita, radar modo)
      // todo lo que hay después del primer ':' es la orden
      orden = data.substring(inicio);
      orden.trim();

      Serial.print("Orden recibida: ");
      Serial.println(orden);
      
      if (orden == "reanudar" || orden == "inicio") {
        enviardatos = true;
        nextMillis = millis() + interval;
      }
      else if (orden == "parar") {
        enviardatos = false;
        fallodatos = false;
      }
      else if (orden == "MediaSAT") {
        calcularMtemperatura = true;
      }
      else if (orden == "MediaTER") {
        calcularMtemperatura = false;
      }
      else if (orden == "OrbitaInicio") {
        enviarorbita = true;
      }
      else if (orden == "OrbitaParar") {
        enviarorbita = false;
      }
      else if (orden.startsWith("RadarManual")) {
        modoAutomatico = false;
        // Buscar si hay un valor después de "RadarManual:"
        // El formato puede ser "RadarManual" o "RadarManual:valor"
        int segundoNum = orden.indexOf(':', 11); // Buscar después de "RadarManual" (11 caracteres)
        if (segundoNum > 0) {
          // Hay un valor, actualizar el servo
          int valor = orden.substring(segundoNum + 1).toInt();
          valor = constrain(valor, 0, 180);
          // Ajustar a saltos de 20° (redondeo al más cercano)
          valor = ((valor + 10) / 20) * 20;
          valor = constrain(valor, 0, 180);
          myServo.write(valor);
          angulo = valor; // Actualizar el ángulo actual
          Serial.print("Radar manual - servo movido a: ");
          Serial.println(valor);
        } else {
          // Si no hay valor, solo se activa el modo manual y volver a 100 grados
          angulo = 100;
          myServo.write(angulo);
          Serial.println("Modo manual activado - servo en 100 grados");
        }
      }
      else if (orden == "RadarAutomatico") {
        modoAutomatico = true;
        // Volver a 100 grados al cambiar a automático
        angulo = 100;
        myServo.write(angulo);
        paso = 20; // Reiniciar paso positivo
        Serial.println("Modo automático activado, servo en 100 grados");
      }
    }
    else if (codigo == 4) {          // Código 4: Cambiar período de envío de datos
      // data: "4:3000"
      orden = data.substring(inicio);
      orden.trim();
      int nuevoPeriodo = orden.toInt();
      if (nuevoPeriodo > 0) {
        interval = nuevoPeriodo;
        Serial.print("Período actualizado a: ");
        Serial.println(interval);
      }
    }
    else if (codigo == 6) {          // Código 6: Control de envío de distancia
      orden = data.substring(inicio);
      orden.trim();
      Serial.print("Orden recibida: ");
      Serial.println(orden);

      if (orden == "inicio") {
        enviardistancia = true;
        nextMillis = millis() + interval;
      }
      else if (orden == "parar") {
        enviardistancia = false;
      }
    }
  }
 
  if (enviardatos == true && millis() >= nextMillis){
    digitalWrite(LedSat, HIGH); // Enciende LED de envío
    nextMillisLED = millis() + intervalLED; // LED se apagará 
    
    float hum = dht.readHumidity();
    float temp = dht.readTemperature();
    nextMillis += interval; // Reinicia temporizador envio
    if ((isnan(hum) || isnan(temp)) && (fallodatos == false)){ // Empieza a no captar datos
      nextMillis2 = millis() + interval2;
      fallodatos = true;
    }
    else if (!(isnan(hum) || isnan(temp))){ // Capta datos correctamente
      fallodatos = false;
      digitalWrite(LedDatos, LOW); // Apaga LED de error
      // Crear mensaje sin checksum
      String mensaje = "1:";
      mensaje += String(temp);
      mensaje += ":";
      mensaje += String(hum);
      // Calcular y agregar checksum
      uint8_t checksum = calcularChecksum(mensaje);
      mySerial.print(mensaje);
      mySerial.print(":");
      mySerial.println(checksum);
      
      if (calcularMtemperatura == true){
        sumadatosT[i] = temp;
        i=i+1;
        if(i == 10){
          i=0;
          contadatosT = true;
        }
        if (contadatosT==true) {
          SumadatosFT = 0;
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
          // Envia media de temperatura con checksum
          String mensajeMedia = "4:";
          mensajeMedia += String(mediaT);
          mensajeMedia += ":";
          mensajeMedia += String(Tmaxsobrepasada);
          uint8_t checksumMedia = calcularChecksum(mensajeMedia);
          mySerial.print(mensajeMedia);
          mySerial.print(":");
          mySerial.println(checksumMedia); 
        }
      }
    }
  }
<<<<<<< Updated upstream
  else if ((millis() >= nextMillis2) && (fallodatos == true)){
  digitalWrite(LedDatos, HIGH); // Enciende LED de error
  String mensajeErrorDatos = "0:ErrorCapturaDatos";
  uint8_t checksumErrorDatos = calcularChecksum(mensajeErrorDatos);
  mySerial.print(mensajeErrorDatos);
  mySerial.print(":");
  mySerial.println(checksumErrorDatos);
=======
  else if ((millis() >= nextMillis2) && (fallodatos == true) && (enviardatos == true)){
    digitalWrite(LedDatos, HIGH); // Enciende LED de error
    String mensajeErrorDatos = "0:ErrorCapturaDatos";
    uint8_t checksumErrorDatos = calcularChecksum(mensajeErrorDatos);
    mySerial.print(mensajeErrorDatos);
    mySerial.print(":");
    mySerial.println(checksumErrorDatos);
>>>>>>> Stashed changes
  }

  if ((modoAutomatico == true) && (millis() >= nextServoMotor)) {
    nextServoMotor = millis() + intervalServoMotor;
    myServo.write(angulo);
    angulo = angulo + paso;

    // Limitar el rango: de 100 a 180 grados, luego vuelve a 100
    if (angulo >= 180) {
      angulo = 180;
      paso = -paso; // Cambiar dirección hacia abajo
    } else if (angulo <= 100) {
      angulo = 100;
      paso = -paso; // Cambiar dirección hacia arriba
    }
  }

  //ULTRASONIDOS
  if (millis() >= nextSensor) {
    nextSensor = millis() + intervalSensor;
    
    digitalWrite(trigPin, LOW); // Aseguramos que el TRIG esté en LOW antes de enviar el pulso
    delayMicroseconds(2); // Creo que es necesario para estabilizar el pin
    digitalWrite(trigPin, HIGH); // Enviamos pulso HIGH
    delayMicroseconds(10); // También necesario para estabilizar el pin
    digitalWrite(trigPin, LOW); // Dejamos de enviar el pulso
    
    duracionSensor = pulseIn(echoPin, HIGH, 30000); // Medimos el tiempo que tarda el pulso en volver
    // 30000 es el timeout, hace que deje de esperar al pulso si pasan 30ms y no ha llegado nada aún
    
    if ((duracionSensor > 0) && (enviardistancia == true)) { // Si ha llegado el pulso en el tiempo establecido
      distanciaSensor = duracionSensor * 0.034 / 2; // Distancia = tiempo * velocidad del sonido / 2
      
      // Envia 2:distancia:angulo con checksum
      String mensajeRadar = "2:";
      mensajeRadar += String(distanciaSensor);
      mensajeRadar += ":";
      mensajeRadar += String(angulo);
      uint8_t checksumRadar = calcularChecksum(mensajeRadar);
      mySerial.print(mensajeRadar);
      mySerial.print(":");
      mySerial.println(checksumRadar);
    } 
    else if (enviardistancia == true) { // Si no se ha detectado la llegada del pulso
      distanciaSensor = 0; // El 0 para nosotros indica error
      // Enviar error en formato correcto: código 0 para errores
      String mensajeError = "0:ErrorSensorDistancia";
      uint8_t checksumError = calcularChecksum(mensajeError);
      mySerial.print(mensajeError);
      mySerial.print(":");
      mySerial.println(checksumError);
    }
  }
}

void simulate_orbit(unsigned long millis, double inclination, int ecef){
  double time = (millis / 1000.0) * TIME_COMPRESSION;  // Real orbital time
  double angle = 2 * PI * (time / real_orbital_period);  // Angle in radians
  double x = r * cos(angle);  // X-coordinate (meters)
  double y = r * sin(angle) * cos(inclination);  // Y-coordinate (meters)
  double z = r * sin(angle) * sin(inclination);  // Z-coordinate (meters)

  if (ecef) {
    double theta = EARTH_ROTATION_RATE * time;
    double x_ecef = x * cos(theta) - y * sin(theta);
    double y_ecef = x * sin(theta) + y * cos(theta);
    x = x_ecef;
    y = y_ecef;
  }

  // Send the data to the serial port with checksum
  if (enviarorbita == true){
    String mensajeOrbita = "9:";
    mensajeOrbita += String(time, 6);  // tiempo con 6 decimales
    mensajeOrbita += ":";
    mensajeOrbita += String(x, 1);     // coordenadas con 1 decimal (mejor para regex)
    mensajeOrbita += ":";
    mensajeOrbita += String(y, 1);
    mensajeOrbita += ":";
    mensajeOrbita += String(z, 1);
    uint8_t checksumOrbita = calcularChecksum(mensajeOrbita);
    mySerial.print(mensajeOrbita);
    mySerial.print(":");
    mySerial.println(checksumOrbita);
  }
}

