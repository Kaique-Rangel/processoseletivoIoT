# Relatório do Candidato

### Identificação do Candidato

- **Nome completo:** Kaique Rangel da Silva
- **GitHub:** Kaique-Rangel

---

## Visão Geral da Solução

O projeto implementa um **Contador de Produção Não-Intrusivo** para linhas de montagem manuais ou semiautomáticas sem CLP. Um sensor óptico (LDR) monitora a passagem de peças em uma esteira: quando o feixe de luz é interrompido e depois restabelecido, o sistema entende que uma peça passou e incrementa o contador. Caso a esteira permaneça bloqueada por tempo excessivo, o sistema emite um alerta de micro-parada. Um botão físico permite ao operador resetar o turno, zerando contadores e cronômetros.

A interação do usuário é feita via botão físico (reset de turno) e acompanhamento em tempo real pelo monitor serial, que exibe as mensagens de status do sistema.

---

## Arquitetura do Sistema Embarcado

O firmware (`src/main.py`) é organizado em torno de uma classe `ContadorProducao`, que encapsula todo o estado do sistema (contagem de peças, estado da esteira, temporizadores e estado do botão).

**Fluxo principal:**

1. Na inicialização, os pinos são configurados e a mensagem `"Contador de Producao Inicializado"` é impressa.
2. O loop principal (não-bloqueante, usando `time.sleep_ms` curto entre iterações) chama a cada ciclo:
   - `atualiza_esteira()` — lê o LDR e avalia transições de estado
   - `atualiza_botao()` — lê o botão com debounce

**Máquina de estados da esteira:**

- `LIVRE`: leitura de luminosidade alta (feixe livre)
- `BLOQUEADA`: leitura baixa (objeto interrompendo o feixe)
- Transição `LIVRE → BLOQUEADA`: início do bloqueio, marca o instante para contagem de tempo
- Transição `BLOQUEADA → LIVRE`: incrementa o contador de peças
- Se o tempo em `BLOQUEADA` ultrapassa 5 segundos, dispara o alerta de micro-parada (uma única vez por bloqueio)

**Botão de reset:**

- Leitura do pino com debounce baseado em tempo (`time.ticks_diff`)
- Só considera o acionamento válido após o nível do pino se manter estável pelo intervalo de debounce
- Ao confirmar o acionamento, zera contador de peças e reinicia o estado da esteira

Todas as temporizações usam `time.ticks_ms()` / `time.ticks_diff()`, evitando funções bloqueantes no loop principal.

---

## Componentes Utilizados na Simulação

- **Placa:** ESP32 DevKit C v4
- **Sensor óptico (LDR):** id `ldr1`, conectado ao pino analógico `35` — mede a luminosidade que representa o feixe de luz da esteira
- **Botão de reset:** id `btn1`, conectado ao pino digital `13`, configurado com pull-up interno (nível baixo = pressionado)
- **Monitor Serial (UART):** usado para exibir as mensagens de status e telemetria do sistema

---

## Decisões Técnicas Relevantes

- **Organização orientada a objetos:** todo o estado do sistema (contagem, estado da esteira, temporizadores, estado do botão) foi encapsulado em uma classe, evitando variáveis globais soltas e facilitando a leitura do fluxo.
- **Debounce por estabilização de borda:** o nível do botão só é considerado válido depois de permanecer estável por um intervalo mínimo, evitando falsos acionamentos por ruído da simulação.
- **Temporização não-bloqueante:** toda a lógica de tempo (micro-parada e debounce) foi implementada com `time.ticks_ms()`/`time.ticks_diff()` em vez de `time.sleep()`, garantindo que o loop principal continue respondendo aos estímulos do CI sem perder janelas de tempo.
- **Pinos e limiares próprios:** os pinos do LDR e do botão, assim como os limiares de leitura do ADC, foram definidos a partir de testes na simulação, calibrando o comportamento esperado (transição de estado e disparo de alertas) sem depender de valores de terceiros.

---

## Resultados Obtidos

O sistema foi validado manualmente no simulador visual do Wokwi, cobrindo os três cenários previstos:

- **Contagem de peças:** transição rápida de escuro para claro incrementa o contador corretamente, exibindo `"Peca detectada! Total: X"`.
- **Micro-parada:** manter o sensor bloqueado por mais de 5 segundos dispara `"Alerta: Micro-parada detectada!"` uma única vez por bloqueio.
- **Reset de turno:** o acionamento do botão zera o contador e os temporizadores, exibindo `"Turno resetado com sucesso. Contadores zerados."`, com debounce funcionando mesmo em cliques rápidos.

A mensagem de inicialização (`"Contador de Producao Inicializado"`) é exibida corretamente ao iniciar a simulação.

---

## Comentários Adicionais

A principal dificuldade foi calibrar os limiares de leitura do ADC para que a transição entre os estados `LIVRE` e `BLOQUEADA` refletisse fielmente o comportamento esperado pelo cenário simulado no Wokwi. Com mais tempo, seria interessante adicionar um mecanismo de calibração automática dos limiares (autocalibração no boot, medindo o nível de luz ambiente) para tornar o sistema mais robusto a variações de iluminação.