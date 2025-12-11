// #include <SoftwareSerial.h>


// int Checksum(char str[]) {
//     int caracter, suma = 0;
//     for(int i = 0; str[i] != '\0'; i++) {
//         caracter = str[i];
//         suma = suma + caracter;
//     }
//     int checksum = (suma)%256;
//     return(checksum);
// }

// char frase[100] = "Hola, mundo!";
// char frase2[100] = "Hola mundo!";
// char frase3[100] = "Hola. mundo!";

// void setup() {
//   Serial.begin(9600);  
// }

// void loop() {
//   Serial.println(Checksum(frase));
//   Serial.println(Checksum(frase2));
//   Serial.println(Checksum(frase3));
//   delay(5000);

// }

int Checksum(const char str[]) {
  unsigned int suma = 0;          // acumulador

  for (int i = 0; str[i] != '\0'; i++) {
    suma += (unsigned char)str[i]; // sumar valor ASCII de cada carácter
  }

  return suma % 256;              // checksum de 8 bits (0..255)
}


