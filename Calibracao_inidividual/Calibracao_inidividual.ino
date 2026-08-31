#include <Arduino.h>
#include <math.h>
#include "HX711.h"

#define HX711_DOUT 19
#define HX711_SCK 18

HX711 scale;

int numLeituras = 10;

long long tara = 0;

// Peso(g) = A*x² + B*x + C
double A = 0.0;
double B = 0.0;
double C = 0.0;

bool curvaConfigurada = false;

long long fazerMedia(int quantidade){
  if(quantidade <= 0){
    quantidade = 1;
  }

  long double soma = 0;

  for(int i = 0; i < quantidade; i++){
    while(!scale.is_ready()){
      delay(1);
    }

    soma += scale.read();

    delay(50);
  }

  return (long long)(soma / quantidade);
}

void enviarLeitura(){
  long long bruto = fazerMedia(numLeituras);

  long long corrigido = bruto - tara;

  Serial.print("RAW=");
  Serial.println(bruto);

  Serial.print("TARE=");
  Serial.println(tara);

  Serial.print("CORR=");
  Serial.println(corrigido);
}

void fazerTara(){
  long long bruto = fazerMedia(numLeituras);

  tara = bruto;

  Serial.print("TARE_OK");
  Serial.println(tara);
}

double calcularPeso(long long leituraBruta){
  double x = (double)leituraBruta - (double)tara;

  return A*x*x + B*x + C;
}

void enviarPeso(){
  if(!curvaConfigurada){
    Serial.println("ERROR=CURVE_NOT_CONFIGURED");
    return;
  }

  long long bruto = fazerMedia(numLeituras);
  double peso = calcularPeso(bruto);

  Serial.print("RAW=");
  Serial.println(bruto);

  Serial.print("CORR=");
  Serial.println(bruto - tara);

  Serial.print("WEIGHT=");
  Serial.println(peso, 6);
}

void processarCoeficientes(String comando){
  int p1 = comando.indexOf(',');
  int p2 = comando.indexOf(',', p1 + 1);
  int p3 = comando.indexOf(',', p2 + 1);
  if(p1 < 0 || p2 < 0 || p3 < 0){
    Serial.println("ERRO=INVALID_COEF");
    return;
  }

  String textoA = comando.substring(p1 + 1, p2);
  String textoB = comando.substring(p2 + 1, p3);
  String textoC = comando.substring(p3 + 1);

  A = textoA.toDouble();
  B = textoA.toDouble();
  C = textoA.toDouble();
  
  curvaConfigurada = true;

  Serial.println("COEF_OK");

  Serial.print("A=");
  Serial.print(A, 15);

  Serial.print("B=");
  Serial.println(B, 15);

  Serial.print("C=");
  Serial.println(C, 15);
}

void processarNumeroLeituras(String comando){
  int separador = comando.indexOf(',');

  if(separador < 0){
    Serial.println("ERROR=INVALID_SETN");
    return;
  }

  String valor = comando.substring(separador + 1);

  int novoNumero = valor.toInt();

  if(novoNumero < 1){
    Serial.print("SETN_OK=");
    Serial.println(numLeituras);
  }
}

void processarComando(String comando){
  comando.trim();

  if(comando.length() == 0){
    return;
  }

  if(comando == "READ"){
    enviarLeitura();
  }
  else if(comando == "TARE"){
    fazerTara();
  }
  else if(comando == "WEIGHT"){
    enviarPeso();
  }
  else if(comando == "INFO"){
    Serial.println("HX711_SCALE");

    Serial.print("READINGS=");
    Serial.println(numLeituras);

    Serial.print("TARE=");
    Serial.println(tara);

    Serial.print("CURVE=");
    Serial.println(curvaConfigurada ? "YES":"NO");
  }
  else if(comando.startsWith("SETN,")){
    processarNumeroLeituras(comando);
  }
  else if(comando.startsWith("COEF,")){
    processarCoeficientes(comando);
  }
  else{
    Serial.println("ERROR=UNKNOWN_COMMAND");
  }
}

void setup(){
  Serial.begin(115200);

  delay(1000);

  scale.begin(HX711_DOUT, HX711_SCK);
  Serial.println("HX711_SCALE_READY");
}

void loop(){
  if(Serial.available()){
    String comando = Serial.readStringUntil('\n');

    processarComando(comando);
  }
}