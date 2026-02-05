# CFE-HYDRO

## Título:

CFE-HYDRO: Um Protocolo Leve para Reconstrução Progressiva de Sinais Hidropônicos sob Restrições de Comunicação

## Resumo:

O artigo propõe o protocolo CFE-HYDRO, uma solução leve para o monitoramento em tempo real de parâmetros físico-químicos em sistemas hidropônicos (como pH, temperatura, condutividade elétrica e Oxigênio dissolvido), que enfrentam restrições de banda e energia em ambientes agrícolas com infraestrutura de comunicação limitada. O objetivo principal do artefato é permitir a aquisição, transmissão e reconstrução eficiente de séries temporais densas, mesmo quando a taxa de transmissão é inferior à taxa de amostragem dos sensores.

O protocolo fundamenta-se nos princípios da Estimativa de Campo Compressiva (CFE), realizando a amostragem em alta frequência, mas transmitindo apenas um subconjunto aleatório das medições. A inovação central está na incorporação de metadados semânticos que descrevem a natureza do sinal (ex.: logarítmica, sigmoidal, polinomial), permitindo que o receptor selecione e aplique automaticamente o modelo de interpolação ou reconstrução mais adequado (linear, logarítmico, etc.), em vez de depender de interpoladores lineares genéricos.

A avaliação experimental com dados reais de um sistema hidropônico comercial demonstrou que o CFE-HYDRO reduz significativamente o uso do canal de comunicação (ex.: transmitindo apenas 33% das amostras) enquanto mantém alta fidelidade na reconstrução dos sinais. Resultados quantitativos mostraram rápida convergência do erro e capacidade preditiva para horizontes futuros curtos, validando a abordagem para o monitoramento contínuo e a tomada de decisão em tempo hábil sob restrições de recursos.

O protocolo opera na camada de aplicação, utilizando MQTT como transporte, representando uma contribuição prática para o avanço da agricultura de precisão e IoT em cenários com conectividade limitada.

# Estrutura do readme.md

│   LICENSE.md
│   README.md
│
├───charts
│       Gráfico 1.tex
│       Gráfico 4.tex
│       Gráfico 5.tex
│       Gráfico 6.tex
│       Gráfico 7.tex
│
├───images
│       Figura 1.Interpolação Linear vs Interpolação Logarítmica.png
│       Figura 2.Visão geral do funcionamento do CFE-HYDRO.png
│       Figura 3.Estrutura do pacote CFE-HDP.png
│       Figura 4.Reconstrução quantitativa da série temporal de CE.png
│       Figura 5.Convegência do RMSE normalizado.png
│       Figura 6.Capacidade preditiva do sinal transmitido.png
│       Figura 7.Impacto da Esparsidade na Precisão.png
│
└───src
    │   Analisa dados sensoriados.py
    │   graficos_resultados.py
    │   Gráficos_Estimativa de Campo Compressiva.py
    │
    └───data
            dataset_cfe-hydro.csv
            resultados_simulacao.csv

# Selos Considerados

Os autores devem descrever quais selos devem ser considerados no processo de avaliação. Como por exemplo: ``Os selos considerados são: Disponíveis e Funcionais.''

# Informações básicas

Esta seção deve apresentar informações básicas de todos os componentes necessários para a execução e replicação dos experimentos. 
Descrevendo todo o ambiente de execução, com requisitos de hardware e software.

# Dependências

Informações relacionadas a benchmarks utilizados e dependências para a execução devem ser descritas nesta seção. 
Busque deixar o mais claro possível, apresentando informações como versões de dependências e processos para acessar recursos de terceiros caso necessário.

# Preocupações com segurança

Caso a execução do artefato ofereça algum tipo de risco para os avaliadores. Este risco deve ser descrito e o processo adequado para garantir a segurança dos revisores deve ser apresentado.

# Instalação

O processo de baixar e instalar a aplicação deve ser descrito nesta seção. Ao final deste processo já é esperado que a aplicação/benchmark/ferramenta consiga ser executada.

# Teste mínimo

Esta seção deve apresentar um passo a passo para a execução de um teste mínimo.
Um teste mínimo de execução permite que os revisores consigam observar algumas funcionalidades do artefato. 
Este teste é útil para a identificação de problemas durante o processo de instalação.

# Experimentos

Esta seção deve descrever um passo a passo para a execução e obtenção dos resultados do artigo. Permitindo que os revisores consigam alcançar as reivindicações apresentadas no artigo. 
Cada reivindicações deve ser apresentada em uma subseção, com detalhes de arquivos de configurações a serem alterados, comandos a serem executados, flags a serem utilizadas, tempo esperado de execução, expectativa de recursos a serem utilizados como 1GB RAM/Disk e resultado esperado. 

Caso o processo para a reprodução de todos os experimento não seja possível em tempo viável. Os autores devem escolher as principais reivindicações apresentadas no artigo e apresentar o respectivo processo para reprodução.

## Reivindicações #X

## Reivindicações #Y

# LICENSE

Apresente a licença.

🌱 CFE-HYDRO
Um Protocolo Leve para Reconstrução Seletiva de Sinais

Introdução
O monitoramento em tempo real de parâmetros físico-químicos é fundamental em aplicações de Internet das Coisas (IoT) para agricultura de precisão, como sistemas hidropônicos. Variáveis como pH, temperatura e condutividade elétrica precisam ser amostradas em alta frequência para garantir a estabilidade do sistema e permitir decisões de manejo oportunas. No entanto, esses sistemas operam sob severas restrições de recursos, especialmente em relação ao consumo energético e comunicação sem fio, tornando desafiadora a transmissão contínua de grandes volumes de dados em ambientes com conectividade limitada.

