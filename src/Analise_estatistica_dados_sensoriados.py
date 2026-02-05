"""
Função: Analisa os dados sensoriados, armazenados no dataset './data/resultados_simulacao.csv' e gera estatísticas e gráficos
"""

import os
import csv
import math
import statistics
from datetime import datetime

# Importações com tratamento de erro robusto
try:
    import numpy as np
except ImportError as e:
    print(f"Erro ao importar numpy: {e}")
    print("Execute: pip install numpy")
    exit(1)

try:
    import pandas as pd
except ImportError as e:
    print(f"Erro ao importar pandas: {e}")
    print("Execute: pip install pandas")
    exit(1)

# Tentar importar bibliotecas opcionais
try:
    from scipy.interpolate import interp1d
    SCIPY_AVAILABLE = True
except ImportError:
    print("Scipy não disponível - usando interpolação linear simples")
    SCIPY_AVAILABLE = False

try:
    from sklearn.metrics import r2_score, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    print("Scikit-learn não disponível - usando implementação própria de métricas")
    SKLEARN_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("Matplotlib não disponível - gráficos desabilitados")
    MATPLOTLIB_AVAILABLE = False

class SimpleInterpolator:
    """Implementação simples de interpolação sem dependências externas"""
    
    @staticmethod
    def linear_interpolation(ids, values):
        # Interpolação linear simples
        ids = [float(x) for x in ids]  # Garantir que IDs são numéricos
        values = [float(x) if x is not None and str(x).replace(',', '').replace('.', '').isdigit() else float('nan') for x in values]
        result = values.copy()
        
        # Encontrar índices com valores conhecidos
        known_indices = [i for i, val in enumerate(values) if not math.isnan(val)]
        
        for i in range(len(known_indices) - 1):
            start_idx = known_indices[i]
            end_idx = known_indices[i + 1]
            
            if end_idx - start_idx > 1:
                start_id = ids[start_idx]
                end_id = ids[end_idx]
                start_val = values[start_idx]
                end_val = values[end_idx]
                
                # Interpolar valores intermediários
                for j in range(start_idx + 1, end_idx):
                    current_id = ids[j]
                    factor = (current_id - start_id) / (end_id - start_id)
                    result[j] = start_val + (end_val - start_val) * factor
        
        return result
    
    @staticmethod
    def conservative_interpolation(ids, values, max_gap=2):
        # Interpolação conservadora para parâmetros sensíveis
        ids = [float(x) for x in ids]  # Garantir que IDs são numéricos
        values = [float(x) if x is not None and str(x).replace(',', '').replace('.', '').isdigit() else float('nan') for x in values]
        result = values.copy()
        
        known_indices = [i for i, val in enumerate(values) if not math.isnan(val)]
        
        for i in range(len(known_indices) - 1):
            start_idx = known_indices[i]
            end_idx = known_indices[i + 1]
            gap_size = end_idx - start_idx
            
            if 1 < gap_size <= max_gap:
                start_id = ids[start_idx]
                end_id = ids[end_idx]
                start_val = values[start_idx]
                end_val = values[end_idx]
                
                for j in range(start_idx + 1, end_idx):
                    current_id = ids[j]
                    factor = (current_id - start_id) / (end_id - start_id)
                    result[j] = start_val + (end_val - start_val) * factor
        
        return result

class MetricCalculator:
    # Calculadora de métricas sem dependência do scikit-learn
    
    @staticmethod
    def r2_score(y_true, y_pred):
        """Calcula R² manualmente"""
        # Converter para float, tratando vírgula como separador decimal
        y_true_clean = []
        y_pred_clean = []
        
        for i in range(min(len(y_true), len(y_pred))):
            try:
                # Tentar converter para float, tratando vírgula
                val_true = float(str(y_true[i]).replace(',', '.')) if y_true[i] is not None else float('nan')
                val_pred = float(str(y_pred[i]).replace(',', '.')) if y_pred[i] is not None else float('nan')
                
                if not math.isnan(val_true) and not math.isnan(val_pred):
                    y_true_clean.append(val_true)
                    y_pred_clean.append(val_pred)
            except (ValueError, TypeError):
                continue
        
        if len(y_true_clean) < 2:
            return float('nan')
        
        y_mean = statistics.mean(y_true_clean)
        
        ss_tot = sum((y - y_mean) ** 2 for y in y_true_clean)
        ss_res = sum((y_true_clean[i] - y_pred_clean[i]) ** 2 for i in range(len(y_true_clean)))
        
        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0
        
        return 1 - (ss_res / ss_tot)
    
    @staticmethod
    def rmse(y_true, y_pred):
        # Calcula RMSE manualmente
        # Converter para float, tratando vírgula como separador decimal
        y_true_clean = []
        y_pred_clean = []
        
        for i in range(min(len(y_true), len(y_pred))):
            try:
                val_true = float(str(y_true[i]).replace(',', '.')) if y_true[i] is not None else float('nan')
                val_pred = float(str(y_pred[i]).replace(',', '.')) if y_pred[i] is not None else float('nan')
                
                if not math.isnan(val_true) and not math.isnan(val_pred):
                    y_true_clean.append(val_true)
                    y_pred_clean.append(val_pred)
            except (ValueError, TypeError):
                continue
        
        if len(y_true_clean) < 1:
            return float('nan')
        
        mse = sum((y_true_clean[i] - y_pred_clean[i]) ** 2 for i in range(len(y_true_clean))) / len(y_true_clean)
        return math.sqrt(mse)

