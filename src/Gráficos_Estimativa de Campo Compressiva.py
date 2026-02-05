import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

# Configuração inicial
ESPACAMENTO = 5
N_LEITURAS = 50
MIN_PH = 5.5
MAX_PH = 8.5

# Carrega dados do Dataset
def ler_dados_csv(nome_arquivo='./data/dataset_cfe-hydro.csv'):
    """Lê dados de pH de arquivo CSV com delimitador ';', decimal '.' """
    try:
        # Ler CSV com delimitador ';' e converter vírgula para ponto decimal
        df = pd.read_csv(nome_arquivo, sep=';', decimal='.')
        print(f"Arquivo '{nome_arquivo}' carregado com sucesso!")
        print(f"Colunas encontradas: {list(df.columns)}")
        
        # Verificar qual coluna tem os dados de pH
        if 'ph' in df.columns:
            ph_valores = df['ph'].values
        elif 'pH' in df.columns:
            ph_valores = df['pH'].values
        else:
            # Pegar a segunda coluna (assumindo que a primeira é 'id')
            ph_valores = df.iloc[:, 1].values
        
        print(f"Total de leituras: {len(ph_valores)}")
        return ph_valores
    
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        print("Usando dados padrão...")
        # Dados fornecidos como fallback
        dados = [
            5.94, 5.96, 5.94, 5.92, 5.98, 5.99, 5.95, 6.00, 6.48, 6.47,
            6.73, 6.94, 6.22, 6.43, 6.48, 6.42, 6.50, 6.39, 6.51, 6.55,
            6.27, 6.37, 6.05, 6.09, 6.04, 6.00, 6.27, 6.17, 6.22, 6.21,
            6.24, 6.13, 6.26, 6.38, 6.29, 8.50, 7.26, 8.50, 6.87, 6.65,
            6.61, 6.73, 6.77, 6.77, 6.99, 6.70, 6.58, 6.36, 6.37, 6.52
        ]
        return np.array(dados)

# Carregar dados
ph_original = ler_dados_csv('./data/dataset_cfe-hydro.csv')

# Verificar se temos o número correto de leituras
if len(ph_original) != N_LEITURAS:
    print(f"Aviso: Número de leituras ({len(ph_original)}) diferente do esperado ({N_LEITURAS})")
    N_LEITURAS = len(ph_original)

# Funções de Interpolação com Espaçamento configurável
def interpolar_linear_npontos(valores, espacamento=ESPACAMENTO):
    """Interpola linearmente mantendo 1 ponto a cada N leituras"""
    n = len(valores)
    resultado = np.zeros(n)
    
    for i in range(n):
        if i % espacamento == 0:
            resultado[i] = valores[i]
        else:
            idx_anterior = i - (i % espacamento)
            idx_proximo = idx_anterior + espacamento
            
            if idx_proximo >= n:
                resultado[i] = valores[idx_anterior]
            else:
                fator = (i - idx_anterior) / espacamento
                resultado[i] = valores[idx_anterior] + fator * (valores[idx_proximo] - valores[idx_anterior])
    
    return resultado

def interpolar_logaritmica_npontos(ph_valores, espacamento=ESPACAMENTO):
    """Interpola logaritmicamente mantendo 1 ponto a cada N leituras"""
    n = len(ph_valores)
    resultado = np.zeros(n)
    
    for i in range(n):
        if i % espacamento == 0:
            resultado[i] = ph_valores[i]
        else:
            idx_anterior = i - (i % espacamento)
            idx_proximo = idx_anterior + espacamento
            
            if idx_proximo >= n:
                resultado[i] = ph_valores[idx_anterior]
            else:
                # Converter para concentração [H+]
                h_anterior = 10 ** (-ph_valores[idx_anterior])
                h_proximo = 10 ** (-ph_valores[idx_proximo])
                
                # Interpolar linearmente concentrações
                fator = (i - idx_anterior) / espacamento
                h_interpolado = h_anterior + fator * (h_proximo - h_anterior)
                
                # Converter de volta para pH
                resultado[i] = -np.log10(h_interpolado)
    
    return resultado

# Calcular interpolações
interp_linear = interpolar_linear_npontos(ph_original, ESPACAMENTO)
interp_log = interpolar_logaritmica_npontos(ph_original, ESPACAMENTO)

