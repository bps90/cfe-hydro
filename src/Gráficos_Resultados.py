"""
Função: Analisa resultados da simulação de interpolações com diferentes intervalos de amostras e mostra estatísticas e gráficos
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
import warnings

warnings.filterwarnings('ignore')

# ===================================================================
# 1. CARREGAR DADOS DOS RESULTADOS DA SIMULAÇÃO
# ===================================================================

print("="*60)
print("CARREGANDO DADOS DOS RESULTADOS DA SIMULAÇÃO")
print("="*60)

# Definir caminhos dos arquivos
resultados_path = './data/resultados_simulacao.csv'
dataset_path = './data/dataset_cfe-hydro.csv'

# Verificar se os arquivos existem
if not os.path.exists(resultados_path):
    print(f"ERRO: Arquivo '{resultados_path}' não encontrado!")
    print("Verifique se o arquivo está no diretório correto.")
    exit()

if not os.path.exists(dataset_path):
    print(f"ERRO: Arquivo '{dataset_path}' não encontrado!")
    print("Verifique se o arquivo está na pasta './data/'.")
    exit()

# Carregar os resultados da simulação
try:
    df_resultados = pd.read_csv(resultados_path)
    print(f"Resultados da simulação carregados: {len(df_resultados)} registros")
    
    # Corrigir a coluna de percentual (se estiver com 0)
    # Vamos calcular o percentual correto baseado no intervalo
    df_resultados['percentual_transmitido'] = 100 / df_resultados['intervalo']
    
    print("\nPrimeiras linhas dos resultados:")
    print(df_resultados.head())
    
except Exception as e:
    print(f"ERRO ao carregar resultados: {e}")
    exit()

# Carregar o dataset original para obter os valores dos parâmetros
try:
    df_original = pd.read_csv(dataset_path, sep=';', decimal='.')
    print(f"\nDataset original carregado: {len(df_original)} registros")
    
    # Converter timestamp se necessário
    if 'timestamp' in df_original.columns:
        df_original['timestamp'] = pd.to_datetime(df_original['timestamp'], format='%d/%m/%Y %H:%M')
    
except Exception as e:
    print(f"ERRO ao carregar dataset original: {e}")
    exit()

# ===================================================================
# 2. PREPARAR OS DADOS PARA OS GRÁFICOS 3D
# ===================================================================

print("\n" + "="*60)
print("PREPARANDO DADOS PARA GRÁFICOS 3D")
print("="*60)

# Obter valores únicos de cada parâmetro do dataset original
temp_unique = np.sort(df_original['temperatura'].unique())
ph_unique = np.sort(df_original['ph'].unique())
ec_unique = np.sort(df_original['ec'].unique())
od_unique = np.sort(df_original['od'].unique())

print("\nValores únicos por parâmetro (do dataset original):")
print(f"Temperatura: {len(temp_unique)} valores ({temp_unique.min():.1f} a {temp_unique.max():.1f} °C)")
print(f"pH: {len(ph_unique)} valores ({ph_unique.min():.2f} a {ph_unique.max():.2f})")
print(f"EC: {len(ec_unique)} valores ({ec_unique.min():.3f} a {ec_unique.max():.3f} mS/cm)")
print(f"OD: {len(od_unique)} valores ({od_unique.min():.2f} a {od_unique.max():.2f} ppm)")

# Intervalos da simulação
intervalos = df_resultados['intervalo'].values
print(f"\nIntervalos da simulação: {len(intervalos)} (de {intervalos.min()} a {intervalos.max()})")

# RMSE de cada parâmetro por intervalo
temp_rmse = df_resultados['temperatura_rmse'].values
ph_rmse = df_resultados['ph_rmse'].values
ec_rmse = df_resultados['ec_rmse'].values
od_rmse = df_resultados['od_rmse'].values

# R² de cada parâmetro por intervalo
temp_r2 = df_resultados['temperatura_r2'].values
ph_r2 = df_resultados['ph_r2'].values
ec_r2 = df_resultados['ec_r2'].values
od_r2 = df_resultados['od_r2'].values

print("\nRMSE por intervalo:")
for i, intervalo in enumerate(intervalos):
    print(f"Intervalo {intervalo}: Temp={temp_rmse[i]:.4f}, pH={ph_rmse[i]:.4f}, "
          f"EC={ec_rmse[i]:.4f}, OD={od_rmse[i]:.4f}")

# ===================================================================
# 3. FUNÇÃO PARA CRIAR SUPERFÍCIE 3D COM VISTA ISOMÉTRICA
# ===================================================================

def criar_superficie_3d(intervalos, valores_parametro, rmse_values, titulo, nome_parametro, unidade, output_file):
    """
    Cria um gráfico 3D de superfície com vista isométrica
    
    Args:
        intervalos: Array de intervalos (eixo X)
        valores_parametro: Array de valores do parâmetro (eixo Y)
        rmse_values: Array de RMSE para cada intervalo (eixo Z)
        titulo: Título do gráfico
        nome_parametro: Nome do parâmetro para o eixo Y
        unidade: Unidade do parâmetro
        output_file: Caminho para salvar o gráfico
    """
    
    # Criar grade para superfície 3D
    # X: Intervalos (1-10)
    # Y: Valores do parâmetro (temperatura, pH, EC, OD)
    # Z: RMSE
    
    X, Y = np.meshgrid(intervalos, valores_parametro)
    
    # Z será uma matriz onde cada coluna tem o mesmo valor (RMSE do intervalo)
    Z = np.zeros_like(X)
    for i, intervalo in enumerate(intervalos):
        Z[:, i] = rmse_values[i]
    
    # Criar figura
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Escolher mapa de cores baseado no parâmetro
    if 'Temperatura' in titulo:
        cmap = plt.cm.coolwarm
    elif 'pH' in titulo:
        cmap = plt.cm.viridis
    elif 'EC' in titulo:
        cmap = plt.cm.plasma
    elif 'OD' in titulo:
        cmap = plt.cm.spring
    else:
        cmap = plt.cm.viridis
    
    # Plotar superfície
    surf = ax.plot_surface(X, Y, Z, 
                          cmap=cmap, 
                          alpha=0.85, 
                          linewidth=0.5, 
                          antialiased=True,
                          edgecolor='gray',
                          rstride=1, cstride=1)
    
    # Configurar labels
    ax.set_xlabel('Intervalos de Transmissão', fontsize=12, labelpad=12)
    ax.set_ylabel(f'{nome_parametro} ({unidade})', fontsize=12, labelpad=12)
    ax.set_zlabel('RMSE', fontsize=12, labelpad=12)
    
    # Configurar título
    ax.set_title(titulo, fontsize=14, pad=20, weight='bold')
    
    # Configurar vista isométrica
    ax.view_init(elev=25, azim=45)
    
    # Configurar limites dos eixos
    ax.set_xlim(intervalos.min(), intervalos.max())
    ax.set_ylim(valores_parametro.min(), valores_parametro.max())
    ax.set_zlim(0, rmse_values.max() * 1.1)
    
    # Adicionar barra de cores
    cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=15, pad=0.1)
    cbar.set_label('RMSE', fontsize=11)
    cbar.ax.tick_params(labelsize=10)
    
    # Adicionar grade
    ax.grid(True, alpha=0.3)
    
    # Adicionar anotações para pontos críticos
    max_rmse_idx = np.argmax(rmse_values)
    ax.text(intervalos[max_rmse_idx], valores_parametro.mean(), rmse_values[max_rmse_idx] * 1.05,
            f'Max RMSE: {rmse_values[max_rmse_idx]:.4f}',
            color='red', fontsize=9, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    # Salvar gráfico
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  • Gráfico salvo: {output_file}")
    plt.show()
    
    return fig, ax

# ===================================================================
# 4. CRIAR GRÁFICOS 3D SEPARADOS
# ===================================================================

print("\n" + "="*60)
print("CRIANDO GRÁFICOS 3D DE SUPERFÍCIE")
print("="*60)

# Criar diretório para salvar gráficos se não existir
output_dir = './graficos_3d_resultados'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 1. Gráfico para TEMPERATURA
print("\n1. Criando gráfico 3D para Temperatura...")
criar_superficie_3d(
    intervalos=intervalos,
    valores_parametro=temp_unique,
    rmse_values=temp_rmse,
    titulo='SUPERFÍCIE 3D: TEMPERATURA vs RMSE vs INTERVALOS\nResultados da Simulação',
    nome_parametro='Temperatura',
    unidade='°C',
    output_file=f'{output_dir}/3d_temperatura_resultados.png'
)

# 2. Gráfico para pH
print("\n2. Criando gráfico 3D para pH...")
criar_superficie_3d(
    intervalos=intervalos,
    valores_parametro=ph_unique,
    rmse_values=ph_rmse,
    titulo='SUPERFÍCIE 3D: pH vs RMSE vs INTERVALOS\nResultados da Simulação',
    nome_parametro='pH',
    unidade='',
    output_file=f'{output_dir}/3d_ph_resultados.png'
)

# 3. Gráfico para EC
print("\n3. Criando gráfico 3D para EC...")
criar_superficie_3d(
    intervalos=intervalos,
    valores_parametro=ec_unique,
    rmse_values=ec_rmse,
    titulo='SUPERFÍCIE 3D: EC vs RMSE vs INTERVALOS\nResultados da Simulação',
    nome_parametro='Condutividade Elétrica',
    unidade='mS/cm',
    output_file=f'{output_dir}/3d_ec_resultados.png'
)

# 4. Gráfico para OD
print("\n4. Criando gráfico 3D para OD...")
criar_superficie_3d(
    intervalos=intervalos,
    valores_parametro=od_unique,
    rmse_values=od_rmse,
    titulo='SUPERFÍCIE 3D: OD vs RMSE vs INTERVALOS\nResultados da Simulação',
    nome_parametro='Oxigênio Dissolvido',
    unidade='ppm',
    output_file=f'{output_dir}/3d_od_resultados.png'
)

# ===================================================================
# 5. GRÁFICOS 3D COM PERCENTUAL DE TRANSMISSÃO
# ===================================================================

print("\n" + "="*60)
print("CRIANDO GRÁFICOS 3D COM PERCENTUAL DE TRANSMISSÃO")
print("="*60)

def criar_superficie_3d_percentual(percentuais, valores_parametro, rmse_values, r2_values, titulo, nome_parametro, unidade, output_file):
    """
    Cria um gráfico 3D de superfície usando percentual de transmissão no eixo X
    """
    
    X, Y = np.meshgrid(percentuais, valores_parametro)
    
    # Z será uma matriz onde cada coluna tem o mesmo valor (RMSE do percentual)
    Z = np.zeros_like(X)
    for i, percentual in enumerate(percentuais):
        Z[:, i] = rmse_values[i]
    
    # Criar figura
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Escolher mapa de cores
    if 'Temperatura' in titulo:
        cmap = plt.cm.coolwarm
    elif 'pH' in titulo:
        cmap = plt.cm.viridis
    elif 'EC' in titulo:
        cmap = plt.cm.plasma
    elif 'OD' in titulo:
        cmap = plt.cm.spring
    else:
        cmap = plt.cm.viridis
    
    # Plotar superfície
    surf = ax.plot_surface(X, Y, Z, 
                          cmap=cmap, 
                          alpha=0.85, 
                          linewidth=0.5, 
                          antialiased=True,
                          edgecolor='gray',
                          rstride=1, cstride=1)
    
    # Configurar labels
    ax.set_xlabel('Percentual de Dados Transmitidos (%)', fontsize=12, labelpad=12)
    ax.set_ylabel(f'{nome_parametro} ({unidade})', fontsize=12, labelpad=12)
    ax.set_zlabel('RMSE', fontsize=12, labelpad=12)
    
    # Configurar título
    ax.set_title(titulo, fontsize=14, pad=20, weight='bold')
    
    # Vista isométrica
    ax.view_init(elev=25, azim=45)
    
    # Adicionar barra de cores
    cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=15, pad=0.1)
    cbar.set_label('RMSE', fontsize=11)
    cbar.ax.tick_params(labelsize=10)
    
    # Salvar gráfico
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  • Gráfico salvo: {output_file}")
    plt.show()
    
    return fig, ax

# Percentuais de transmissão (calculados a partir dos intervalos)
percentuais = 100 / intervalos

print("\nCriando gráficos com percentual de transmissão...")

# Temperatura com percentual
criar_superficie_3d_percentual(
    percentuais=percentuais,
    valores_parametro=temp_unique,
    rmse_values=temp_rmse,
    r2_values=temp_r2,
    titulo='SUPERFÍCIE 3D: TEMPERATURA vs RMSE vs % TRANSMISSÃO',
    nome_parametro='Temperatura',
    unidade='°C',
    output_file=f'{output_dir}/3d_temperatura_percentual.png'
)

# pH com percentual
criar_superficie_3d_percentual(
    percentuais=percentuais,
    valores_parametro=ph_unique,
    rmse_values=ph_rmse,
    r2_values=ph_r2,
    titulo='SUPERFÍCIE 3D: pH vs RMSE vs % TRANSMISSÃO',
    nome_parametro='pH',
    unidade='',
    output_file=f'{output_dir}/3d_ph_percentual.png'
)

# EC com percentual
criar_superficie_3d_percentual(
    percentuais=percentuais,
    valores_parametro=ec_unique,
    rmse_values=ec_rmse,
    r2_values=ec_r2,
    titulo='SUPERFÍCIE 3D: EC vs RMSE vs % TRANSMISSÃO',
    nome_parametro='Condutividade Elétrica',
    unidade='mS/cm',
    output_file=f'{output_dir}/3d_ec_percentual.png'
)

# OD com percentual
criar_superficie_3d_percentual(
    percentuais=percentuais,
    valores_parametro=od_unique,
    rmse_values=od_rmse,
    r2_values=od_r2,
    titulo='SUPERFÍCIE 3D: OD vs RMSE vs % TRANSMISSÃO',
    nome_parametro='Oxigênio Dissolvido',
    unidade='ppm',
    output_file=f'{output_dir}/3d_od_percentual.png'
)

# ===================================================================
# 6. ANÁLISE ESTATÍSTICA DOS RESULTADOS
# ===================================================================

print("\n" + "="*60)
print("ANÁLISE ESTATÍSTICA DOS RESULTADOS")
print("="*60)

# Calcular estatísticas para cada parâmetro
print("\n1. ESTATÍSTICAS DE RMSE POR PARÂMETRO:")

parametros = ['Temperatura', 'pH', 'EC', 'OD']
rmse_dados = [temp_rmse, ph_rmse, ec_rmse, od_rmse]
r2_dados = [temp_r2, ph_r2, ec_r2, od_r2]

for i, (param, rmse_vals, r2_vals) in enumerate(zip(parametros, rmse_dados, r2_dados)):
    print(f"\n   {param}:")
    print(f"     • RMSE médio: {rmse_vals.mean():.4f}")
    print(f"     • RMSE máximo: {rmse_vals.max():.4f} (Intervalo {intervalos[np.argmax(rmse_vals)]})")
    print(f"     • RMSE mínimo: {rmse_vals.min():.4f} (Intervalo {intervalos[np.argmin(rmse_vals)]})")
    print(f"     • R² médio: {r2_vals.mean():.4f}")
    print(f"     • R² mínimo: {r2_vals.min():.4f}")

# Calcular correlações entre RMSE de diferentes parâmetros
print("\n2. CORRELAÇÕES ENTRE RMSE DOS PARÂMETROS:")
rmse_df = pd.DataFrame({
    'temp_rmse': temp_rmse,
    'ph_rmse': ph_rmse,
    'ec_rmse': ec_rmse,
    'od_rmse': od_rmse
})
corr_matrix = rmse_df.corr()

print("\nMatriz de correlação:")
print(corr_matrix.round(3))

# Identificar correlações fortes
print("\nCorrelações significativas (|r| > 0.7):")
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        corr_value = corr_matrix.iloc[i, j]
        if abs(corr_value) > 0.7:
            param1 = corr_matrix.columns[i].replace('_rmse', '').upper()
            param2 = corr_matrix.columns[j].replace('_rmse', '').upper()
            if param1 == 'TEMP': param1 = 'Temperatura'
            if param2 == 'TEMP': param2 = 'Temperatura'
            print(f"   {param1} vs {param2}: r = {corr_value:.3f}")

# Análise de degradação com redução da transmissão
print("\n3. ANÁLISE DE DEGRADAÇÃO COM REDUÇÃO DA TRANSMISSÃO:")

# Calcular taxa de degradação (RMSE no último intervalo / RMSE no primeiro intervalo não nulo)
for i, (param, rmse_vals) in enumerate(zip(parametros, rmse_dados)):
    # Encontrar primeiro intervalo com RMSE não nulo (geralmente intervalo 2)
    idx_primeiro = np.where(rmse_vals > 0)[0]
    if len(idx_primeiro) > 0:
        idx_primeiro = idx_primeiro[0]
        rmse_inicial = rmse_vals[idx_primeiro]
        rmse_final = rmse_vals[-1]
        fator_aumento = rmse_final / rmse_inicial if rmse_inicial > 0 else float('inf')
        
        print(f"   {param}:")
        print(f"     • RMSE inicial (intervalo {intervalos[idx_primeiro]}): {rmse_inicial:.4f}")
        print(f"     • RMSE final (intervalo {intervalos[-1]}): {rmse_final:.4f}")
        print(f"     • Fator de aumento: {fator_aumento:.2f}x")

# ===================================================================
# 7. GRÁFICOS ADICIONAIS: EVOLUÇÃO DO RMSE E R²
# ===================================================================

print("\n" + "="*60)
print("CRIANDO GRÁFICOS ADICIONAIS DE EVOLUÇÃO")
print("="*60)

# Gráfico 2D de evolução do RMSE por intervalo
fig1, axes1 = plt.subplots(2, 2, figsize=(15, 10))
fig1.suptitle('EVOLUÇÃO DO RMSE POR INTERVALO DE TRANSMISSÃO', fontsize=16, weight='bold')

# Temperatura
axes1[0, 0].plot(intervalos, temp_rmse, 'o-', linewidth=2, markersize=8, color='red')
axes1[0, 0].set_xlabel('Intervalo')
axes1[0, 0].set_ylabel('RMSE')
axes1[0, 0].set_title('Temperatura', fontsize=12, weight='bold')
axes1[0, 0].grid(True, alpha=0.3)
axes1[0, 0].fill_between(intervalos, 0, temp_rmse, alpha=0.2, color='red')

# pH
axes1[0, 1].plot(intervalos, ph_rmse, 'o-', linewidth=2, markersize=8, color='blue')
axes1[0, 1].set_xlabel('Intervalo')
axes1[0, 1].set_ylabel('RMSE')
axes1[0, 1].set_title('pH', fontsize=12, weight='bold')
axes1[0, 1].grid(True, alpha=0.3)
axes1[0, 1].fill_between(intervalos, 0, ph_rmse, alpha=0.2, color='blue')

# EC
axes1[1, 0].plot(intervalos, ec_rmse, 'o-', linewidth=2, markersize=8, color='green')
axes1[1, 0].set_xlabel('Intervalo')
axes1[1, 0].set_ylabel('RMSE')
axes1[1, 0].set_title('Condutividade Elétrica (EC)', fontsize=12, weight='bold')
axes1[1, 0].grid(True, alpha=0.3)
axes1[1, 0].fill_between(intervalos, 0, ec_rmse, alpha=0.2, color='green')

# OD
axes1[1, 1].plot(intervalos, od_rmse, 'o-', linewidth=2, markersize=8, color='orange')
axes1[1, 1].set_xlabel('Intervalo')
axes1[1, 1].set_ylabel('RMSE')
axes1[1, 1].set_title('Oxigênio Dissolvido (OD)', fontsize=12, weight='bold')
axes1[1, 1].grid(True, alpha=0.3)
axes1[1, 1].fill_between(intervalos, 0, od_rmse, alpha=0.2, color='orange')

plt.tight_layout()
plt.savefig(f'{output_dir}/evolucao_rmse.png', dpi=300, bbox_inches='tight')
print(f"  • Gráfico de evolução do RMSE salvo: {output_dir}/evolucao_rmse.png")
plt.show()

# Gráfico 2D de evolução do R² por intervalo
fig2, axes2 = plt.subplots(2, 2, figsize=(15, 10))
fig2.suptitle('EVOLUÇÃO DO R² POR INTERVALO DE TRANSMISSÃO', fontsize=16, weight='bold')

# Temperatura
axes2[0, 0].plot(intervalos, temp_r2, 'o-', linewidth=2, markersize=8, color='red')
axes2[0, 0].set_xlabel('Intervalo')
axes2[0, 0].set_ylabel('R²')
axes2[0, 0].set_title('Temperatura', fontsize=12, weight='bold')
axes2[0, 0].grid(True, alpha=0.3)
axes2[0, 0].axhline(y=0.95, color='gray', linestyle='--', alpha=0.5, label='Limite 0.95')
axes2[0, 0].legend()

# pH
axes2[0, 1].plot(intervalos, ph_r2, 'o-', linewidth=2, markersize=8, color='blue')
axes2[0, 1].set_xlabel('Intervalo')
axes2[0, 1].set_ylabel('R²')
axes2[0, 1].set_title('pH', fontsize=12, weight='bold')
axes2[0, 1].grid(True, alpha=0.3)
axes2[0, 1].axhline(y=0.95, color='gray', linestyle='--', alpha=0.5, label='Limite 0.95')
axes2[0, 1].legend()

# EC
axes2[1, 0].plot(intervalos, ec_r2, 'o-', linewidth=2, markersize=8, color='green')
axes2[1, 0].set_xlabel('Intervalo')
axes2[1, 0].set_ylabel('R²')
axes2[1, 0].set_title('Condutividade Elétrica (EC)', fontsize=12, weight='bold')
axes2[1, 0].grid(True, alpha=0.3)
axes2[1, 0].axhline(y=0.95, color='gray', linestyle='--', alpha=0.5, label='Limite 0.95')
axes2[1, 0].legend()

# OD
axes2[1, 1].plot(intervalos, od_r2, 'o-', linewidth=2, markersize=8, color='orange')
axes2[1, 1].set_xlabel('Intervalo')
axes2[1, 1].set_ylabel('R²')
axes2[1, 1].set_title('Oxigênio Dissolvido (OD)', fontsize=12, weight='bold')
axes2[1, 1].grid(True, alpha=0.3)
axes2[1, 1].axhline(y=0.95, color='gray', linestyle='--', alpha=0.5, label='Limite 0.95')
axes2[1, 1].legend()

plt.tight_layout()
plt.savefig(f'{output_dir}/evolucao_r2.png', dpi=300, bbox_inches='tight')
print(f"  • Gráfico de evolução do R² salvo: {output_dir}/evolucao_r2.png")
plt.show()

# ===================================================================
# 8. RESUMO E RECOMENDAÇÕES
# ===================================================================

print("\n" + "="*60)
print("RESUMO E RECOMENDAÇÕES")
print("="*60)

print("\n1. RESUMO DOS RESULTADOS:")
print(f"   • Total de intervalos analisados: {len(intervalos)}")
print(f"   • Percentual de transmissão variando de {percentuais[0]:.0f}% a {percentuais[-1]:.0f}%")
print(f"   • Parâmetros analisados: Temperatura, pH, EC, OD")

print("\n2. COMPORTAMENTO POR PARÂMETRO:")
print("   • Temperatura: RMSE aumenta gradualmente com redução da transmissão")
print("   • pH: Mantém RMSE baixo (0.0) na maioria dos intervalos, exceto intervalo 2")
print("   • EC: Mostra maior variação de RMSE entre intervalos")
print("   • OD: Aumento consistente e quase linear do RMSE")

print("\n3. RECOMENDAÇÕES PARA TRANSMISSÃO:")
print("   • Para Temperatura e OD: Manter acima de 50% de transmissão para RMSE < 0.1")
print("   • Para pH: Pode reduzir significativamente a transmissão sem grande impacto")
print("   • Para EC: Necessário monitoramento mais cuidadoso devido à maior variação")
print("   • Intervalo ideal: 3-5 (33-20% de transmissão) para equilíbrio qualidade/eficiência")

print("\n" + "="*60)
print("EXECUÇÃO COMPLETADA COM SUCESSO!")
print("="*60)
print(f"• Resultados processados: {len(df_resultados)} intervalos")
print(f"• Gráficos 3D gerados: 8")
print(f"• Gráficos 2D adicionais: 2")
print(f"• Todos os gráficos salvos em: '{output_dir}/'")
print(f"• Análise estatística completa realizada")