class AnalisadorInterpolacaoCorrigido:
    def __init__(self, arquivo_dataset):
        # Inicializa o analisador com o dataset
        self.df = self.carregar_dataset_corrigido(arquivo_dataset)
        self.resultados = {}
        self.interpolator = SimpleInterpolator()
        self.metric_calculator = MetricCalculator()
        
    def carregar_dataset_corrigido(self, arquivo):
        # Carrega o dataset CSV corrigindo problemas de vírgula decimal
        print("Carregando dataset...")
        
        try:
            # Primeiro, ler como string para processamento manual
            df_str = pd.read_csv(arquivo, sep=';', dtype=str, encoding='utf-8')
            
            # Converter colunas numéricas, tratando vírgula como ponto decimal
            colunas_numericas = ['id', 'temperatura', 'ph', 'ec', 'od']
            
            for coluna in colunas_numericas:
                if coluna in df_str.columns:
                    # Substituir vírgula por ponto e converter para float
                    df_str[coluna] = df_str[coluna].str.replace(',', '.', regex=False)
                    df_str[coluna] = pd.to_numeric(df_str[coluna], errors='coerce')
            
            print(f"Dataset carregado com sucesso: {df_str.shape[0]} linhas, {df_str.shape[1]} colunas")
            
        except Exception as e:
            print(f"Erro ao carregar com pandas: {e}")
            print("Tentando carregar manualmente...")
            df_str = self._carregar_dataset_manual(arquivo)
        
        # Verificar estrutura
        print(f"Estrutura do dataset: {df_str.shape}")
        print(f"Colunas: {df_str.columns.tolist()}")
        print(f"Primeiras linhas:")
        print(df_str.head().to_string())
        
        # Verificar valores nulos e estatísticas básicas
        print(f"\nEstatísticas básicas:")
        for coluna in ['temperatura', 'ph', 'ec', 'od']:
            if coluna in df_str.columns:
                nulos = df_str[coluna].isna().sum()
                if nulos == 0:
                    media = df_str[coluna].mean()
                    std = df_str[coluna].std()
                    print(f"   {coluna.upper():<6}: Média = {media:.3f}, Desvio = {std:.3f}, Nulos = {nulos}")
                else:
                    print(f"   {coluna.upper():<6}: Nulos = {nulos}")
        
        return df_str
    
    def _carregar_dataset_manual(self, arquivo):
        # Carrega dataset manualmente se o pandas falhar
        dados = []
        with open(arquivo, 'r', encoding='utf-8') as f:
            leitor = csv.reader(f, delimiter=';')
            cabecalho = next(leitor)
            
            for linha_num, linha in enumerate(leitor, start=2):
                if len(linha) == len(cabecalho):
                    # Processar cada valor, convertendo vírgula para ponto
                    linha_processada = []
                    for valor in linha:
                        if ',' in str(valor) and valor.replace(',', '').replace('.', '').isdigit():
                            # É um número com vírgula decimal
                            linha_processada.append(float(valor.replace(',', '.')))
                        else:
                            linha_processada.append(valor)
                    dados.append(linha_processada)
                else:
                    print(f"Linha {linha_num} ignorada: número de colunas incorreto")
        
        # Criar DataFrame manualmente
        df = pd.DataFrame(dados, columns=cabecalho)
        
        return df
    
    def _converter_para_float(self, valor):
        """
        Converte valor para float, tratando vírgula como separador decimal
        """
        if valor is None or pd.isna(valor):
            return float('nan')
        
        try:
            if isinstance(valor, str):
                return float(valor.replace(',', '.'))
            else:
                return float(valor)
        except (ValueError, TypeError):
            return float('nan')
    
    def simular_transmissao_intervalo(self, intervalo):
        """
        Simula a transmissão por intervalo - mantém apenas a cada 'n' IDs
        """
        df_simulado = self.df.copy()
        
        # Garantir que a coluna id existe e é numérica
        if 'id' not in df_simulado.columns:
            df_simulado['id'] = range(1, len(df_simulado) + 1)
        
        # Converter ID para numérico
        df_simulado['id'] = pd.to_numeric(df_simulado['id'], errors='coerce')
        
        # CORREÇÃO: Usar índice baseado em posição ao invés de valor do ID
        indices = np.arange(len(df_simulado))
        mask_transmitidos = (indices % intervalo) == 0
        
        # Para colunas numéricas, definir como NaN os não transmitidos
        colunas_numericas = ['temperatura', 'ph', 'ec', 'od']
        for coluna in colunas_numericas:
            if coluna in df_simulado.columns:
                # Manter apenas os valores dos pontos transmitidos
                valores_originais = df_simulado[coluna].copy()
                df_simulado[coluna] = np.where(mask_transmitidos, valores_originais, np.nan)
        
        pontos_transmitidos = mask_transmitidos.sum()
        total_pontos = len(df_simulado)
        percentual = (pontos_transmitidos / total_pontos) * 100
        
        print(f"Intervalo {intervalo}: {pontos_transmitidos}/{total_pontos} pontos transmitidos ({percentual:.1f}%)")
        
        return df_simulado
    
    def interpolar_parametro(self, ids, valores, parametro, intervalo=1):
        # Interpola valores baseado no tipo de parâmetro
        # Garantir que todos os valores são floats
        ids_float = [self._converter_para_float(id_val) for id_val in ids]
        valores_float = [self._converter_para_float(val) for val in valores]
        
        if parametro == 'temperatura':
            return self.interpolar_temperatura(ids_float, valores_float, intervalo)
        elif parametro == 'ph':
            return self.interpolar_ph(ids_float, valores_float)
        elif parametro == 'ec':
            return self.interpolar_ec(ids_float, valores_float)
        elif parametro == 'od':
            return self.interpolar_od(ids_float, valores_float)
        else:
            return valores_float
    
    def interpolar_temperatura(self, ids, temperaturas, intervalo=1):
        # Interpolação para temperatura
        return self.interpolator.linear_interpolation(ids, temperaturas)
    
    def interpolar_ph(self, ids, valores_ph):
        # Interpolação conservadora para pH
        return self.interpolator.conservative_interpolation(ids, valores_ph, max_gap=2)
    
    def interpolar_ec(self, ids, valores_ec):
        # Interpolação para condutividade elétrica"
        return self.interpolator.linear_interpolation(ids, valores_ec)
    
    def interpolar_od(self, ids, valores_od):
        # Interpolação para oxigênio dissolvido
        return self.interpolator.linear_interpolation(ids, valores_od)
    
    def calcular_metricas(self, original, interpolado):
        # Calcula métricas de qualidade R² e RMSE
        # Usar scikit-learn se disponível, senão usar implementação própria
        if SKLEARN_AVAILABLE:
            try:
                # Garantir que são arrays numpy e converter para float
                orig_clean = []
                interp_clean = []
                
                for i in range(min(len(original), len(interpolado))):
                    val_orig = self._converter_para_float(original[i])
                    val_interp = self._converter_para_float(interpolado[i])
                    
                    if not math.isnan(val_orig) and not math.isnan(val_interp):
                        orig_clean.append(val_orig)
                        interp_clean.append(val_interp)
                
                if len(orig_clean) < 2:
                    return float('nan'), float('nan')
                
                r2 = r2_score(orig_clean, interp_clean)
                rmse = np.sqrt(mean_squared_error(orig_clean, interp_clean))
                
                return r2, rmse
            except Exception as e:
                print(f"Erro no scikit-learn: {e}")
        
        # Implementação própria
        return self.metric_calculator.r2_score(original, interpolado), self.metric_calculator.rmse(original, interpolado)
    
    def executar_simulacao(self, intervalos=None):
        # Executa simulações para diferentes intervalos
        if intervalos is None:
            intervalos = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        print("\nINICIANDO SIMULAÇÕES DE INTERVALO")
        print("=" * 60)
        
        resultados_completos = []
        
        for intervalo in intervalos:
            print(f"\nAnalisando intervalo {intervalo}...")
            
            try:
                # Simular transmissão com intervalo
                df_simulado = self.simular_transmissao_intervalo(intervalo)
                
                # Aplicar interpolações
                ids = df_simulado['id'].values
                
                # Interpolar cada parâmetro
                interpolacoes = {}
                for parametro in ['temperatura', 'ph', 'ec', 'od']:
                    if parametro in df_simulado.columns:
                        valores_originais = df_simulado[parametro].values
                        interpolacoes[parametro] = self.interpolar_parametro(
                            ids, valores_originais, parametro, intervalo
                        )
                
                # Calcular métricas para cada parâmetro
                metricas = {}
                
                for parametro in ['temperatura', 'ph', 'ec', 'od']:
                    if parametro in self.df.columns and parametro in interpolacoes:
                        original = self.df[parametro].values
                        interpolado = interpolacoes[parametro]
                        
                        r2, rmse = self.calcular_metricas(original, interpolado)
                        metricas[parametro] = {'R2': r2, 'RMSE': rmse}
                        
                        status_r2 = f"{r2:.4f}" if not math.isnan(r2) else "NaN"
                        status_rmse = f"{rmse:.4f}" if not math.isnan(rmse) else "NaN"
                        print(f"   {parametro.upper():<6}\tR² = {status_r2}\tRMSE = {status_rmse}")
                    else:
                        print(f"   {parametro.upper():<6}\tColuna não encontrada no dataset")
                
                # Armazenar resultados
                resultado_intervalo = {
                    'intervalo': intervalo,
                    'pontos_transmitidos': (~pd.isna(df_simulado['temp'])).sum() if 'temp' in df_simulado.columns else 0,
                    'percentual_transmitido': 0
                }
                
                # Calcular percentual
                if 'temp' in df_simulado.columns:
                    total = len(df_simulado)
                    transmitidos = (~pd.isna(df_simulado['temp'])).sum()
                    resultado_intervalo['percentual_transmitido'] = (transmitidos / total) * 100
                
                for parametro in ['temperatura', 'ph', 'ec', 'od']:
                    if parametro in metricas:
                        resultado_intervalo[f'{parametro}_r2'] = metricas[parametro]['R2']
                        resultado_intervalo[f'{parametro}_rmse'] = metricas[parametro]['RMSE']
                    else:
                        resultado_intervalo[f'{parametro}_r2'] = float('nan')
                        resultado_intervalo[f'{parametro}_rmse'] = float('nan')
                
                resultados_completos.append(resultado_intervalo)
                
                # Salvar dados interpolados para análise posterior
                self.resultados[intervalo] = {
                    'df_simulado': df_simulado,
                    'interpolado': interpolacoes
                }
                
            except Exception as e:
                print(f"Erro no intervalo {intervalo}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if resultados_completos:
            self.df_resultados = pd.DataFrame(resultados_completos)
            return self.df_resultados
        else:
            print("Nenhuma simulação foi bem-sucedida")
            return pd.DataFrame()
    
    def _calcular_eficiencia(self, r2, percentual_transmitido):
        """Calcula score de eficiência balanceando qualidade e economia"""
        if math.isnan(r2) or r2 < 0:
            return 0
        # Score = R² * log(1/percentual) - penaliza baixos R² e recompensa alta economia
        return r2 * math.log(1/(percentual_transmitido/100 + 0.01))
    
    def _encontrar_melhores_intervalos_eficiencia(self):
        """Encontra os melhores intervalos baseado em eficiência R² vs economia"""
        melhores = {}
        
        for parametro in ['temperatura', 'ph', 'ec', 'od']:
            r2_col = f'{parametro}_r2'
            if r2_col not in self.df_resultados.columns:
                continue
                
            # Filtrar apenas intervalos > 1
            df_filtrado = self.df_resultados[self.df_resultados['intervalo'] > 1].copy()
            
            if df_filtrado.empty:
                continue
            
            # Calcular score de eficiência para cada intervalo
            df_filtrado['eficiencia'] = df_filtrado.apply(
                lambda row: self._calcular_eficiencia(row[r2_col], row['percentual_transmitido']), 
                axis=1
            )
            
            # Encontrar intervalo com melhor eficiência
            idx_melhor = df_filtrado['eficiencia'].idxmax()
            melhor = df_filtrado.loc[idx_melhor]
            
            # Também encontrar intervalo com R² > 0.9 mais econômico
            df_alta_qualidade = df_filtrado[df_filtrado[r2_col] >= 0.9]
            if not df_alta_qualidade.empty:
                idx_economico = df_alta_qualidade['percentual_transmitido'].idxmin()
                economico = df_alta_qualidade.loc[idx_economico]
            else:
                economico = None
            
            melhores[parametro] = {
                'melhor_eficiencia': {
                    'intervalo': melhor['intervalo'],
                    'r2': melhor[r2_col],
                    'rmse': melhor[f'{parametro}_rmse'],
                    'transmitido': melhor['percentual_transmitido'],
                    'eficiencia': melhor['eficiencia']
                },
                'mais_economico_alta_qualidade': {
                    'intervalo': economico['intervalo'] if economico is not None else None,
                    'r2': economico[r2_col] if economico is not None else None,
                    'rmse': economico[f'{parametro}_rmse'] if economico is not None else None,
                    'transmitido': economico['percentual_transmitido'] if economico is not None else None
                } if economico is not None else None
            }
        
        return melhores
    
    def gerar_relatorio(self):
        """
        Gera relatório completo com estatísticas
        """
        if not hasattr(self, 'df_resultados') or self.df_resultados.empty:
            print("Nenhum resultado disponível. Execute primeiro executar_simulacao()")
            return
        
        print("\nRELATÓRIO COMPLETO DE SIMULAÇÃO")
        print("=" * 80)
        
        # Tabela de resultados com separação por TAB
        print("\nRESUMO DE MÉTRICAS POR INTERVALO:")
        
        # Cabeçalho da tabela
        headers = ["Intervalo", "Transmitidos", "TEMP_R2", "TEMP_RMSE", "PH_R2", "PH_RMSE", "EC_R2", "EC_RMSE", "OD_R2", "OD_RMSE"]
        print("\t".join(headers))
        
        # Dados da tabela
        for _, row in self.df_resultados.iterrows():
            linha = [
                str(int(row['intervalo'])),
                f"{row['pontos_transmitidos']} ({row['percentual_transmitido']:.1f}%)"
            ]
            
            for parametro in ['temperatura', 'ph', 'ec', 'od']:
                r2 = row[f'{parametro}_r2']
                rmse = row[f'{parametro}_rmse']
                
                linha.append(f"{r2:.4f}" if not math.isnan(r2) else "NaN")
                linha.append(f"{rmse:.4f}" if not math.isnan(rmse) else "NaN")
            
            print("\t".join(linha))
        
        # Análise de ganhos aprimorada
        print("\nANÁLISE DE EFICIÊNCIA (Intervalos > 1):")
        print("=" * 60)
        
        melhores_intervalos = self._encontrar_melhores_intervalos_eficiencia()
        
        for parametro in ['temperatura', 'ph', 'ec', 'od']:
            if parametro in melhores_intervalos:
                dados = melhores_intervalos[parametro]
                melhor_ef = dados['melhor_eficiencia']
                economico = dados['mais_economico_alta_qualidade']
                
                print(f"\n{parametro.upper():<6}:")
                print(f"  Melhor eficiência global:")
                print(f"     • Intervalo: {melhor_ef['intervalo']}")
                print(f"     • R²: {melhor_ef['r2']:.4f}")
                print(f"     • RMSE: {melhor_ef['rmse']:.4f}")
                print(f"     • Transmitido: {melhor_ef['transmitido']:.1f}%")
                print(f"     • Score eficiência: {melhor_ef['eficiencia']:.4f}")
                
                if economico:
                    print(f"  Mais econômico com R² ≥ 0.9:")
                    print(f"     • Intervalo: {economico['intervalo']}")
                    print(f"     • R²: {economico['r2']:.4f}")
                    print(f"     • RMSE: {economico['rmse']:.4f}")
                    print(f"     • Transmitido: {economico['transmitido']:.1f}%")
                else:
                    print(f"  Nenhum intervalo >1 atingiu R² ≥ 0.9")
        
        # Análise comparativa adicional
        print("\nCOMPARAÇÃO ENTRE INTERVALOS POPULARES:")
        print("=" * 50)
        
        intervalos_analise = [2, 3, 5, 10]
        for intervalo in intervalos_analise:
            if intervalo in self.df_resultados['intervalo'].values:
                linha = self.df_resultados[self.df_resultados['intervalo'] == intervalo].iloc[0]
                print(f"\n🔸 Intervalo {intervalo} ({linha['percentual_transmitido']:.1f}% transmitido):")
                for parametro in ['temperatura', 'ph', 'ec', 'od']:
                    r2 = linha[f'{parametro}_r2']
                    if not math.isnan(r2):
                        qualidade = "Excelente" if r2 >= 0.95 else "Boa" if r2 >= 0.9 else "Regular" if r2 >= 0.8 else "Ruim"
                        print(f"   {parametro.upper():<6}: R² = {r2:.4f} ({qualidade})")
    
    def gerar_graficos_estatisticos(self):
        """
        Gera gráficos individuais para análise estatística dos dados
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Matplotlib não disponível - gráficos não serão gerados")
            return
        
        print("\nGERANDO GRÁFICOS ESTATÍSTICOS...")
        
        try:
            # Gráfico 1: Evolução temporal dos parâmetros originais
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('EVOLUÇÃO TEMPORAL DOS PARÂMETROS - DADOS ORIGINAIS', fontsize=16, fontweight='bold')
            
            parametros = ['temperatura', 'ph', 'ec', 'od']
            titulos = ['Temperatura', 'pH', 'Condutividade Elétrica', 'Oxigênio Dissolvido']
            unidades = ['°C', 'pH', 'mS/cm', 'mg/L']

            for idx, (parametro, titulo, unidade) in enumerate(zip(parametros, titulos, unidades)):
                if parametro in self.df.columns:
                    ax = axes[idx//2, idx%2]
                    valores = self.df[parametro].dropna()
                    
                    if not valores.empty:
                        ax.plot(range(len(valores)), valores, 'b-', linewidth=1, alpha=0.7)
                        ax.set_title(f'{titulo}', fontweight='bold')
                        ax.set_ylabel(unidade)
                        ax.set_xlabel('Amostras')
                        ax.grid(True, alpha=0.3)
                        
                        # Adicionar estatísticas no gráfico
                        media = valores.mean()
                        std = valores.std()
                        ax.axhline(y=media, color='r', linestyle='--', alpha=0.8, label=f'Média: {media:.2f}')
                        ax.axhline(y=media + std, color='orange', linestyle=':', alpha=0.6, label=f'+1σ: {media+std:.2f}')
                        ax.axhline(y=media - std, color='orange', linestyle=':', alpha=0.6, label=f'-1σ: {media-std:.2f}')
                        ax.legend(fontsize=8)
            
            plt.tight_layout()
            plt.savefig('evolucao_temporal_parametros.png', dpi=300, bbox_inches='tight')
            print("Gráfico 1 salvo: 'evolucao_temporal_parametros.png'")
            
            # Gráfico 2: Distribuição dos parâmetros
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('DISTRIBUIÇÃO DOS PARÂMETROS - HISTOGRAMAS', fontsize=16, fontweight='bold')
            
            for idx, (parametro, titulo, unidade) in enumerate(zip(parametros, titulos, unidades)):
                if parametro in self.df.columns:
                    ax = axes[idx//2, idx%2]
                    valores = self.df[parametro].dropna()
                    
                    if not valores.empty:
                        n, bins, patches = ax.hist(valores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                        ax.set_title(f'{titulo}', fontweight='bold')
                        ax.set_ylabel('Frequência')
                        ax.set_xlabel(unidade)
                        ax.grid(True, alpha=0.3)
                        
                        # Adicionar linhas de estatísticas
                        media = valores.mean()
                        mediana = valores.median()
                        ax.axvline(media, color='red', linestyle='--', linewidth=2, label=f'Média: {media:.2f}')
                        ax.axvline(mediana, color='green', linestyle='--', linewidth=2, label=f'Mediana: {mediana:.2f}')
                        ax.legend()
            
            plt.tight_layout()
            plt.savefig('distribuicao_parametros.png', dpi=300, bbox_inches='tight')
            print("Gráfico 2 salvo: 'distribuicao_parametros.png'")
            
            # Gráfico 3: Métricas R² por intervalo
            if hasattr(self, 'df_resultados') and not self.df_resultados.empty:
                fig, ax = plt.subplots(figsize=(12, 8))
                
                for parametro, cor, marcador in zip(['temperatura', 'ph', 'ec', 'od'], 
                                                  ['red', 'blue', 'green', 'purple'],
                                                  ['o', 's', '^', 'D']):
                    r2_col = f'{parametro}_r2'
                    if r2_col in self.df_resultados.columns:
                        r2_values = self.df_resultados[r2_col]
                        intervalos = self.df_resultados['intervalo']
                        
                        # Filtrar valores válidos
                        valid_mask = ~r2_values.isna()
                        if valid_mask.any():
                            ax.plot(intervalos[valid_mask], r2_values[valid_mask], 
                                   marker=marcador, color=cor, linewidth=2, 
                                   markersize=8, label=parametro.upper())
                
                ax.set_title('QUALIDADE DA INTERPOLAÇÃO - R² POR INTERVALO', fontsize=14, fontweight='bold')
                ax.set_xlabel('Intervalo de Transmissão')
                ax.set_ylabel('Coeficiente de Determinação (R²)')
                ax.grid(True, alpha=0.3)
                ax.legend()
                ax.set_ylim(0, 1)
                
                # Adicionar linha de referência para alta qualidade
                ax.axhline(y=0.9, color='orange', linestyle='--', alpha=0.7, label='R² = 0.9 (Alta qualidade)')
                ax.axhline(y=0.8, color='yellow', linestyle='--', alpha=0.7, label='R² = 0.8 (Qualidade aceitável)')
                
                plt.savefig('r2_por_intervalo.png', dpi=300, bbox_inches='tight')
                print("Gráfico 3 salvo: 'r2_por_intervalo.png'")
            
            # Gráfico 4: RMSE por intervalo
            if hasattr(self, 'df_resultados') and not self.df_resultados.empty:
                fig, ax = plt.subplots(figsize=(12, 8))
                
                for parametro, cor, marcador in zip(['temperatura', 'ph', 'ec', 'od'], 
                                                  ['red', 'blue', 'green', 'purple'],
                                                  ['o', 's', '^', 'D']):
                    rmse_col = f'{parametro}_rmse'
                    if rmse_col in self.df_resultados.columns:
                        rmse_values = self.df_resultados[rmse_col]
                        intervalos = self.df_resultados['intervalo']
                        
                        # Filtrar valores válidos
                        valid_mask = ~rmse_values.isna()
                        if valid_mask.any():
                            ax.plot(intervalos[valid_mask], rmse_values[valid_mask], 
                                   marker=marcador, color=cor, linewidth=2, 
                                   markersize=8, label=parametro.upper())
                
                ax.set_title('ERRO DA INTERPOLAÇÃO - RMSE POR INTERVALO', fontsize=14, fontweight='bold')
                ax.set_xlabel('Intervalo de Transmissão')
                ax.set_ylabel('Raiz do Erro Quadrático Médio (RMSE)')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                plt.savefig('rmse_por_intervalo.png', dpi=300, bbox_inches='tight')
                print("Gráfico 4 salvo: 'rmse_por_intervalo.png'")
            
            # Gráfico 5: Boxplot dos parâmetros originais (CORREÇÃO DO WARNING)
            fig, ax = plt.subplots(figsize=(10, 6))
            
            dados_boxplot = []
            labels_boxplot = []
            
            for parametro, titulo in zip(parametros, titulos):
                if parametro in self.df.columns:
                    valores = self.df[parametro].dropna()
                    if not valores.empty:
                        dados_boxplot.append(valores)
                        labels_boxplot.append(titulo)
            
            if dados_boxplot:
                # CORREÇÃO: usar 'tick_labels' em vez de 'labels' para versões recentes do Matplotlib
                ax.boxplot(dados_boxplot, tick_labels=labels_boxplot, patch_artist=True)
                ax.set_title('DISTRIBUIÇÃO - BOXPLOT DOS PARÂMETROS', fontsize=14, fontweight='bold')
                ax.set_ylabel('Valores')
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                
                plt.savefig('boxplot_parametros.png', dpi=300, bbox_inches='tight')
                print("✅ Gráfico 5 salvo: 'boxplot_parametros.png'")
            
            # Gráfico 6: Eficiência por intervalo (novo)
            if hasattr(self, 'df_resultados') and not self.df_resultados.empty:
                fig, axes = plt.subplots(2, 2, figsize=(15, 10))
                fig.suptitle('EFICIÊNCIA: QUALIDADE vs ECONOMIA POR INTERVALO', fontsize=16, fontweight='bold')
                
                for idx, parametro in enumerate(['temperatura', 'ph', 'ec', 'od']):
                    ax = axes[idx//2, idx%2]
                    r2_col = f'{parametro}_r2'
                    
                    if r2_col in self.df_resultados.columns:
                        # Calcular eficiência para este parâmetro
                        eficiencias = []
                        for _, row in self.df_resultados.iterrows():
                            if row['intervalo'] > 1:  # Apenas intervalos > 1
                                eff = self._calcular_eficiencia(row[r2_col], row['percentual_transmitido'])
                                eficiencias.append((row['intervalo'], eff))
                        
                        if eficiencias:
                            intervalos_eff, scores_eff = zip(*eficiencias)
                            bars = ax.bar(intervalos_eff, scores_eff, color='lightgreen', alpha=0.7, edgecolor='green')
                            ax.set_title(f'{parametro.upper()} - Score de Eficiência', fontweight='bold')
                            ax.set_xlabel('Intervalo')
                            ax.set_ylabel('Score de Eficiência')
                            ax.grid(True, alpha=0.3)
                            
                            # Destacar a melhor barra
                            melhor_idx = np.argmax(scores_eff)
                            bars[melhor_idx].set_color('gold')
                            bars[melhor_idx].set_edgecolor('orange')
                            bars[melhor_idx].set_linewidth(2)
                
                plt.tight_layout()
                plt.savefig('eficiencia_por_intervalo.png', dpi=300, bbox_inches='tight')
                print("Gráfico 6 salvo: 'eficiencia_por_intervalo.png'")
            
            print("Todos os gráficos gerados com sucesso!")
            
        except Exception as e:
            print(f"Erro ao gerar gráficos: {e}")
            import traceback
            traceback.print_exc()
    
    def salvar_resultados(self, arquivo='./data/resultados_simulacao.csv'):
        """Salva resultados em arquivo CSV"""
        if hasattr(self, 'df_resultados') and not self.df_resultados.empty:
            self.df_resultados.to_csv(arquivo, index=False)
            print(f"Resultados salvos em '{arquivo}'")
        else:
            print("Nenhum resultado para salvar")

def main():
    """
    Função principal
    """
    print("ANALISADOR DE INTERPOLAÇÃO")
    print("=" * 50)
    
    # Verificar se o arquivo existe
    arquivo_dataset = './data/dataset_cfe-hydro.csv'
    if not os.path.exists(arquivo_dataset):
        print(f"Arquivo '{arquivo_dataset}' não encontrado.")
        print("Criando dataset de exemplo...")
        criar_dataset_exemplo(arquivo_dataset)
    
    # Inicializar analisador
    analisador = AnalisadorInterpolacaoCorrigido(arquivo_dataset)
    
    # Executar simulações
    intervalos_testar = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    resultados = analisador.executar_simulacao(intervalos_testar)
    
    # Gerar relatório
    analisador.gerar_relatorio()
    
    # Gerar gráficos estatísticos
    analisador.gerar_graficos_estatisticos()
    
    # Salvar resultados
    analisador.salvar_resultados()
    
    return analisador

def criar_dataset_exemplo(arquivo):
    """Cria um dataset de exemplo se não existir"""
    print("Criando dataset de exemplo com vírgula decimal...")
    
    # Criar dados de exemplo
    np.random.seed(42)
    n_points = 100
    
    dados = {
        'id': range(1, n_points + 1),
        'timestamp': pd.date_range('2024-01-01', periods=n_points, freq='H').strftime('%d/%m/%Y %H:%M:%S'),
        'temp': [f"{15 + 8 * math.sin(i * 4 * math.pi / n_points) + np.random.normal(0, 0.3):.2f}".replace('.', ',') for i in range(n_points)],
        'ph': [f"{7.0 + 0.3 * math.sin(i * 2 * math.pi / n_points) + np.random.normal(0, 0.05):.2f}".replace('.', ',') for i in range(n_points)],
        'ec': [f"{0.5 + 0.2 * math.sin(i * 3 * math.pi / n_points) + np.random.normal(0, 0.02):.2f}".replace('.', ',') for i in range(n_points)],
        'od': [f"{8.0 + 1.5 * math.sin(i * 6 * math.pi / n_points) + np.random.normal(0, 0.1):.2f}".replace('.', ',') for i in range(n_points)]
    }
    
    df = pd.DataFrame(dados)
    df.to_csv(arquivo, sep=';', index=False)
    print(f"Dataset de exemplo criado: '{arquivo}' com {n_points} registros")

if __name__ == "__main__":
    analisador = main()