# Calcular erros
erro_linear = np.abs(ph_original - interp_linear)
erro_log = np.abs(ph_original - interp_log)

# GRÁFICO 1a: Comparação
plt.figure(figsize=(14, 6))

# Plot principal
plt.plot(range(N_LEITURAS), ph_original, 'k-', linewidth=3, 
         label='pH Original', alpha=0.8)

plt.plot(range(N_LEITURAS), interp_linear, 'r--', linewidth=2.5, 
         label=f'Interpolação Linear (1 a cada {ESPACAMENTO})')

plt.plot(range(N_LEITURAS), interp_log, 'b-.', linewidth=2.5, 
         label=f'Interpolação Logarítmica (1 a cada {ESPACAMENTO})')

# Destacar pontos transmitidos
pontos_transmitidos = range(0, N_LEITURAS, ESPACAMENTO)
valores_transmitidos = ph_original[pontos_transmitidos]
plt.scatter(pontos_transmitidos, valores_transmitidos, 
           color='green', s=100, zorder=5, 
           label=f'Pontos Transmitidos (1/{ESPACAMENTO})', 
           edgecolors='black', linewidth=1.5)

# Configurar eixos
plt.xlabel(f'Intervalos ({N_LEITURAS} leituras de pH)', fontsize=12)
plt.ylabel('Valor do pH', fontsize=12)
plt.title(f'Comparação: Interpolação Linear vs Logarítmica (Esparsidade: 1/{ESPACAMENTO})', 
          fontsize=14, fontweight='bold')

plt.ylim(5.5, 9.0)  # Ajustado para incluir 8.5
plt.xlim(0, N_LEITURAS - 1)

# Grade
plt.grid(True, alpha=0.3, linestyle='--')

# Linhas verticais a cada 10 intervalos
for i in range(0, N_LEITURAS, 10):
    plt.axvline(x=i, color='gray', linestyle=':', alpha=0.5)

# Legenda
plt.legend(loc='upper left', fontsize=10)

# Adicionar estatísticas
erro_medio_linear = np.mean(erro_linear)
erro_medio_log = np.mean(erro_log)
reducao_percentual = (1 - erro_medio_log/erro_medio_linear) * 100 if erro_medio_linear > 0 else 0

info_text = f'Estatísticas (1/{ESPACAMENTO}):\n'
info_text += f'Erro Médio Linear: {erro_medio_linear:.3f}\n'
info_text += f'Erro Médio Log: {erro_medio_log:.3f}\n'
info_text += f'Redução: {reducao_percentual:.1f}%'

plt.text(0.85, 0.98, info_text,
         transform=plt.gca().transAxes,
         fontsize=10, 
         verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8)
)

plt.tight_layout()
plt.show()

# GRÁFICO 1b: Erro Absoluto (RMSE)
plt.figure(figsize=(14, 5))

x = np.arange(N_LEITURAS)
largura = 0.35

plt.bar(x - largura/2, erro_linear, largura, 
        color='red', alpha=0.7, label='Erro Linear')
plt.bar(x + largura/2, erro_log, largura, 
        color='blue', alpha=0.7, label='Erro Logarítmico')

# Linhas de média
plt.axhline(y=erro_medio_linear, color='darkred', 
           linestyle=':', linewidth=2, label=f'Média: {erro_medio_linear:.3f}')
plt.axhline(y=erro_medio_log, color='darkblue', 
           linestyle=':', linewidth=2, label=f'Média: {erro_medio_log:.3f}')

plt.xlabel('Índice da Leitura', fontsize=11)
plt.ylabel('Erro Absoluto (unidades pH)', fontsize=11)
plt.title(f'Erro Absoluto (RMSE) - (Esparsidade: 1/{ESPACAMENTO})', fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3, axis='y')
plt.legend(loc='upper left', fontsize=9)

plt.tight_layout()
plt.show()

# GRÁFICO 1c: Comparação das Interpolações (Erros)
plt.figure(figsize=(14, 5))

diferenca_erros = erro_linear - erro_log
cores = ['green' if diff > 0 else 'red' for diff in diferenca_erros]

bars = plt.bar(range(N_LEITURAS), diferenca_erros, color=cores, alpha=0.7)
plt.axhline(y=0, color='black', linewidth=1)

