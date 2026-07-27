from machine import Pin, ADC
import time

# Pinos de acordo com o diagram.json deste projeto
SENSOR_PIN = 35
BOTAO_PIN = 13

sensor_luz = ADC(Pin(SENSOR_PIN))
sensor_luz.atten(ADC.ATTN_11DB)  # range 0-3.3V -> leitura 0-4095

botao = Pin(BOTAO_PIN, Pin.IN, Pin.PULL_UP)  # nivel baixo = pressionado

# Estados possiveis da esteira
LIVRE = 0
BLOQUEADA = 1

# Limiares de leitura do ADC (calibrados para o range 0-4095)
LIMIAR_ESCURO = 1900   # acima disso -> objeto bloqueando o feixe
LIMIAR_CLARO = 1300    # abaixo disso -> feixe liberado

JANELA_MICROPARADA_MS = 5000
JANELA_DEBOUNCE_MS = 60
CICLO_MS = 15


class ContadorProducao:
    def __init__(self):
        self.total_pecas = 0
        self.estado_esteira = LIVRE
        self.instante_bloqueio = None
        self.microparada_avisada = False

        estado_inicial_botao = botao.value()
        self.botao_nivel_anterior = estado_inicial_botao
        self.botao_nivel_estavel = estado_inicial_botao
        self.botao_instante_borda = time.ticks_ms()

    def _leitura_sensor(self):
        return sensor_luz.read()

    def atualiza_esteira(self):
        agora = time.ticks_ms()
        leitura = self._leitura_sensor()

        if self.estado_esteira == LIVRE and leitura >= LIMIAR_ESCURO:
            self.estado_esteira = BLOQUEADA
            self.instante_bloqueio = agora
            self.microparada_avisada = False
            return

        if self.estado_esteira == BLOQUEADA and leitura <= LIMIAR_CLARO:
            self.estado_esteira = LIVRE
            self.instante_bloqueio = None
            self.total_pecas += 1
            print("Peca detectada! Total: {}".format(self.total_pecas))
            return

        if self.estado_esteira == BLOQUEADA and self.instante_bloqueio is not None:
            bloqueado_ha = time.ticks_diff(agora, self.instante_bloqueio)
            if bloqueado_ha > JANELA_MICROPARADA_MS and not self.microparada_avisada:
                print("Alerta: Micro-parada detectada!")
                self.microparada_avisada = True

    def atualiza_botao(self):
        agora = time.ticks_ms()
        nivel_atual = botao.value()

        if nivel_atual != self.botao_nivel_anterior:
            self.botao_instante_borda = agora
            self.botao_nivel_anterior = nivel_atual

        estabilizado = time.ticks_diff(agora, self.botao_instante_borda) > JANELA_DEBOUNCE_MS
        if estabilizado and nivel_atual != self.botao_nivel_estavel:
            self.botao_nivel_estavel = nivel_atual
            if nivel_atual == 0:  # transicao para pressionado
                self.reseta_turno()

    def reseta_turno(self):
        self.total_pecas = 0
        self.estado_esteira = LIVRE
        self.instante_bloqueio = None
        self.microparada_avisada = False
        print("Turno resetado com sucesso. Contadores zerados.")

    def loop(self):
        print("Contador de Producao Inicializado")
        while True:
            self.atualiza_esteira()
            self.atualiza_botao()
            time.sleep_ms(CICLO_MS)


if __name__ == "__main__":
    ContadorProducao().loop()