Contexto
Sistemas hidropônicos requerem monitoramento contínuo de diversos parâmetros para manter condições ideais de crescimento das plantas. Tradicionalmente, as abordagens de coleta e transmissão de dados assumem largura de banda suficiente para envio contínuo de medições ou utilizam estratégias de agregação em lote que introduzem latência e perda de granularidade temporal. Mesmo quando técnicas de subamostragem são empregadas, a reconstrução dos sinais no receptor frequentemente baseia-se em modelos genéricos de interpolação linear, inadequados para capturar dinâmicas não lineares presentes em muitos parâmetros agrícolas.

Problema
Existe uma lacuna entre a necessidade de monitoramento preciso e em tempo quase real e as capacidades efetivas das redes de sensoriamento disponíveis em ambientes agrícolas com restrições de comunicação. As abordagens tradicionais não conseguem equilibrar eficientemente a redução no uso de banda com a preservação da fidelidade dos sinais reconstruídos, especialmente para parâmetros com comportamento não linear como pH (logarítmico), condutividade elétrica (polinomial/complexa) e crescimento vegetal (sigmoidal).

Protocolo Proposto: CFE-HYDRO
O CFE-HYDRO é um protocolo leve baseado nos princípios de Estimativa de Campo Compressiva (CFE) que viabiliza a coleta e transmissão eficientes de sinais sensoriados sob restrições de largura de banda. O protocolo integra três componentes principais:

1. Subamostragem Aleatória
Realiza sensoriamento em alta taxa, mas transmite apenas um subconjunto aleatório das medições
Seleciona k amostras aleatórias dentro de cada intervalo de transmissão

2. Metadados Semânticos
Inclui informações sobre a natureza de cada parâmetro monitorado
Identifica o modelo de interpolação mais apropriado (linear, logarítmico, polinomial, sigmoidal)
Utiliza o cabeçalho CFE-HDP (Compressive Field Estimation - Hydroponic Data Protocol Header)

3. Reconstrução Seletiva no Receptor
Aplica automaticamente técnicas de interpolação adequadas a cada tipo de sinal
Permite reconstrução progressiva de séries temporais densas a partir de amostras esparsas
Opera sobre protocolos de transporte existentes (como MQTT)

Avaliação Experimental
A avaliação do protocolo foi realizada com dados reais de um sistema hidropônico comercial, considerando três métricas principais:

Métricas de Avaliação
Erro Quadrático Médio (RMSE): Para quantificar a diferença entre a série reconstruída e a original
Evolução temporal do erro: Análise da redução do erro em função do número de amostras recebidas
Capacidade preditiva: Habilidade de estimar valores futuros do sinal a partir de amostras esparsas

Resultados Principais
O protocolo atinge erro abaixo de 5% com apenas 7 amostras transmitidas
Mantém capacidade preditiva com erro inferior a 1% para horizontes de 2 minutos
Reduz significativamente o uso do canal de comunicação enquanto preserva a fidelidade da reconstrução
Fornece estimativas úteis desde os primeiros instantes de operação, sem necessidade de aguardar recepção completa dos dados

Trabalhos Relacionados
A literatura sobre monitoramento hidropônico abrange desde fundamentos agronômicos até sistemas IoT inteligentes, mas geralmente assume conectividade suficiente para transmissão contínua de dados. Protocolos leves como MQTT são amplamente adotados, mas focam na eficiência do transporte sem considerar o conteúdo semântico do sinal.
O Sensoriamento Comprimido (CS) oferece uma alternativa promissora, permitindo redução significativa no volume de dados transmitidos. A Compressive Field Estimation (CFE) estende esses princípios para reconstrução contínua de campos espaciais ou temporais, sendo aplicada com sucesso em cenários agrícolas. No entanto, abordagens existentes não incorporam explicitamente conhecimento semântico sobre a natureza dos parâmetros monitorados.

Conclusão e Trabalhos Futuros
O CFE-HYDRO apresenta-se como uma solução viável para o monitoramento de sistemas hidropônicos sob restrições severas de comunicação. A combinação de subamostragem aleatória, metadados semânticos e reconstrução seletiva permite reduzir o uso de banda sem comprometer a fidelidade dos sinais reconstruídos.

Direções Futuras de Pesquisa
Identificação automática da natureza dos sinais: Desenvolvimento de mecanismos capazes de identificar automaticamente o tipo de sinal a partir de suas características, reduzindo o overhead de comunicação
Implementação em ambientes operacionais reais: Avaliação do protocolo em condições práticas de operação
Integração de novos sensores e parâmetros: Extensão do protocolo para outros tipos de sensores agrícolas
Amostragem adaptativa: Estratégias que priorizem transmissão em momentos de maior incerteza na reconstrução
Modelos de previsão avançados: Incorporação de técnicas de aprendizado de máquina para melhorar capacidade preditiva

Recursos Disponíveis
Em aderência aos princípios da Ciência Aberta, disponibilizamos:
Dataset: Dados reais de sistema hidropônico utilizados na avaliação experimental
Documentação: Artigo com as Especificações técnicas

Autores
Autores: André L. Rocha, Paulo II. H. L. Rettore, Gustavo Figueiredo, Maycon Peixoto, Cássio Prazeres, Bruno P. Santos

Agradecimentos: CNPq, FAPESP, CGI.br, FAPESB