# Destacar diferenças significativas
for i in range(N_LEITURAS):
    if abs(diferenca_erros[i]) > 0.1:  # Limite maior para dados reais
        sinal = '+' if diferenca_erros[i] > 0 else ''
        plt.annotate(f'{sinal}{diferenca_erros[i]:.2f}', 
                    xy=(i, diferenca_erros[i]), 
                    xytext=(i, diferenca_erros[i] + 0.05 if diferenca_erros[i] > 0 else diferenca_erros[i] - 0.05),
                    ha='center', fontsize=8, fontweight='bold')

plt.xlabel('Índice da Leitura', fontsize=11)
plt.ylabel('Diferença (Linear - Log)', fontsize=11)
plt.title('Comparação das Interpolações (Erros)', fontsize=12, fontweight='bold')
plt.grid(True, alpha=0.3, axis='y')

# Legenda de cores
legend_elements = [
    Patch(facecolor='green', alpha=0.7, label='Interpolação Logarítmica'),
    Patch(facecolor='red', alpha=0.7, label='Interpolação Linear')
]
plt.legend(handles=legend_elements, loc='upper left', fontsize=9)

plt.tight_layout()
plt.show()

# Testar diferentes esparsidades
esparsidades = [3, 5, 7, 10]
resultados = []
for esp in esparsidades:
    interp_linear_esp = interpolar_linear_npontos(ph_original, esp)
    interp_log_esp = interpolar_logaritmica_npontos(ph_original, esp)
    
    erro_linear_esp = np.mean(np.abs(ph_original - interp_linear_esp))
    erro_log_esp = np.mean(np.abs(ph_original - interp_log_esp))
    
    resultados.append({
        'espacamento': esp,
        'erro_linear': erro_linear_esp,
        'erro_log': erro_log_esp,
        'reducao': (1 - erro_log_esp/erro_linear_esp) * 100 if erro_linear_esp > 0 else 0,
        'taxa_transmissao': 100/esp  # Porcentagem de pontos transmitidos
    })

# GRÁFICO 1d: Impacto da Esparsidade na Precisão
plt.figure(figsize=(12, 5))

x_pos = np.arange(len(esparsidades))
largura = 0.35

# Extrair dados
erros_linear = [r['erro_linear'] for r in resultados]
erros_log = [r['erro_log'] for r in resultados]
taxas = [r['taxa_transmissao'] for r in resultados]

plt.bar(x_pos - largura/2, erros_linear, largura, 
        color='orange', alpha=0.7, label='Erro Linear Médio')
plt.bar(x_pos + largura/2, erros_log, largura, 
        color='lightblue', alpha=0.7, label='Erro Logarítmico Médio')
#plt.bar(x_pos + largura/2, taxas, largura, 
#        color='lightblue', alpha=0.7, label='Taxa de Transmissão (%)')

plt.xlabel('Esparsidade (1 ponto a cada N leituras)', fontsize=12)
plt.ylabel('Erro Absoluto Médio (unidades pH)', fontsize=10)
plt.title('Impacto da Esparsidade na Precisão', fontsize=14, fontweight='bold')
plt.xticks(x_pos, [f'1/{esp}' for esp in esparsidades])
plt.grid(True, alpha=0.3, axis='y')
plt.legend(loc='upper left')

# Adicionar valores nas barras
for i, (erro_l, erro_log_val) in enumerate(zip(erros_linear, erros_log)):
    plt.text(i - largura/2, erro_l + 0.005, f'{erro_l:.3f}', 
             ha='center', fontsize=9)
    plt.text(i + largura/2, erro_log_val + 0.005, f'{erro_log_val:.3f}', 
             ha='center', fontsize=9)

# Adicionar linha da taxa de transmissão no segundo eixo
ax2 = plt.gca().twinx()
ax2.plot(x_pos, taxas, 'g-o', linewidth=2, markersize=8, label='Taxa de Transmissão (%)')
ax2.set_ylabel('Taxa de Transmissão (%)', fontsize=10, color='green')
ax2.tick_params(axis='y', labelcolor='green')
ax2.set_ylim(0, 50)

# Linhas horizontais para referência
for i, taxa in enumerate(taxas):
    ax2.text(i, taxa + 2, f'{taxa:.1f}%', ha='center', fontsize=9, color='green')

plt.tight_layout()
plt.show()

# Resumo Estatístico
print("="*70)
print(f"ANÁLISE DE INTERPOLAÇÃO COM ESPARSIDADE: 1/{ESPACAMENTO}")
print("="*70)

print(f"\nCONFIGURAÇÃO:")
print(f"  • Total de leituras: {N_LEITURAS}")
print(f"  • Esparsidade: 1 ponto transmitido a cada {ESPACAMENTO} leituras")
print(f"  • Pontos transmitidos: {len(pontos_transmitidos)} de {N_LEITURAS} ({100/ESPACAMENTO:.1f}%)")
print(f"  • Faixa observada: {np.min(ph_original):.2f} a {np.max(ph_original):.2f}")

print(f"\nESTATÍSTICAS DOS DADOS REAIS:")
print(f"  • Mínimo: {np.min(ph_original):.2f}")
print(f"  • Máximo: {np.max(ph_original):.2f}")
print(f"  • Média: {np.mean(ph_original):.2f}")
print(f"  • Mediana: {np.median(ph_original):.2f}")
print(f"  • Desvio padrão: {np.std(ph_original):.2f}")

print(f"\nVALORES ATÍPICOS DETECTADOS:")
for i, valor in enumerate(ph_original):
    if valor > 7.5 or valor < 5.8:  # Limites para considerar atípico
        print(f"  • Índice {i}: {valor:.2f}")

print(f"\nDESEMPENHO DAS INTERPOLAÇÕES (ERRO ABSOLUTO MÉDIO):")
print(f"  • Interpolação Linear: {erro_medio_linear:.4f}")
print(f"  • Interpolação Logarítmica: {erro_medio_log:.4f}")
print(f"  • Melhoria: {reducao_percentual:.1f}%")

print(f"\nANÁLISE DETALHADA DOS ERROS:")
print(f"  • Máximo erro Linear: {np.max(erro_linear):.3f} (índice {np.argmax(erro_linear)})")
print(f"  • Máximo erro Logarítmico: {np.max(erro_log):.3f} (índice {np.argmax(erro_log)})")
print(f"  • Pontos onde Logarítmica é >0.1 melhor: {np.sum(diferenca_erros > 0.1)}")
print(f"  • Pontos onde Linear é >0.1 melhor: {np.sum(diferenca_erros < -0.1)}")

print(f"\nCOMPARAÇÃO DE DIFERENTES ESPARSIDADES:")
print(f"{'Esparsidade':<12} {'Erro Linear':<12} {'Erro Log':<12} {'Redução':<10} {'Tx Transmissão':<15}")
print("-" * 65)
for r in resultados:
    print(f"{'1/' + str(r['espacamento']):<12} {r['erro_linear']:<12.4f} {r['erro_log']:<12.4f} "
          f"{r['reducao']:<10.1f}% {r['taxa_transmissao']:<15.1f}%")

print("\nOBSERVAÇÕES:")
print("1. O Dataset contém valores atípicos (ex: 8.50 nos índices 35 e 37)")
print("2. A interpolação logarítmica é particularmente importante para valores extremos")
print("3. Em regiões estáveis, ambas as interpolações performam similarmente")
print("4. Em transições bruscas, a interpolação logarítmica preserva melhor a fidelidade")
print("5. A esparsidade 1/3 oferece melhor reconstrução mas transmite mais dados")
print("="*70)

# Criar DataFrame com resultados
df_resultados = pd.DataFrame({
    'indice': range(N_LEITURAS),
    'ph_original': ph_original,
    'interpolacao_linear': interp_linear,
    'interpolacao_logaritmica': interp_log,
    'erro_linear': erro_linear,
    'erro_logaritmico': erro_log,
    'transmitido': [1 if i % ESPACAMENTO == 0 else 0 for i in range(N_LEITURAS)]
})

# Salvar resultados
df_resultados.to_csv('resultados_interpolacao.csv', index=False, float_format='%.3f')
print(f"\nResultados salvos em 'resultados_interpolacao.csv'")
print(f"Arquivo contém {len(df_resultados)} linhas com dados de interpolação")
